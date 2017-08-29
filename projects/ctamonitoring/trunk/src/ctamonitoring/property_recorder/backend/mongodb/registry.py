# coding=utf-8
__version__ = "$Id$"


"""
The mongodb registry and buffer

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: bson
@requires: copy
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: ctamonitoring.property_recorder.backend.exceptions
@requires: ctamonitoring.property_recorder.backend.ring_buffer
@requires: ctamonitoring.property_recorder.backend.util
@requires: datetime
@requires: pymongo
@requires: threading
@requires: time
@requires: Acspy.Common.Log or logging
@requires: mongo_proxy
"""


import bson
import copy
import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.exceptions \
    import InterruptedException
from ctamonitoring.property_recorder.backend.ring_buffer import RingBuffer
from ctamonitoring.property_recorder.backend.util import to_datetime
from ctamonitoring.property_recorder.backend.util import get_floor
from ctamonitoring.property_recorder.backend.util import get_total_seconds
from ctamonitoring.property_recorder.backend.mongodb \
    import __name__ as defaultname
from datetime import datetime
from datetime import timedelta
import pymongo
from pymongo import MongoClient
from pymongo.errors import AutoReconnect
from threading import Event
from threading import Thread
from threading import ThreadError
import time

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger

try:
    from mongo_proxy import MongoProxy
    MONGO_PROXY_WAIT_TIME = 20
    MONGO_PROXY_DISCONNECT_ON_TIMEOUT = True
except ImportError:
    MongoProxy = None


class MongoSimpleLock(object):
    """
    A simple, distributed lock on the basis of MongoDB.

    MongoSimpleLock creates a document that identifies the resource
    to protect and its 'user' in a 'lock collection' while it is
    locked. This document is deleted when it is released.
    However, a 'user' may 'miss' to release it (like during a crash).
    This is why MongoSimpleLock will 'self release' after a given duration
    (cf. create_index).
    """

    def __init__(self, col, id, uid, expire_after=timedelta(seconds=180)):
        """
        ctor.

        @param col: The 'lock collection'.
        @type: pymongo.database.Collection
        @param id: Identifies the resource to protect by the lock.
        This ID must be unique.
        @type: pymongo.ObjectId
        @param uid: Identifies the 'user' who acquires the lock.
        Only this 'user' can release the lock before 'self release'.
        This ID must be unique.
        @type: pymongo.ObjectId
        @param expire_after: The lock will expire (self release) after
        this duration.
        Optional, default is 3 minutes.
        @type expire_after: datetime.timedelta
        """
        self._col = col
        self._doc = {"_id": id,
                     "uid": uid}
        self._expire_after = expire_after

    def acquire(self, blocking=True):
        """
        Acquire the lock, blocking or non-blocking.

        @param blocking: When invoked with the blocking argument set to True
        (the default), block until the lock is unlocked, then set it to locked.
        @type blocking: boolean
        @return: True if the lock was locked.
        @rtype: boolean
        """
        retval = False
        doc = copy.deepcopy(self._doc)
        i = 0
        while not retval:
            try:
                doc["expire_at"] = datetime.utcnow() + self._expire_after
                self._col.insert_one(doc)
                retval = True
            except pymongo.errors.DuplicateKeyError:
                if not blocking:
                    break
                time.sleep(min(5, pow(2, i)))
                i += 1
        return retval

    def release(self):
        """
        Release the lock.

        @raise threading.ThreadError: When invoked on an unlocked lock.
        """
        result = self._col.delete_one(self._doc)
        if result.acknowledged and not result.deleted_count:
            raise ThreadError()

    @staticmethod
    def create_index(col):
        """
        Create an index on the 'lock collection' that supports TTL.

        MongoSimpleLocks are intended to expire (self release) after a
        given duration. This is achieved by an index for 'expire_at'
        and an 'expireAfterSeconds' time equal 0.
        If this index is not created MongoSimpleLock will not support
        'self release'.
        @param col: The 'lock collection'.
        @type col: pymongo.database.Collection
        """
        col.create_index("expire_at", expireAfterSeconds=0)


