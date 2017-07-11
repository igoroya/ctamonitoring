__version__ = "$Id$"


"""
The log registry and buffer.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: ctamonitoring.property_recorder.backend.dummy.registry
@requires: ctamonitoring.property_recorder.backend.property_type
@requires: ctamonitoring.property_recorder.backend.util
@requires: Acspy.Common.Log or logging
"""


import ctamonitoring.property_recorder.backend.dummy.registry
from ctamonitoring.property_recorder.backend.util import to_datetime
from ctamonitoring.property_recorder.backend.util import to_string
from ctamonitoring.property_recorder.backend.util import get_enum_inverted_desc
from ctamonitoring.property_recorder.backend.log import __name__ as defaultname
from ctamonitoring.property_recorder.backend.property_type import PropertyType

try:
    from Acspy.Common.Log import getLogger
except ImportError:
    # use the standard logging module if this doesn't run in an ACS system
    from logging import getLogger


class Buffer(ctamonitoring.property_recorder.backend.dummy.registry.Buffer):
    """
    This buffer doesn't store monitoring/time series data but writes it to the log.
    """
    def __init__(self, log,
                 component_name,
                 property_name, property_type, property_type_desc,
                 disable):
        """
        ctor.

        @param log: The logger to write data to.
        @type log: logging.Logger
        @param component_name: Component name and
        @type component_name: string
        @param property_name: property name this buffer will receive data from.
        @type property_name: string
        @param property_type: The property type.
        @type property_type: ctamonitoring.property_recorder.backend.property_type.PropertyType
        @param property_type_desc: The property type description.
        Enums typically provide additional information to convert an enum integer
        value into a string - an enum's raw data representation is an integer.
        All other property types don't need a property type description.
        @type property_type_desc: dict
        @param disable: Create a buffer for a property that was detected
        but isn't actually monitored. This will only allow for calling
        Buffer.close().
        @type disable: boolean
        """
        log.debug("creating buffer %s/%s" % (component_name, property_name))
        super(Buffer, self).__init__()
        self._log = log
        self._component_name = component_name
        self._property_name = property_name
        self._property_type = property_type
        if property_type is PropertyType.ENUMERATION:
            self._property_type_desc = \
                get_enum_inverted_desc(property_type_desc)
        else:
            self._property_type_desc = property_type_desc
        self._disable = disable
        self._canceled = False

    def add(self, tm, dt):
        """
        Write data to the log.

        @raise RuntimeError: If buffer is closed.
        @warning: Creates log warnings if called although property/buffer
        is disabled.
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.add()
        """
        if self._canceled:
            raise RuntimeError("unregistered property %s/%s - buffer is closed." %
                               (self._component_name, self._property_name))
        if not self._disable:
            self._log.info("%s/%s(%s) = %s" %
                           (self._component_name, self._property_name,
                            to_datetime(tm).isoformat(),
                            to_string(dt, self._property_type,
                                      self._property_type_desc)))
        else:
            self._log.warn("property monitoring for %s/%s is disabled" %
                           (self._component_name, self._property_name))

    def close(self):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Buffer.close()
        """
        if not self._canceled:
            self._log.info("closing %s/%s" %
                           (self._component_name, self._property_name))
        self._canceled = True


class Registry(ctamonitoring.property_recorder.backend.dummy.registry.Registry):
    """
    This is the log registry to register a property
    and to create a buffer that writes data to the log.
    """

    def __init__(self, log=None, *args, **kwargs):
        """
        ctor.

        @param log: An external logger to write log messages to.
        Optional, default is None.
        """
        super(Registry, self).__init__(log, *args, **kwargs)
        if not self._log:
            self._log = getLogger(defaultname)
        self._log.debug("creating a log registry")

    def register(self,
                 component_name, component_type,
                 property_name, property_type, property_type_desc=None,
                 disable=False, force=False, *args, **meta):
        """
        @see ctamonitoring.property_recorder.backend.dummy.registry.Registry.register()
        """
        self._log.info("registering %s/%s" % (component_name, property_name))
        return Buffer(self._log,
                      component_name,
                      property_name, property_type, property_type_desc,
                      disable)
