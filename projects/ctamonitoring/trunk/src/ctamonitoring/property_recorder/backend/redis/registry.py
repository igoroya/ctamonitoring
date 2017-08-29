# coding=utf-8
__version__ = "$Id$"


"""
The redis registry and buffer

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: ctamonitoring.property_recorder.backend.exceptions
@requires: ctamonitoring.property_recorder.backend.ring_buffer
@requires: ctamonitoring.property_recorder.backend.util
@requires: datetime
@requires: msgpack
@requires: redis
@requires: threading
@requires: Acspy.Common.Log or logging
"""


import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.exceptions \
    import InterruptedException
from ctamonitoring.property_recorder.backend.ring_buffer import RingBuffer
from ctamonitoring.property_recorder.backend.util import to_posixtime
from ctamonitoring.property_recorder.backend.util import get_total_seconds
from ctamonitoring.property_recorder.backend.redis \
    import __name__ as defaultname
from datetime import timedelta
import msgpack
import redis
from threading import Event
from threading import Lock
from threading import Thread

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger


_lock = Lock()
_to_expire = set()


class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
    """
    This buffer stores monitoring/time series data indirectly in redis.

    The buffer and redis are decoupled by a FIFO plus (a) consumer thread(s)
    that is/are managed by the registry.
    """

    def __init__(self, log, fifo, chunk_size,
                 component_name, property_name,
                 disable):
        """
        ctor.

        @param log: The logger to publish log messages.
        @type log: logging.Logger
        @param fifo: The FIFO that is the input for the redis consumer.
        @type fifo: ctamonitoring.property_recorder.backend.ring_buffer.RingBuffer
        @param component_name: Component name and
        @type component_name: string
        @param property_name: property name this buffer will receive data from.
        @type property_name: string
        @param disable: Create a buffer for a property that was detected
        but isn't actually monitored. This will only allow for calling
        Buffer.close().
        @type disable: bool
        """
        super(Buffer, self).__init__()
        self._log = log
        self._fifo = fifo
        log.debug("creating buffer %s/%s" % (component_name, property_name))
        self._chunk_size = get_total_seconds(chunk_size, True)
        self._component_name = component_name
        self._property_name = property_name
        self._disable = disable
        self._chunk_begin = None
        self._key = None
        self._canceled = False  # keep this the last line in ctor

    def add(self, tm, dt):
        """
        Write data to the db... well fifo.

        @raise RuntimeError: If buffer is closed.
        @warning: Creates log warnings if called although property/buffer
        is disabled.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        """
        if self._canceled:
            raise RuntimeError("unregistered property %s/%s - buffer is closed." %
                               (self._component_name, self._property_name))
        if not self._disable:
            t = to_posixtime(tm)
            chunk_begin = long((t // self._chunk_size) * self._chunk_size)
            new_key = (self._chunk_begin is None or
                       self._chunk_begin != chunk_begin)
            if new_key:
                key = ":".join((self._component_name,
                                self._property_name,
                                str(chunk_begin)))
            else:
                key = self._key
            self._fifo.add((new_key, key, t, dt))
            if new_key:
                self._chunk_begin = chunk_begin
                self._key = key
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
            self._fifo.flush(current=True)
            self._chunk_begin = None
            self._key = None

    def close(self):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        """
        if not self._canceled:
            self._log.info("closing buffer %s/%s" %
                           (self._component_name, self._property_name))
            self.flush()
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
    def __init__(self, uri, client, ttl, ttl_last_item, fifo, log):
        log.debug("creating redis worker")
        super(_Worker, self).__init__()
        self._uri = uri
        self._client = client
        self._ttl = ttl
        self._ttl_last_item = ttl_last_item
        # what is a good timeout here?
        # do we want the worker waiting for n_ values for longer time?
        # well, this would be ok, since it will get interrupted via the
        # fifo cancel... but on motivation for using redis is low latencies
        # so, let's try O(1sec) first and get an idea how this works
        self._timeout = 5
        # don't use timeouts less than 100ms
        if self._timeout < 0.1:
            self._timeout = 0.1
        self._fifo = fifo
        self._log = log
        # let's try to read a few values from the fifo and to do bulk inserts
        # starting with O(10)...
        self._n = 10
        self._canceled = Event()
        self._canceled.clear()

    def run(self):
        global _lock
        global _to_expire
        timeouts = [1, 2, 5, 10]
        try:
            while not self._canceled.is_set():
                try:
                    data = self._fifo.get(n=self._n, timeout=self._timeout)
                except InterruptedException:
                    self._log.info("request to cancel redis worker")
                    continue
                except:
                    self._log.exception("oups, unexpected exception... " +
                                        "ignore and continue")
                    continue
                i = 0
                while data and not self._canceled.is_set():
                    try:
                        expected_results = []
                        check_results = False
                        with self._client.pipeline(transaction=False) as p:
                            for new_key, key, t, val in data:
                                p.zadd(key, t, msgpack.packb((t, val)))
                                expected_results.append(None)
                                if (self._ttl is not None and
                                        (self._ttl_last_item or new_key)):
                                    p.expire(key, self._ttl)
                                    expected_results.append(1)
                                    check_results = True
                            results = p.execute()
                            if len(results) != len(expected_results):
                                raise RuntimeError("invalid response from execute")
                            if check_results:
                                for j in range(len(results)):
                                    if (expected_results[j] is not None and
                                            results[j] != expected_results[j]):
                                        raise RuntimeError("cannot set ttl")
                            data = None
                    except:
                        self._log.exception("cannot add data to %s" %
                                            (self._uri,))
                        self._canceled.wait(timeouts[i])
                        if i < (len(timeouts) - 1):
                            i += 1
                if data and self._ttl is not None:
                    with _lock:
                        for new_key, key, t, val in data:
                            if self._ttl_last_item or new_key:
                                _to_expire.add(key)
        except:
            self._log.exception("exiting redis worker")
        else:
            self._log.info("exiting redis worker")

    def cancel(self):
        self._canceled.set()


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the redis registry to register a property
    and to create a buffer that stores data in redis.
    """
    def __init__(self,
                 uri="redis://localhost:6379/0",
                 ttl=timedelta(seconds=1800),
                 ttl_last_item=False,
                 fifo_size=1000,
                 n_workers=1,
                 worker_is_daemon=False,
                 log=None,
                 *args, **kwargs):
        """
        ctor.

        @param uri: redis URI. Optional, default is "redis://localhost:6379/0".
        @type uri: string
        @param ttl: Data is currently stored in 15 minutes long chunks per
        property. A chunk will expire after its 'time to live'.
        The ttl can be given as a timedelta, a 'number of seconds' or None
        in case a chunk should never expire. Optional, default is 30 minutes.
        @type ttl: datetime.timedelta or int or float or NoneType
        @param ttl_last_item: Trigger the ttl watch when a new chunk is created
        or when the last value is inserted. Optional, default is False.
        @param ttl_last_item: bool
        @param fifo_size: Sets the upperbound limit on the number of values
        that can be placed in the FIFO before overwriting older values.
        The FIFO decouples the producers of monitoring data (frontend,
        backend buffers) and the consumer thread(s) that insert(s) the data
        into redis. Optional, default is 1000.
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
        self._log.debug("creating a redis registry")
        self._uri = uri
        self._chunk_size = timedelta(seconds=900)
        if ttl is None or isinstance(ttl, timedelta):
            self._ttl = ttl
        else:
            self._ttl = timedelta(seconds=ttl)
        if self._ttl is not None:
            if not ttl_last_item and (self._ttl < 2 * self._chunk_size):
                raise RuntimeError("The chunk size is currently %s." %
                                   (self._chunk_size,) + " " +
                                   "TTL of a chunk should be 2x longer " +
                                   "than that.")
            elif ttl_last_item and (self._ttl < self._chunk_size):
                raise RuntimeError("The chunk size is currently %s." %
                                   (self._chunk_size,) + " " +
                                   "TTL of a chunk should be longer " +
                                   "than that.")
        self._ttl_last_item = ttl_last_item

        self._client = redis.StrictRedis.from_url(uri)

        self._worker_is_daemon = worker_is_daemon
        if n_workers <= 0:
            n_workers = 1
        self._fifo = RingBuffer(fifo_size)
        self._workers = []  # keep this the last class member variable in ctor
        for _ in range(n_workers):
            worker = _Worker(uri, self._client,
                             self._ttl, self.ttl_last_item,
                             self._fifo, self._log)
            worker.daemon = worker_is_daemon
            worker.start()
            self._workers.append(worker)

    def _check_name(self, name, description):
        if not isinstance(name, basestring):
            raise TypeError("check " + description)
        if not name:
            raise ValueError("check " + description)

    def _insert_description(self, property_desc, force):
        ct = property_desc["component_type"]
        cn = property_desc["component_name"]
        pn = property_desc["property_name"]
        key = ":".join([ct, cn, pn])
        val = msgpack.packb(property_desc)
        if force:
            with self._client.pipeline() as p:
                p.hincrby("properties", "rev", 1)
                p.hset("properties", key, val)
                results = p.execute()
                if not results[1]:
                    self._log.warn("a property description for %s/%s existed" %
                                   (cn, pn) + " " +
                                   "and was replaced!")
        else:
            with self._client.pipeline() as p:
                while 1:
                    try:
                        p.watch("properties")
                        orig_val = p.hget("properties", key)
                        if orig_val is not None:
                            orig_property_desc = msgpack.unpackb(orig_val)
                            if orig_property_desc != property_desc:
                                raise UserWarning("a different property " +
                                                  "description for %s/%s" %
                                                  (cn, pn) + " " +
                                                  "is existing")
                            else:
                                self._log.info("a property description " +
                                               "for %s/%s is existing" %
                                               (cn, pn) + " - " +
                                               "is another recorder running?")
                        else:
                            p.multi()
                            p.hincrby("properties", "rev", 1)
                            p.hset("properties", key, val)
                            p.execute()
                        break
                    except redis.WatchError:
                        continue

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        @raise TypeError: if component type, component name or
        property name is not a string.
        @raise ValueError: if component type, component name or
        property name is empty.
        @raise UserWarning: if a property with similar component type,
        component name and property name, but different property type,
        property type description or meta data was already registered
        before.
        One can force (=True) register to succeed.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        """
        self._log.info("registering %s/%s" % (component_name, property_name))
        # we actually don't care too much here what parameters are given
        # however, component name and property name are the main
        # characteristics to identify a property so we will check these
        # component type is also important for bookkeeping
        self._check_name(component_type, "component_type")
        self._check_name(component_name, "component_name")
        self._check_name(property_name, "property_name")
        property_desc = {"component_name": component_name,
                         "component_type": component_type,
                         "property_name": property_name,
                         "property_type": str(property_type),
                         "property_type_desc": property_type_desc,
                         "meta": meta,
                         "chunk_size":
                         get_total_seconds(self._chunk_size, True),
                         "ttl": get_total_seconds(self._ttl, False)}
        self._insert_description(property_desc, force)
        return Buffer(self._log, self._fifo, self._chunk_size,
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
            global _lock
            global _to_expire
            if not self._worker_is_daemon:
                for worker in self._workers:
                    worker.cancel()
                self._fifo.terminate()
                for worker in self._workers:
                    worker.join()
            if self._ttl is not None:
                with self._client.pipeline(transaction=False) as p:
                    with _lock:
                        for key in _to_expire:
                            p.expire(key, self._ttl)
                    p.execute()
        except:
            pass