class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
    """
    This buffer stores monitoring/time series data indirectly in mongodb.

    The buffer and mongodb are decoupled by a FIFO plus (a) consumer thread(s)
    that are common for the registry and all properties that it manages.
    """

    def __init__(self, log, fifo, chunk_size,
                 property_id, log_id, log_col,
                 component_name, property_name,
                 disable):
        """
        ctor.

        @param log: The logger to publish log messages.
        @type log: logging.Logger
        @param fifo: The FIFO that is the input for the mongodb consumer.
        @type fifo: ctamonitoring.property_recorder.backend.ring_buffer.RingBuffer
        @param chunk_size: Specifies the time duration within monitoring data
        is safed into a chunk (fraction of seconds will be ignored).
        @type chunk_size: datetime.timedelta
        @param property_id: This is the ID that identifies the
        property/monitoring in the properties collection
        (cf. mongodb Registry).
        @type property_id: bson.ObjectId
        @param log_id: This is the ID that identifies the current data taking
        period for property property_id in the log collection
        (cf. mongodb Registry).
        @type log_id: bson.ObjectId
        @param log_col: This is the log collection to add an end date to
        the current data taking period while closing this buffer.
        @type log_col: pymongo.database.Collection
        @param component_name: Component name and
        @type component_name: string
        @param property_name: property name this buffer will receive data from.
        @type property_name: string
        @param disable: Create a buffer for a property that was detected
        but isn't actually monitored. This will only allow for calling
        Buffer.close().
        @type disable: boolean
        """
        log.debug("creating buffer %s/%s" % (component_name, property_name))
        super(Buffer, self).__init__()
        self._log = log
        self._fifo = fifo
        self._chunk_size = chunk_size
        self._property_id = property_id
        self._log_id = log_id
        self._log_col = log_col
        self._component_name = component_name
        self._property_name = property_name
        self._disable = disable
        self._bin_begin = None
        self._doc = None
        self._canceled = False  # keep this the last line in ctor

    def add(self, tm, dt):
        """
        Write data to the db.

        @raise RuntimeError: If buffer is closed.
        @warning: Creates log warnings if called although property/buffer
        is disabled.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        """
        if self._canceled:
            raise RuntimeError("unregistered property %s/%s - buffer is closed." %
                               (self._component_name, self._property_name))
        if not self._disable:
            t = to_datetime(tm)
            bin_begin = get_floor(t, self._chunk_size, True)
            if self._bin_begin is not None and bin_begin != self._bin_begin:
                if self._doc and self._doc["end"] is not None:
                    self._fifo.add(self._doc)
                self._bin_begin = None
                self._doc = None
            if self._bin_begin is None:
                self._bin_begin = bin_begin
                self._doc = {"begin": t, "end": None,
                             "values": [],
                             "bin": bin_begin, "pid": self._property_id}
            self._doc["values"].append({"t": t, "val": dt})
            self._doc["end"] = t
        else:
            self._log.warn("property monitoring for %s/%s is disabled" %
                           (self._component_name, self._property_name))

    def flush(self):
        """
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.flush()
        """
        if not self._disable and not self._canceled:
            if self._doc and self._doc["end"] is not None:
                self._fifo.add(self._doc)
            self._bin_begin = None
            self._doc = None
            self._fifo.flush(current=True)

    def close(self):
        """
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry. However,
        this error only indicates a potential loss of data during flush.
        The end date/time of the monitoring in the log collection
        is most likely updated appropriately
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        """
        if not self._canceled:
            self._log.info("closing buffer %s/%s" %
                           (self._component_name, self._property_name))
            try:
                self.flush()
            finally:
                self._log_col.update_one({"_id": self._log_id},
                                         {"$set": {"end": datetime.now()}})
                self._canceled = True

    def __del__(self):
        """dtor."""
        # The dtor is called even if the ctor didn't run through.
        # So, make sure the ctor did work by using self._canceled
        # and catching a potential AttributeError (well, catch all).
        try:
            if not self._canceled:
                try:
                    self.close()
                except InterruptedException:
                    self._log.warn("cannot close buffer %s/%s appropriately" %
                                   (self._component_name, self._property_name))
                except:
                    self._log.warn("cannot close buffer %s/%s" %
                                   (self._component_name, self._property_name))
        except:
            pass


