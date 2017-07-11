__version__ = "$Id$"


"""
The dummy registry and buffer.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""


class Buffer(object):
    """This is a dummy buffer to store monitoring/time series data in."""

    def __init__(self, *args, **kwargs):
        """ctor."""
        self._log = None

    def add(self, tm, dt):
        """
        Add/push a data point to/into the buffer.

        @param tm: The time of the observation.
        @type tm: long, float or datetime?
        @param dt: The observation data.
        @type dt: a type that corresponds to property_type (cf. Registry.register()).
        """
        pass

    def flush(self):
        """Flush the data towards the backend."""
        pass

    def close(self):
        """
        Flush the data and close this buffer/the backend connection
        ("unregister" the property).
        """
        pass

    def set_logger(self, log):
        """
        Set the logger that is used to publish log messages.

        The logger within the Buffer is either undefined (like for the dummy)
        or usually set via the registry.
        set_logger() provides the chance to use an external one.

        @param log: An external logger.
        """
        log.debug("setting a new logger")
        self._log = log

    log=property(fset=set_logger)


class Registry(object):
    """
    This is the dummy registry to register a property
    and to create a buffer to store its monitoring data in.
    """

    def __init__(self, log=None, *args, **kwargs):
        """
        ctor.

        @param log: An external logger to write log messages to.
        Optional, default is None.
        """
        self._log = log

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        Register a property and create the buffer for its data.

        @param component_name: The component that "owns" the property.
        @type component_name: string
        @param component_type: The type of the component.
        @type component_type: string
        @param property_name: The property name.
        @type property_name: string
        @param property_type: The property type.
        @type property_type: ctamonitoring.property_recorder.backend.property_type.PropertyType
        @param property_type_desc: Some property types need additional
        information to use the property monitoring data later.
        An enumeration is an example. Enumeration monitoring data is
        an integer. However, to relate these values to a "tag" one should
        provide a dictionary "tags -> values" here.
        Optional(None).
        @type property_type_desc: typically dict
        @param disable: The property recorder might detect a property within
        the system, but decide not to monitor it.
        It might still log the detection via this call but "disable"
        the buffer that is returned. Optional(False).
        @type disable: boolean
        @param force: Some backends my refuse to register a property if it was
        registered once before and not "unregistered" appropriately afterwards.
        But one can force it this way.
        @type force: boolean
        @param meta: Optional property characteristics such as "units"
        or "format" etc.
        @type meta: dict
        @return: The buffer.
        @rtype: ctamonitoring.property_recorder.backend.dummy.registry.Buffer
        @note: Call Buffer.close() to "cancel" a property even if it is
        disabled.
        @note contextlib.closing returns a context manager that closes
        a buffer upon completion of the block in a with statement.
        """
        return Buffer()

    def set_logger(self, log):
        """
        Set the logger that is used to write log messages to.

        The logger within the Registry is either undefined (like for the dummy)
        or usually set via getLogger(__name__).
        set_logger() provides the chance to use an external one.

        @param log: An external logger.
        @note: Buffers typically inherit the registry's logger.
        """
        log.debug("setting a new logger")
        self._log = log

    log = property(fset=set_logger)
