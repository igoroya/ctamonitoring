__version__ = "$Id: registry.py 600 2013-09-24 20:53:25Z tschmidt $"


"""
The simple fork registry and buffer.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: registry.py 600 2013-09-24 20:53:25Z tschmidt $
@change: $LastChangedDate: 2013-09-24 22:53:25 +0200 (Di, 24 Sep 2013) $
@change: $LastChangedBy: tschmidt $
@requires: ctamonitoring.property_recorder.backend
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: Acspy.Common.Log or logging
"""


from ctamonitoring.property_recorder.backend import get_registry_class
import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.simple_fork \
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
        log.debug("creating buffer %s/%s" % (component_name, property_name))
        super(Buffer, self).__init__()
        self._log = log
        self._strict = strict
        self._buffers = buffers
        self._component_name = component_name
        self._property_name = property_name

    def add(self, tm, dt):
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
            raise RuntimeError("cannot add %s/%s at %d buffers" %
                               (self._component_name,
                                self._property_name, err))

    def flush(self):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.flush()
        """
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
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        """
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


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the simple fork registry.

    The simple fork creaties second level backends so called childs.
    It registers a given property at these childs (Registry) and adds
    property data to their buffers (Buffer).
    """
    def __init__(self, backends, strict=False, log=None, *args, **kwargs):
        """
        ctor.

        @param backends: This is a list of backend names and configurations.
        The actual backends are created using:
        get_registry_class(name)(**config)
        @type backends: list of (string, dict) pairs
        @param strict: Simple fork may raise an exception if
        a buffer operation such as add fails. A strict buffer raises
        an exception already if the operation fails at one and more childs.
        A "lazy" buffer only raises an exception if the operation fails
        at every child.
        Optional, default is False.
        @type strict: boolean
        @param log: An external logger to write log messages to.
        Optional, default is None.
        @type log: logging.Logger
        """
        super(Registry, self).__init__(log, *args, **kwargs)
        if not self._log:
            self._log = getLogger(defaultname)
        self._log.debug("creating a simple fork registry")
        self._registries = []
        for backend_name, backend_config in backends:
            r = get_registry_class(backend_name)
            self._registries.append((backend_name, r(**backend_config)))
        self._strict = strict

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

        return Buffer(self._log, self._strict, buffers,
                      component_name, property_name)
