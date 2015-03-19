__version__ = "$Id: registry.py 945 2014-11-07 12:52:36Z igoroya $"


'''
The mongodb registry and buffer

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: registry.py 945 2014-11-07 12:52:36Z igoroya $
@change: $LastChangedDate: 2014-11-07 13:52:36 +0100 (Fri, 07 Nov 2014) $
@change: $LastChangedBy: igoroya $
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: ctamonitoring.property_recorder.backend.exceptions
@requires: ctamonitoring.property_recorder.backend.ring_buffer
@requires: ctamonitoring.property_recorder.backend.util
@requires: datetime
@requires: pymongo
@requires: mongodb_proxy
@requires: threading
@requires: Acspy.Common.Log or logging
'''


import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.exceptions import InterruptedException
from ctamonitoring.property_recorder.backend.ring_buffer import RingBuffer
from ctamonitoring.property_recorder.backend.util import to_datetime
from ctamonitoring.property_recorder.backend.util import get_floor
from ctamonitoring.property_recorder.backend.mongodb import __name__ as defaultname
from datetime import datetime
from datetime import timedelta
import pymongo
from pymongo import MongoClient
from pymongo.errors import AutoReconnect
from threading import Event
from threading import Thread

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger


class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
    '''
    This buffer stores monitoring/time series data indirectly in mongodb.
    
    The buffer and mongodb are decoupled by a FIFO plus (a) consumer thread(s)
    that are common for the registry and all properties that it manages.
    '''
    def __init__(self, log, fifo, chunk_size,
                 property_id, log_id, log_col,
                 component_name, property_name,
                 disable):
        '''
        ctor.
        
        @param log: The logger to publish log messages.
        @type log: logging.Logger
        @param fifo: The FIFO that is the input for the mongodb consumer.
        @type fifo: ctamonitoring.property_recorder.backend.ring_buffer.RingBuffer
        @param chunk_size: Specifies the time duration within monitoring data
        is safed into a chunk.
        @type chunk_size: datetime.timedelta
        @param property_id: This is the ID that identifies the
        property/monitoring in the properties collection (cf. mongodb Registry).
        @type property_id: bson.ObjectId
        @param log_id: This is the ID that identifies the current data taking
        period for property property_id in the log collection
        (cf. mongodb Registry).
        @type log_id: bson.ObjectId
        @param log_col: This is the log collection to add an end date to
        the current data taking period while closing this buffer.
        @type log_col: bson.ObjectId
        @param component_name: Component name and
        @type component_name: string
        @param property_name: property name this buffer will receive data from.
        @type property_name: string
        @param disable: Create a buffer for a property that was detected
        but isn't actually monitored. This will only allow for calling
        Buffer.close().
        @type disable: boolean
        '''
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
        self._canceled = False # keep this the last line in ctor
    
    def add(self, tm, dt):
        '''
        Write data to the db.
        
        @raise RuntimeError: If buffer is closed.
        @warning: Creates log warnings if called although property/buffer is disabled.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        '''
        if self._canceled:
            raise RuntimeError("unregistered property %s/%s - buffer is closed."
                               % (self._component_name, self._property_name))
        if not self._disable:
            t = to_datetime(tm)
            bin_begin = get_floor(t, self._chunk_size)
            if self._bin_begin is not None and bin_begin != self._bin_begin:
                if self._doc and self._doc["end"] is not None:
                    self._fifo.add(self._doc)
                self._bin_begin = None
                self._doc = None
            if self._bin_begin is None:
                self._bin_begin = bin_begin
                self._doc = {"begin" : t, "end" : None,
                             "values" : [],
                             "bin" : bin_begin, "pid" : self._property_id}
            self._doc["values"].append({"t" : t, "val" : dt})
            self._doc["end"] = t
        else:
            self._log.warn("property monitoring for %s/%s is disabled"
                           % (self._component_name, self._property_name))
    
    def flush(self):
        '''
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.flush()
        '''
        if not self._disable and not self._canceled:
            if self._doc and self._doc["end"] is not None:
                self._fifo.add(self._doc)
            self._bin_begin = None
            self._doc = None
            self._fifo.flush(current = True)
    
    def close(self):
        '''
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry. However, this error
        only indicates a potential loss of data during flush.
        The end date/time of the monitoring in the log collection is most likely
        updated appropriately 
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        '''
        if not self._canceled:
            self._log.info("closing buffer %s/%s"
                           % (self._component_name, self._property_name))
            try:
                self.flush()
            finally:
                self._log_col.update({"_id" : self._log_id},
                                     {"$set" : {"end" : datetime.now()}})
                self._canceled = True
    
    def __del__(self):
        '''
        dtor.
        '''
        # The dtor is called even if the ctor didn't run through.
        # So, make sure the ctor did work by using self._canceled
        # and catching a potential AttributeError (well, catch all).
        try:
            if not self._canceled:
                try:
                    self.close()
                except InterruptedException:
                    self._log.warn("cannot close buffer %s/%s appropriately"
                                   % (self._component_name, self._property_name))
                except:
                    self._log.warn("cannot close buffer %s/%s"
                                   % (self._component_name, self._property_name))
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
            self._timeout = (chunk_size.days * 86400. +
                             chunk_size.seconds +
                             chunk_size.microseconds * 1e-6) / 2
        if self._timeout < 0.1:  # don't use timeouts less than 100ms
            self._timeout = 0.1
        self._fifo = fifo
        self._log = log
        self._canceled = Event()
        self._canceled.clear()
    
    def run(self):
        try:
            while not self._canceled.is_set():
                try:
                    chunks = self._fifo.get(n = 10, timeout = self._timeout)
                except InterruptedException:
                    self._log.exception("request to cancel mongodb worker")
                    break
                except:
                    self._log.exception("oups, unexpected exception... " +
                                        "ignore and continue")
                    continue
                begin = 0
                while begin < len(chunks) and not self._canceled.is_set():
                    try:
                        ids = self._chunks.insert(chunks[begin:])
                    except AutoReconnect:
                        begin += len(ids)
                        self._log.exception(("still %d chunks to insert " +
                                             "into mongodb (%s)... keep trying") %
                                            (len(chunks) - begin, self._uri))
                    except:
                        begin += len(ids)
                        self._log.exception(("still %d chunks to insert " +
                                            "into mongodb (%s)... keep trying") %
                                            (len(chunks) - begin, self._uri))
                        self._log.warn("skipping document: " +
                                       str(chunks[begin]))
                        begin += 1
                    else:
                        break
        except:
            self._log.exception("exiting mongodb worker")
        else:
            self._log.info("exiting mongodb worker")
    
    def cancel(self):
        self._canceled.set()


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    '''
    This is the mongodb registry to register a property
    and to create a buffer that writes data to mongodb.
    '''
    def __init__(self,
                 database,
                 logs ="logs",
                 properties = "properties",
                 chunks = "chunks",
                 uri = "mongodb://localhost",
                 chunk_size = timedelta(seconds = 60),
                 fifo_size = 1000,
                 n_workers = 1,
                 worker_is_daemon = False,
                 log = None):
        '''
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
        is safed into a chunk. Optional, default is 1 minute.
        @type chunk_size: datetime.timedelta
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
        @raise ValueError: if n_workers is <= 0.
        '''
        super(Registry, self).__init__(log)
        if not self._log:
            self._log = getLogger(defaultname)
        self._log.debug("creating a mongodb registry")
        self._database_name = database
        self._logs_name = logs;
        self._properties_name = properties
        self._chunks_name = chunks
        self._uri = uri
        self._chunk_size = chunk_size
        
        self._uses_proxy = False
        try:
            from mongodb_proxy import MongoProxy
            self._client = MongoProxy(MongoClient(uri), self._log, 5)
            self._uses_proxy = True
        except ImportError:
            self._client = MongoClient(uri)
        self._database = self._client[database]
        self._logs = self._database[logs]
        self._properties = self._database[properties]
        self._chunks = self._database[chunks]
        
        self._worker_is_daemon = worker_is_daemon
        if n_workers <= 0:
            raise ValueError("check n_workers")
        self._fifo = RingBuffer(fifo_size)
        self._workers = [] # keep this the last class member variable in ctor
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
        log_desc = {"pid" : property_id,
                    "begin" : begin,
                    "end" : None,
                    "disabled" : disable}
        # ...
        count1 = self._logs.find({"pid" : property_id}).count()
        cursor = self._logs.find({"pid": property_id},
                                 sort = [("begin", pymongo.DESCENDING)],
                                 limit = 1)
        for log_entry in cursor:
            if log_entry["begin"] >= begin:
                raise RuntimeError("oups, beginning in the " +
                                   "latest log entry of " +
                                   "%s/%s " % (component_name, property_name) +
                                   "is in future!?!")
            if log_entry["end"] is None and not force:
                raise UserWarning("undefined end in the latest log entry of " +
                                  "%s/%s" % (component_name, property_name))
        log_id = self._logs.insert(log_desc)
        count2 = self._logs.find({"pid" : property_id}).count()
        if count2 - count1 != 1:
            self._logs.remove(log_id)
            raise RuntimeError("check if " +
                               "%s/%s " % (component_name, property_name) +
                               "is already monitored in parallel")
        return log_id
    
    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc = None,
                 disable = False, force = False, **meta):
        '''
        @raise TypeError: if component name or property name is not a string.
        @raise ValueError: if component name or property name is empty.
        @raise RuntimeError: if the log entries for this property are not
        consistent.
        @raise UserWarning: if the property seems currently still monitored.
        One can force (= True) register to succeed.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        '''
        self._log.info("registering %s/%s" % (component_name, property_name))
        # we actually don't care too much here what parameters are given
        # however, component name and property name are the main characteristics
        # to identify a property so we will check these
        self._check_name(component_name, "component_name")
        self._check_name(property_name, "property_name")
        property_desc = {"component_name" : component_name,
                         "component_type" : component_type,
                         "property_name" : property_name,
                         "property_type" : str(property_type),
                         "property_type_desc" : property_type_desc,
                         "meta" : meta,
                         "chunk_size" : (self._chunk_size.days * 86400. +
                                         self._chunk_size.seconds +
                                         self._chunk_size.microseconds * 1e-6)}
        tmp = self._properties.find_and_modify(query=property_desc,
                                               update=property_desc,
                                               upsert=True, new=True)
        property_id = tmp["_id"]
        log_id = self._get_log_id(component_name, property_name,
                                  property_id, disable, force)
        return Buffer(self._log, self._fifo, self._chunk_size,
                      property_id, log_id, self._logs,
                      component_name, property_name,
                      disable)
    
    def __del__(self):
        '''
        dtor.
        '''
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