class _Worker(Thread):
    def __init__(self, uri, chunks, chunk_size, fifo, log):
        log.debug("creating mongodb worker")
        super(_Worker, self).__init__()
        self._uri = uri
        self._chunks = chunks
        if chunk_size is None:
            self._timeout = None
        else:
            self._timeout = get_total_seconds(chunk_size, True) * 0.5
            # don't use timeouts less than 100ms
            if self._timeout < 0.1:
                self._timeout = 0.1
        self._fifo = fifo
        self._log = log
        self._n = 10
        self._canceled = Event()
        self._canceled.clear()

    def run(self):
        try:
            while not self._canceled.is_set():
                try:
                    chunks = self._fifo.get(n=self._n, timeout=self._timeout)
                except InterruptedException:
                    self._log.info("request to cancel mongodb worker")
                    continue
                except:
                    self._log.exception("oups, unexpected exception... " +
                                        "ignore and continue")
                    continue
                begin = 0
                while begin < len(chunks) and not self._canceled.is_set():
                    try:
                        result = self._chunks.insert_many(chunks[begin:],
                                                          ordered=True)
                    except AutoReconnect:
                        self._log.exception(("still %d chunks to insert " +
                                             "into mongodb (%s)... " +
                                             "keep trying") %
                                            (len(chunks) - begin, self._uri))
                    except:
                        self._log.exception(("still %d chunks to insert " +
                                             "into mongodb (%s)... " +
                                             "keep trying") %
                                            (len(chunks) - begin, self._uri))
                        self._log.warn("skipping document: " +
                                       str(chunks[begin]))
                        begin += 1
                    else:
                        begin += len(result.inserted_ids)
        except:
            self._log.exception("exiting mongodb worker")
        else:
            self._log.info("exiting mongodb worker")

    def cancel(self):
        self._canceled.set()


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the mongodb registry to register a property
    and to create a buffer that writes data to mongodb.
    """
    def __init__(self,
                 database,
                 logs="logs",
                 properties="properties",
                 chunks="chunks",
                 uri="mongodb://localhost",
                 chunk_size=timedelta(seconds=60),
                 fifo_size=1000,
                 n_workers=1,
                 worker_is_daemon=False,
                 log=None,
                 *args, **kwargs):
        """
        ctor.

        @param database: Database name.
        @type database: string
        @param logs: Collection name.
        This collection keeps information when a property was "monitored".
        Optional, default is "log".
        @type logs: string
        @param properties: Collection name.
        This collection keeps information about the property and its meta data.
        Optional, default is "properties".
        @type properties: string
        @param chunks: Collection name.
        This collection keeps the actual monitoring data.
        However, it will keep chunks of it instead of single values
        to be more efficient. Optional, default is "chunks".
        @type chunks: string
        @param uri: mongodb URI. Optional, default is "mongodb://localhost".
        @type uri: string
        @param chunk_size: Specifies the time duration within monitoring data
        is safed into a chunk (fraction of seconds will be ignored).
        Optional, default is 1 minute.
        The chunk size can be given as a timedelta or a 'number of seconds'.
        @type chunk_size: datetime.timedelta or int or float
        @param fifo_size: Sets the upperbound limit on the number of chunks
        that can be placed in the FIFO before overwriting older chunks.
        The FIFO decouples the producers of monitoring data (frontend,
        backend buffers) and the consumer thread(s) that insert(s) the data
        into mongodb. Optional, default is 1000.
        @type fifo_size: int
        @param n_workers: Number of consumer threads, so called workers.
        Optional, default is 1.
        @type n_workers: int
        @param worker_is_daemon: Workers traditionally run as daemon threads
        but this seems not to work within an ACS component. So this is your
        choice ;). We will try to stop all workers in the destructor in case
        they aren't daemons. Optional, default is False.
        @type worker_is_daemon: bool
        @param log: An external logger to write log messages to.
        Optional, default is None.
        @type log: logging.Logger
        """
        super(Registry, self).__init__(log, *args, **kwargs)
        if not self._log:
            self._log = getLogger(defaultname)
        self._log.debug("creating a mongodb registry")
        self._database_name = database
        self._logs_name = logs
        self._properties_name = properties
        self._chunks_name = chunks
        self._uri = uri
        if isinstance(chunk_size, timedelta):
            self._chunk_size = chunk_size
        else:
            self._chunk_size = timedelta(seconds=chunk_size)

        cl = MongoClient(uri)
        assert cl.write_concern.acknowledged
        # Starting with version 3.0 the MongoClient constructor no longer
        # blocks while connecting to the server or servers, and it no longer
        # raises ConnectionFailure if they are unavailable,
        # nor ConfigurationError if the user’s credentials are wrong.
        # Instead, the constructor returns immediately and launches
        # the connection process on background threads.
        # Check if the server is available...
        # The ismaster command is cheap and does not require auth.
        cl.admin.command('ismaster')
        if MongoProxy is not None:
            self._client = \
                MongoProxy(cl,
                           logger=self._log,
                           wait_time=MONGO_PROXY_WAIT_TIME,
                           disconnect_on_timeout=MONGO_PROXY_DISCONNECT_ON_TIMEOUT)
        else:
            self._client = cl

        self._database = self._client[database]
        self._logs = self._database[logs]
        self._logs_locks = self._logs["locks"]
        MongoSimpleLock.create_index(self._logs_locks)
        self._properties = self._database[properties]
        self._chunks = self._database[chunks]

        self._worker_is_daemon = worker_is_daemon
        if n_workers <= 0:
            n_workers = 1
        self._fifo = RingBuffer(fifo_size)
        self._workers = []  # keep this the last class member variable in ctor
        for _ in range(n_workers):
            worker = _Worker(uri, self._chunks,
                             self._chunk_size, self._fifo, self._log)
            worker.daemon = worker_is_daemon
            worker.start()
            self._workers.append(worker)

    def _check_name(self, name, description):
        if not isinstance(name, basestring):
            raise TypeError("check " + description)
        if not name:
            raise ValueError("check " + description)

    def _get_log_id(self, component_name, property_name,
                    property_id, disable, force):
        begin = datetime.now()
        id = bson.ObjectId()
        log_desc = {"_id": id,
                    "pid": property_id,
                    "begin": begin,
                    "end": None,
                    "disabled": disable}
        lock = MongoSimpleLock(self._logs_locks, property_id, id)
        lock.acquire()
        try:
            cursor = self._logs.find({"pid": property_id},
                                     sort=[("begin", pymongo.DESCENDING)],
                                     limit=1)
            for log_entry in cursor:
                if log_entry["begin"] >= begin:
                    raise RuntimeError("oups, beginning of the latest log " +
                                       "entry for %s/%s " % (component_name,
                                                             property_name) +
                                       "is in future!?!")
                if log_entry["end"] is None and not force:
                    raise UserWarning("undefined end of the latest log " +
                                      "entry for %s/%s" % (component_name,
                                                           property_name))
            self._logs.insert_one(log_desc)
        finally:
            lock.release()
        return id

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        @raise TypeError: if component name or property name is not a string.
        @raise ValueError: if component name or property name is empty.
        @raise RuntimeError: if the log entries for this property are not
        consistent.
        @raise UserWarning: if the property seems currently still monitored.
        One can force (=True) register to succeed.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        """
        self._log.info("registering %s/%s" % (component_name, property_name))
        # we actually don't care too much here what parameters are given
        # however, component name and property name are the main
        # characteristics to identify a property so we will check these
        self._check_name(component_name, "component_name")
        self._check_name(property_name, "property_name")
        property_desc = {"component_name": component_name,
                         "component_type": component_type,
                         "property_name": property_name,
                         "property_type": str(property_type),
                         "property_type_desc": property_type_desc,
                         "meta": meta,
                         "chunk_size": get_total_seconds(self._chunk_size,
                                                         True)}
        tmp = self._properties.find_one_and_replace(filter=property_desc,
                                                    replacement=property_desc,
                                                    upsert=True,
                                                    return_document=pymongo.ReturnDocument.AFTER)
        property_id = tmp["_id"]
        log_id = self._get_log_id(component_name, property_name,
                                  property_id, disable, force)
        return Buffer(self._log, self._fifo, self._chunk_size,
                      property_id, log_id, self._logs,
                      component_name, property_name,
                      disable)

    def __del__(self):
        """dtor."""
        # The dtor is called even if the ctor didn't run through.
        # So, make sure the ctor did work by using self._worker_is_daemon
        # and self._workers plus catching a potential AttributeError
        # (well, catch all).
        #
        # Workers traditionally run as daemon threads but this seems
        # not to work within an ACS component. Cancel all workers
        # in case they aren't daemons...
        # Workers may block calling RingBuffer.get() --> terminate the
        # ring buffer in addition!
        # Note: data that is in the ring buffer will be lost but
        # the frontend is supposed to flush it before it releases
        # the registry.
        try:
            if not self._worker_is_daemon:
                for worker in self._workers:
                    worker.cancel()
                self._fifo.terminate()
                for worker in self._workers:
                    worker.join()
        except:
            pass
