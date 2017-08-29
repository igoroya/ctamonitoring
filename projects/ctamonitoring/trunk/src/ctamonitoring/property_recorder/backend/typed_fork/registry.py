__version__ = "$Id$"


"""
The typed fork registry.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: ctamonitoring.property_recorder.backend
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: Acspy.Common.Log or logging
"""

from ctamonitoring.property_recorder.backend import get_registry_class
from ctamonitoring.property_recorder.backend.property_type import PropertyType
import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.typed_fork \
    import __name__ as defaultname

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger


    class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
        """This is the simple fork buffer that adds data to its child buffers."""

        def __init__(self, log, strict, buffers, component_name, property_name):
            """
            ctor.

            @param log: The logger to publish log messages.
            @type log: logging.Logger
            @param strict: The buffer may raise an exception if an operation
            such as add fails. A strict buffer raises an exception already if
            the operation fails at one and more backends/child buffers.
            A "lazy" buffer only raises an exception if the operation fails at
            every backend/child buffer.
            @type strict: boolean
            @param buffers: This is the list of backends/child buffers the simple
            fork is forking into.
            The list also provides an ID/name per backend/buffer.
            @type buffers: list of (string, Buffer) pairs
            @param component_name: Component name and
            @type component_name: string
            @param property_name: property name this buffer will receive data from.
            @type property_name: string
            """
            super(Buffer, self).__init__()
            self._buffer = buffer
            self._default_buffer = default_buffer

        def add(self, tm, dt):
            """
            @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
            """
            self._buffer.add(tm, dt)

        def flush(self):
            """
            @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.flush()
            """
            self._buffer.flush()

        def close(self):
            """
            @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
            """
            redo = False
            if self._default_buffer is not None:
                try:
                    self._buffer.close()
                except:
                    redo = True
                self._default_buffer.close()
            if self._default_buffer is None or redo:
                self._buffer.close()


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the typed fork registry.

    The typed fork creates second level backends so called childs
    - there will be a default child that will receive all 'untyped' data
    and possibly additional childs that may receive corresponding 'typed' data.
    An example: You want to record all float data in Akumuli, but data
    of different type in MongoDB. Your choice for the default child is
    the MongoDB backend and the choice for the 'float backend' is the
    Akumuli backend.
    """
    def __init__(self, default_backend, typed_backends=[],
                 log=None, *args, **kwargs):
        """
        ctor.

        @param default_backend: This is the name and configuration
        of the default backend. The actual backend is created using:
        get_registry_class(name)(**config)
        @type default_backend: (string, dict) pair
        @param typed_backends: This is a list of property types,
        backend names and configurations of the 'typed backends'.
        @type typed_backends: list of (string,..., string, dict)
        tuples/lists. The last string is the particular backend name.
        The strings before name the property types such as 'FLOAT'.
        @param log: An external logger to write log messages to.
        Optional, default is None.
        @type log: logging.Logger
        """
        super(Registry, self).__init__(log, *args, **kwargs)
        if not self._log:
            self._log = getLogger(defaultname)
        self._log.debug("creating a typed fork registry")

        self._default_backend_name, backend_config = default_backend
        self._log.info("create default registry %s" %
                       (self._default_backend_name,))
        try:
            r = get_registry_class(self._default_backend_name)
            self._default_backend = r(**backend_config)
        except:
            self._log.exception("cannot create default registry %s" %
                                (self._default_backend_name,))
            raise

        self._typed_backend_names = {}
        self._typed_backends = {}
        try:
            for typed_backend in typed_backends:
                backend_name = typed_backend[-2]
                backend_config = typed_backend[-1]
                ptypes = typed_backend[:-2]
                backend = None
                for t in ptypes:
                    try:
                        ptype = getattr(PropertyType, t.upper())
                        if ptype in self._typed_backends:
                            bn = self._typed_backend_names[ptype]
                            raise RuntimeError("registry %s " % (bn,) +
                                               "already configured " +
                                               "for property type: %s " %
                                               (t.upper(),) +
                                               "can't use %s in addition" %
                                               (backend_name),)
                    except AttributeError:
                        self._log.exception("invalid property type: %s" %
                                            (t.upper(),))
                        raise
                    if backend is None:
                        self._log.info("create registry %s" % (backend_name,))
                        try:
                            r = get_registry_class(backend_name)
                            backend = r(**backend_config)
                        except:
                            self._log.exception("cannot create registry %s" %
                                                (backend_name,))
                            raise
                    self._typed_backend_names[ptype] = backend_name
                    self._typed_backends[ptype] = backend
        except:
            del self._typed_backends
            del self._default_backend
            raise

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        """
        if property_type in self._typed_backends:
            n = self._typed_backend_names[property_type]
            r = self._typed_backends[property_type]
            default_n = self._default_backend_name
            default_r = self._default_backend
        else:
            n = self._default_backend_name
            r = self._default_backend
            default_n = None
            default_r = None
        buffers = []
        for name, registry, do_disable in ((n, r, disable),
                                           (default_n, default_r, True)):
            if registry is None:
                buffers.append(None)
            else:
                self._log.info("registering %s/%s at %s" %
                               (component_name, property_name, name))
                try:
                    b = registry.register(component_name, component_type,
                                          property_name, property_type,
                                          property_type_desc,
                                          do_disable, force, *args, **meta)
                    buffers.append(b)
                except:
                    self._log.exception("cannot register %s/%s at %s" %
                                        (component_name, property_name, name))
                    if buffers:
                        try:
                            buffers[0].close()
                        except:
                            pass
                    raise
        return Buffer(*buffers)
