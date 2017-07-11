__version__ = "$Id: registry.py 600 2013-09-24 20:53:25Z tschmidt $"


"""
The fork registry and buffer.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: registry.py 600 2013-09-24 20:53:25Z tschmidt $
@change: $LastChangedDate: 2013-09-24 22:53:25 +0200 (Di, 24 Sep 2013) $
@change: $LastChangedBy: tschmidt $
@requires: ctamonitoring.property_recorder.backend
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: ctamonitoring.property_recorder.backend.exceptions
@requires: ctamonitoring.property_recorder.backend.ring_buffer
@requires: threading
@requires: Acspy.Common.Log or logging
"""


from ctamonitoring.property_recorder.backend import get_registry_class
import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.exceptions \
    import InterruptedException
from ctamonitoring.property_recorder.backend.ring_buffer import RingBuffer
from ctamonitoring.property_recorder.backend.simple_fork \
    import __name__ as defaultname
from threading import Event
from threading import Thread

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger


class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
    """This is the fork buffer that adds data to its child buffers."""
    def __init__(self, log, fifo, strict, buffers,
                 component_name, property_name):
        """
        ctor.

        @param log: The logger to publish log messages.
        @type log: logging.Logger
        @param fifo: The FIFO that is the input for the workers.
        @type fifo: ctamonitoring.property_recorder.backend.ring_buffer.RingBuffer
        @param strict: The buffer may raise an exception if an operation
        such as flush fails. A strict buffer raises an exception already if
        the operation fails at one and more backends/child buffers.
        A "lazy" buffer only raises an exception if the operation fails at
        every backend/child buffer.
        @type strict: boolean
        @param buffers: This is the list of backends/child buffers the fork
        is forking into.
        The list also provides an ID/name per backend/buffer.
        @type buffers: list of (string, Buffer) pairs
        @param component_name: Component name and
        @type component_name: string
        @param property_name: property name this buffer will receive data from.
        @type property_name: string
        """
        log.debug("creating buffer %s/%s" % (component_name, property_name))
        super(Buffer, self).__init__()
        self._log = log
        self._fifo = fifo
        self._strict = strict
        self._buffers = buffers
        self._component_name = component_name
        self._property_name = property_name
        self._cannot_add = Event()
        self._cannot_add.clear()
        self._canceled = False  # keep this the last line in ctor

    def add(self, tm, dt):
        """
        @raise RuntimeError: If buffer is closed.
        @raise RuntimeError: In case a worker cannot add to one and more
        (strict) or to any (lazy) backend/child buffer before.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        """
        if self._canceled:
            raise RuntimeError("unregistered property %s/%s - buffer is closed." %
                               (self._component_name, self._property_name))

        if self._cannot_add.is_set():
            self._cannot_add.clear()
            raise RuntimeError("cannot add %s/%s at %d" %
                               (self._component_name, self._property_name))
        self._fifo.add((self, tm, dt))

    def _add(self, tm, dt):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        """
        err = 0
        for id, buffer in self._buffers:
            try:
                buffer.add(tm, dt)
            except:
                self._log.exception("cannot add %s/%s at %s" %
                                    (self._component_name,
                                     self._property_name, id))
                err += 1
        if err and (self._strict or err >= len(self._buffers)):
            self._cannot_add.set()

    def flush(self):
        """
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry.
        @raise RuntimeError: if fork cannot flush one and more (strict)
        or any (lazy) backends/child buffers.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.flush()
        """
        if not self._canceled:
            self._fifo.flush(current=True)

            err = 0
            for id, buffer in self._buffers:
                try:
                    buffer.flush()
                except:
                    self._log.exception("cannot flush %s/%s at %s" %
                                        (self._component_name,
                                         self._property_name, id))
                    err += 1
            if err and (self._strict or err >= len(self._buffers)):
                raise RuntimeError("cannot flush %s/%s at %d buffers" %
                                   (self._component_name,
                                    self._property_name, err))

    def close(self):
        """
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if the FIFO is terminated by the parent registry.
        @raise RuntimeError: if fork cannot close one and more (strict)
        or any (lazy) backends/child buffers.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        """
        if not self._canceled:
            self.flush()

            err = 0
            for id, buffer in self._buffers:
                try:
                    buffer.close()
                except:
                    self._log.exception("cannot close %s/%s at %s" %
                                        (self._component_name,
                                         self._property_name, id))
                    err += 1
            if err and (self._strict or err >= len(self._buffers)):
                raise RuntimeError("cannot close %s/%s at %d buffers" %
                                   (self._component_name,
                                    self._property_name, err))

            self._canceled = True

    def __del__(self):
        """
        dtor.
        """
        # The dtor is called even if the ctor didn't run through.
        # So, make sure the ctor did work by using self._canceled
        # and catching a potential AttributeError (well, catch all).
        try:
            if not self._canceled:
                try:
                    self.close()
                except InterruptedException:
                    self._log.warn("cannot close buffer %s/%s appropriately"
                                   % (self._component_name,
                                      self._property_name))
                except:
                    self._log.warn("cannot close buffer %s/%s"
                                   % (self._component_name,
                                      self._property_name))
        except:
            pass


class _Worker(Thread):
    def __init__(self, fifo, log):
        super(_Worker, self).__init__()
        log.debug("creating fork worker")
        self._fifo = fifo
        self._log = log
        self._timeout = 0.25
        self._canceled = Event()
        self._canceled.clear()
        self._blah = 0

    def run(self):
        try:
            while not self._canceled.is_set():
                try:
                    items = self._fifo.get(n=1, timeout=self._timeout)
                except InterruptedException:
                    self._log.info("request to cancel fork worker")
                    continue
                except:
                    self._log.exception("oups, unexpected exception... " +
                                        "ignore and continue")
                    continue
                for buffer, tm, dt in items:
                    buffer._add(tm, dt)
                self._blah += len(items)
        except:
            self._log.exception("exiting fork worker")
        else:
            self._log.info("exiting fork worker %d" % self._blah)

    def cancel(self):
        self._canceled.set()


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the fork registry.

    The fork creaties second level backends so called childs.
    It registers a given property at these childs (Registry) and adds
    property data to their buffers (Buffer).
    """
    def __init__(self,
                 backends,
                 strict=False,
                 fifo_size=1000,
                 n_workers=1,
                 worker_is_daemon=False,
                 log=None,
                 *args, **kwargs):
        """
        ctor.

        @param backends: This is a list of backend names and configurations.
        The actual backends are created using:
        get_registry_class(name)()
        @type backends: list of (string, dict) pairs
        @param strict: Fork may raise an exception if
        a buffer operation such as flush fails. A strict buffer raises
        an exception already if the operation fails at one and more childs.
        A "lazy" buffer only raises an exception if the operation fails
        at every child.
        @type strict: boolean
        @param fifo_size: Sets the upperbound limit on the number of
        data points that can be placed in the FIFO before overwriting
        older data.
        The FIFO decouples the producers of monitoring data (frontend,
        backend buffers, add) and the consumer thread(s)/workers
        that add(s) the data to the childs. Optional, default is 1000.
        @type fifo_size: int
        @param n_workers: Number of consumer threads/workers.
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
        self._log.debug("creating a fork registry")
        self._registries = []
        for backend_name, backend_config in backends:
            r = get_registry_class(backend_name)
            self._registries.append((backend_name, r(**backend_config)))
        self._strict = strict

        self._worker_is_daemon = worker_is_daemon
        if n_workers <= 0:
            n_workers = 1
        self._fifo = RingBuffer(fifo_size)
        self._workers = []  # keep this the last class member variable in ctor
        for _ in range(n_workers):
            worker = _Worker(self._fifo, self._log)
            worker.daemon = worker_is_daemon
            worker.start()
            self._workers.append(worker)

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        """
        self._log.info("registering %s/%s" % (component_name, property_name))
        buffers = []
        for id, r in self._registries:
            try:
                buffers.append((id,
                                r.register(component_name, component_type,
                                           property_name, property_type,
                                           property_type_desc,
                                           disable, force, *args, **meta)))
            except:
                self._log.exception("cannot register %s/%s at %s" %
                                    (component_type, component_name, id))
                for id, buffer in buffers:
                    try:
                        buffer.close()
                    except:
                        self._log.exception("cannot close buffer")
                raise RuntimeError("cannot register %s/%s at %s" %
                                   (component_type, component_name, id))

        return Buffer(self._log, self._fifo, self._strict, buffers,
                      component_name, property_name)

    def __del__(self):
        """
        dtor.
        """
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
