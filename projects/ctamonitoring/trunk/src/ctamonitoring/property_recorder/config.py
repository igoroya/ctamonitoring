__version__ = "$Id: config.py 1 2015-01-01 00:40:12Z igoroya $"


'''
Module with all what is related to the configuration holding for the property 
recorder frontend

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: config.py 1 2015-20-3 00:40:12Z igoroya $
@change: $LastChangedDate: 2015-20-3  02:40:12 +0200 (Wed, 25 Sep 2013) $
@change: $LastChangedBy: igoroya $
@requires: Enum
'''


from ctamonitoring.property_recorder.backend import get_registry_class 
from enum import Enum

BackendType = Enum('DUMMY', 'LOG', 'MYSQL', 'MONGODB')

backend_registries = {}
backend_registries[BackendType.DUMMY] = get_registry_class("dummy")
backend_registries[BackendType.LOG] = get_registry_class("log")
backend_registries[BackendType.MYSQL] = None
backend_registries[BackendType.MONGODB] = get_registry_class("mongodb")

class RecorderConfig(object):
    """
    Holds the configuration from the property recorder

    Attributes:
    default_monitor_rate -- Monitoring rate for those properties
                            with no CDB entry for the monitoring rate
                            in seconds (default 60 s)
    max_comps            -- Maximum number of components accepted by this
                            property recorder (default 100)
    max_props            -- Maximum number of properties being monitored
                            (default 1000)
    checking_period      -- Period in seconds to check for lost components or new components
                            (default 10 s)
    backend_type         -- Enum value of :class:`ctamonitoring.property_recorder.BackendType`  
                            (Default LOG)
    backend_config       -- Map with configuration parameters for the backend
                            (Default None)
   `is_include_mode      -- In True, the recorder will only consider the components 
                            included in list components and reject all the others 
                            (a include list). 
                            If set to False, will consider all the components except
                            those in the list (A exclude list)
    components         --   The include or exclude list, depending on the include_mode,
                            of component represented by their string names
  
    """
    #-------------------------------------------------------------------------
    def __init__(self):
        """
        Initializes the values to those defined as default:
        """
        # 1/min, units in in 100 of ns, OMG time
        self._default_monitor_rate = 60
        # will not accept more components if this number is exceeded
        self._max_comps = 100
        # will not accept more components if the total number of props is this
        # number or more
        self._max_props = 1000
        self._checking_period = 10  # seconds
        self._backend_type = BackendType.LOG
        self._backend_config = None
                
        self._is_include_mode = None

        self._components = []        
    
   
    @property
    def default_monitor_rate(self):
        """"
        The monitoring rate in s to be used when no input is provided in the CDB
        
        Raises a ValueError when input type is incorrect or value is negative        
        """
        return self._default_monitor_rate
    @default_monitor_rate.setter
    def default_monitor_rate(self, default_monitor_rate):
        rate = long(default_monitor_rate)
        if rate < 1:
            raise ValueError("default_monitoring_rate type must be positive")
        self._default_monitor_rate = rate
  
    @property      
    def max_comps(self):
        """"
        The maximum number of components that the recorder will monitor.
        
        Raises a ValueError when input type is incorrect or value is negative        
        """
        return self._max_comps
    @max_comps.setter
    def max_comps(self, max_comps):
        comps = long(max_comps)
        if comps < 1:
            raise ValueError("max_comps type must be positive")
        self._max_comps = comps

    @property
    def max_props(self):
        """"
        The total maximum number of properties, including all the components, 
        that the recorder will monitor.
        
        Raises a ValueError when input type is incorrect or value is negative        
        """
        return self._max_props
    max_props.setter
    @max_props.setter
    def max_props(self, max_props):
        props = long(max_props)
        if props < 1:
            raise ValueError("max_props type must be positive")
        self._max_props = props
        
    @property  
    def checking_period(self):
        """"
        The period in s that the recorder uses to find new components in the system
        
        Raises a ValueError when input type is incorrect or value is negative        
        """
        return self._checking_period
    @checking_period.setter
    def checking_period(self, checking_period):
        period = long(checking_period)
        if period < 1:
            raise ValueError("checking_period checking period must be > 1 s")
        self._checking_period = period

    @property
    def backend_type(self):
        return self._backend_type
    @backend_type.setter
    def backend_type(self, backend_type):
        try:
            BackendType._values.index(backend_type)
        except ValueError:
            raise ValueError("Backend type not recognized. Supported types are " 
                     + str(BackendType._keys))
        self._backend_type = backend_type
    
    @property
    def is_include_mode(self):
        """"
        The mode to handle the component list. If true, the property recorder works in include mode
        which means that will only monitor those components in the list
        
        If false, the list will be used as an exclude mode, and therefore any component accessible 
        will be used except those in the list    
        """
        return self._is_include_mode 
    @is_include_mode.setter
    def is_include_mode(self, include_mode):
        if type(include_mode) is not bool:
            raise TypeError("include_mode must be True or False")
        self._is_include_mode  = include_mode
  
        
    @property
    def components(self):
        return self._components
    @components.setter
    def components(self, components):
        raise NotImplementedError("Cannot mutate, components are set by setComponentList")
    
    
    def setComponentList(self, components):
        """
        Replaces the actual list of components by the provided one.
        
        Throws a TypeError if any of the components in the list is not str
        """
        if type(components) is not list:
            raise TypeError("A list of str needs to be provided")
        
        for component in components:
            if type(component) is not str:
                raise TypeError("components need to be represented as str, a " 
                                + str(type(component)) + "was provided")
  
        self._components = components
    
    
    