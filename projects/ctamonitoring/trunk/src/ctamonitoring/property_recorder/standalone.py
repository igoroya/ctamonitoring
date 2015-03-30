from ctamonitoring.property_recorder import recorder
from ctamonitoring.property_recorder.recorder import STORAGE_TYPE

import threading
import collections
from __builtin__ import str
from ctamonitoring.property_recorder.config import backend_registries
from ctamonitoring.property_recorder.config import PropertyAttributeHandler
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.util import  PropertyTypeUtil
from ctamonitoring.property_recorder.util import ComponentUtil
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder.callbacks import CBFactory
import ACS
import ACS__POA

PropertyType = property_type.PropertyType

ComponentInfo = collections.namedtuple(
                    'componentInfo',
                    ['compReference',
                    'monitors'],
                    verbose=False)
'''
compReference -- the CORBA reference to the component
monitors      -- list with the monitor objects associated to the component
'''

class standalone(recorder.recorder):

    """
    For using the standalone version of the PropertyRecorder.
    See recorder.py for details.

    @author: igoroya
    @organization: HU Berlin
    @copyright: cta-observatory.org
    @version: $Id$
    @change: $LastChangedDate$, $LastChangedBy$
    """
    #-------------------------------------------------------------------------

    def __init__(self):
        # TODO: the storage stuff should be removed
        recorder.recorder.__init__(self)
        self._checkThread = self._createComponentFindThread()
        self._checkThread.start()
        
        "List of ACS components to use as include, or exclude list"
        self.__predefinedComponents = []
        '''If include mode, only the components considered in the scanning. 
        If false, all the components deployed are considered except those in the list,
        which will be excluded'''
        

    #-------------------------------------------------------------------------
    def _scanForComps(self):
        """
        Scans the system, locate containers,
        their components and their properties.
        """

        self.getlogger.logInfo("called...")

        if (self._isFull):
            self.getlogger.logInfo("property recorder is full, returning")
            return

        # try:
        activatedComponents = self.availableComponents("*", "*", True)

        nAvComps = len(activatedComponents)
        self.getlogger.logInfo('found ' + str(nAvComps) + ' components')

        # Check the availableComponent, only those which are already activated
        countComp = 0
        while (countComp < nAvComps):
            componentId = self.findComponents("*", "*", True)[countComp]
            self.getlogger.logInfo(
                "inspecting component: " + str(componentId))
            self.getlogger.logInfo("self name: " + str(self.getName()))

            if not self.addComponent(componentId):
                countComp = countComp + 1  # continue with the loop then
                continue

        self.getlogger.logInfo("done...")
        

    def _createComponentFindThread(self):
        return standalone.ComponentFindThread(self)

    #-------------------------------------------------------------------------
    class ComponentFindThread(recorder.recorder.ComponentCheckThread):

        """
        Inner class defining a thread to the check components
        Overriding recorder.recorder.ComponentCheckThread to scan
        for new components as well.
        """

        def __init__(self, recorderInstance):
            recorder.recorder.ComponentCheckThread.__init__(
                self, recorderInstance)

        def _run(self):
            # First check if we lost any property
            self._recorderInstance._checkLostComponents()
            # now look for new properties
            self._recorderInstance._scanForComps()



class FrontEnd(object):
    '''
    The core class of the property recorder front-end
    Keeps a track of the existing components
    Takes care of opening buffers in the DB backends
    
    Requires to have ACS up and running to run
    '''
    
    def __init__(self, recorder_config, acs_client):
        '''
        recorder_config -- the setup parameters for the recorder
        acs_client      -- the instance of the ACS client, or component where the 
                           recorder is hosted, that provides access to the ACS world
        '''
        # dictionary to store the components with acquired references
        self._componentsMap = ComponentStore()

        self._isRecording = threading.Event()

        # get threading lock to make some methods synchronized
        self._lock = threading.RLock()

        self._component_whatchdog = None
        
        self.recorder_config = recorder_config
        
        self.recoder_space = RecorderSpaceMonitor(self._componentsMap, 
                                                recorder_config.max_comps,  
                                                recorder_config.max_props)
        
        self.logger = acs_client.getLogger()
        
        self.acs_client = acs_client
        
        self._registry = None
        
        self._setup_backend()
        
        self._start_watchdog()
    #TODO: Add a destructor
    
    def __del__(self):
        """
        Stops the check thread, releases the components and closes teh registry
        """
        self.logger.logDebug("destroying...")
        
        #self._component_whatchdog.reset()
        
        self._component_whatchdog.stop()
        
        self._component_whatchdog = None

        #This step flushes all the data to the backend
        self._release_all_comps()
                
        self._registry = None;
    
    def _setup_backend(self):
        if self.recorder_config.backend_config is None:
            self._registry = backend_registries[self.recorder_config.backend_type]()   
        else :
            self._registry = backend_registries[self.recorder_config.backend_type](**self.config.storage_config)   
        
    def _start_watchdog(self):
        # if it is an standalone recorder this will be created by the parent
        # class
        if self._component_whatchdog is None:
            self._component_whatchdog = self._create_component_whatchdog()
            self._component_whatchdog.start()
    
    def _create_component_whatchdog (self):
        return ComponentWhatchdog(self)
    
    
    def _remove_wrong_components(self):
        """
        Check if any component was lost or went into wrong state
        before last check
        Take action if it is the case
        """
        self.logger.logDebug("called...")
        self.logger.logDebug("acquiring lock")
        self._lock.acquire()
        try:
            length = len(self._componentsMap)

            for compName, compInfo in self._componentsMap.items() :

                comp_reference = compInfo.compReference
                
                self.logger.logDebug("checking component: " + compName)
                
                try: 
                    ComponentUtil.verify_component_state(comp_reference, compName)
                except Exception, e:
                    self.logger.logWarning(
                    "the component " + compName + " is in a wrong state, "+
                    str(e))
                    self._componentsMap.pop(compName)

            length -= len(self._componentsMap)

            if length > 0:
                self.getLogger(
                ).logInfo("%d component(s) removed from the records" %
                          (length,))
            else:
                self.logger.logDebug(
                    "no component was removed from the records")

            self.logger.logDebug("release lock")
        finally:
            self._lock.release()   
            
    def _scan_for_components(self):
        """
        Scans the system, locate containers,
        their components and their properties.
        """

        self.logger.logDebug("called...")

        if (self.recoder_space.isFull):
            self.logger.logWarning("property recorder is full, will not accept more components/properties!")
            return

        # try:
        activatedComponents = self.acs_client.availableComponents("*", "*", True)

        n_components = len(activatedComponents)

        if n_components is 0:
            self.logger.logDebug("No components active")
            return
        
        self.logger.logInfo('found ' + str(n_components) + ' components')

        # Check the availableComponent, only those which are already activated
        for count_comp in (0, n_components):
            
            try:
                component_id = activatedComponents[count_comp]
            except IndexError:
                self.logger.logDebug("Number of components was reduced, returning")
                return
            
            self.logger.logInfo(
                "inspecting component: " + str(component_id))

            #If working in INCLUDE mode and it is in the include list, add it
            if self.recorder_config.is_include_mode:
                if component_id in self.recorder_config.components:
                    self.process_component(component_id)
            
            #If working in EXCLUDE mode and it is NOT in the EXCLUDE list, add it
            if not self.recorder_config.is_include_mode:
                if not self.process_component(component_id):
                    self.process_component(component_id)
            
            
        self.logger.logInfo("done...")
        
    def process_component(self, component_id):
        """
        Verify a component in the recorder
        If it is not contained, insert it.
        
        Keyword arguments:
        component_id     -- string with the component ID

        returns True or False if it managed to insert or not the component
        """

        self.logger.logDebug("called...")

        self.logger.logDebug("take lock")
        self.__lock.acquire()
        
        result = False

        try:
        
            if self._componentsMap.has_key(component_id):
                self.logger.logDebug(
                    "the component " + component_id + 
                    " is already registered")
                return
            
            if self._can_be_added(component_id):
                try:
                    # get no sticky so we do not prevent them of being deactivated
                    component = self.getComponentNonSticky(component_id)
                except Exception, e:
                    self.logger.logWarning(
                        "could not get a reference to the component "+ str(component_id) + 
                        " due to an exception: "+ str(e))
                    return
        
                # skip other property recorders
                if(ComponentUtil.is_a_property_recorder_component(component)):
                    self.logger.logDebug("skipping other property recorders")
                    return
                
                comp_info = ComponentInfo(component, self._get_component_characteristics(component))

                self._componentsMap[component_id] = comp_info
                              
                result = True
            
            else:
                self._logger.logDebug("Component " +component_id 
                                  + " cannot be added")
                return 
                
        finally:
            self.logger.logDebug("release lock")
            self._lock.release()
            return result

        
    #-------------------------------------------------------------------------
    

    
    def _can_be_added(self, component_id):
        """
        Checks if the component can be stored

        Keyword arguments:
        componentId     -- string with the component ID

        returns True if can be stored, False if not
        """

        #TODO: Add here the Exclude/Include list

        if component_id in self._componentsMap:
            self.logger.logDebug(
                "the component " + component_id + " is already registered")
            return False
    
        # Skipping the self component to avoid getting a self-reference
        if(component_id == self.getName()):
            self.logger.logDebug("skipping myself")
            return False


        return True        
    
    
    def _get_component_characteristics(self, component_reference):
        """
        Find and evaluate the properties
        and characteristics of a Component
        It reads the CDB entry of the component and
        decoded and interprets it.
        
        It then forwards this to the backend and 
        returns the list of monitors

        Keyword arguments:
        component_reference  -- corba reference of the conponent

        Returns monitorList with all the monitors created, or None if not possible
        """
        
        #TODO Can raise exception, document it
        
        self.logger.logDebug("called...")

        component = component_reference

        if ComponentUtil.is_characteristic_component(component):
            return None

        monitor_list = []
        
        chars = component.find_characteristic("*")
        
        for count in range(0, len(chars)):
            myCharList = self._component.get_characteristic_by_name(
                str(chars[count])).value().split(',')
            # As a way of discerning from a property to other type of
            # characteristic, I check for the length of the char list. If it is
            # longer than 5, then is probably a property
            if (len(myCharList) > 5):
                self._logger.logDebug(
                    "probably is a property, trying the information of the archive")

                # Check if the characteristic is a property

                acs_property = self._get_acs_property(component,
                                                    chars[count])
                if acs_property is None:
                    continue

                if not PropertyTypeUtil.is_property_ok(acs_property):
                    continue


                property_attributes = (
                            PropertyAttributeHandler
                            .get_prop_attribs_cdb(
                                     acs_property, 
                                     ComponentUtil
                                     .is_python_char_component(component))
                    )
                
                try: 
                    my_buffer = self._create_buffer(acs_property, property_attributes)
                except Exception, e:
                    self.logger.logWarning(
                        "The buffer could not be created" + str(e))
                    continue
                
  
                property_monitor = self._create_monitor(
                                        acs_property, 
                                        property_attributes, 
                                        my_buffer)
              
                if property_monitor is not None:
                    monitor_list.append(object)

        return monitor_list   
      
    
       
            
    def _create_buffer(self, acs_property, property_attributes):
        '''
        Creates a buffer in the backend
        
        Returns buffer in the backend
        
        Raises:
        TypeError -- If the property type is not supported
        Exception  -- If any other problem happened when creating the buffers  
        '''
        my_prop_type = None
                          
        try:
            my_prop_type = PropertyTypeUtil.getPropertyType(
                acs_property._NP_RepositoryId)
        except Exception, e:
            self._logger.logWarning(
                "Property type not supported, skipping")
            raise TypeError(e)
        
        
        #TODO: Think in what to do with the enum states
        enumStates = None
          
        if (type is None) or (type is PropertyType.OBJECT):
                    my_prop_type = PropertyType.OBJECT #TODO: Try to get this from the PropertyUtil 
                    try:
                        enumStates = PropertyTypeUtil.getEnumPropDict(acs_property, self._logger)
                        self._logger.logDebug("Enum States found: "+str(enumStates))
                        
                    except Exception:
                        self._logger.logDebug(
                            "Enum states cannot be read, use the int representation")

        try:         
            my_buffer = self._registry.register(component_name = self._component._get_name(),
                               component_type = self._component._NP_RepositoryId,
                               property_name = acs_property._get_name(),
                               property_type = my_prop_type,
                               property_type_desc = enumStates, 
                               **property_attributes) 
        
        except UserWarning: 
            self._logger.logWarning(
                "Warning of buffer being used received, forcing in")
            my_buffer = self._registry.register(component_name = self._component._get_name(),
                                component_type = self._component._NP_RepositoryId,
                                property_name = acs_property._get_name(),
                                property_type = my_prop_type,
                                property_type_desc = enumStates, 
                                disable = False, 
                                force = True,
                                **property_attributes) 
        return my_buffer
        
        
    def _create_monitor(self, acs_property, property_attributes, my_buffer):
    
        try:
            time_trigger_omg = long(10000000 * my_buffer.get("default_timer_trig"))
           
        except Exception:
            self._logger.logDebug("no time trigger found in the CDB, "
                                  "using the default value")
            time_trigger_omg = 10000000 * self.recorder_config.default_timer_trigger

       
        
        cbMon = CBFactory.getCallback(
            acs_property,
            my_buffer,
            self.logger)

        # Activate the callback monitor
        cbMonServant = self.activateOffShoot(cbMon)
        # Create the real monitor registered with the component

        desc = ACS.acscommon_idl.CBDescIn(0, 0, 0)
        # CBDescIn(0, 0, 0)
        property_monitor = property.create_monitor(cbMonServant, desc)

        self.logger.logDebug("Time trigger to use for the monitor: " + 
                                  str(time_trigger_omg))

        # Note, here time should be OMG time!
        property_monitor.set_timer_trigger(time_trigger_omg)
        
        
        archive_delta = property_attributes.get("archive_delta")
        if PropertyTypeUtil.is_archive_delta_enabled(archive_delta):
            property_monitor.set_value_trigger(archive_delta, True)
        
        archive_delta_perc = property_attributes.get("archive_delta_percent")
        if PropertyTypeUtil.is_archive_delta_enabled(archive_delta_perc):
            property_monitor.set_value_percent_trigger(archive_delta_perc, True)

      
        return property_monitor
    
    def _get_acs_property(self, component, chars):
        """
        Allows to evaluate a characteristic by using the capabilities of the
        Python ACS clients (in this case the recorder), in order to check
        if it is a property or not

        Keyword arguments:
            component -- object
            chars     -- characteristic to be evaluated
        Returns:
            Property  -- The object or None if could not get it
        Raises:
            Exception -- If the property could not be evaluated
                         in the component
        """
        my_prop_str = 'component' + '._get_' + chars + '()'
        my_pro = None

        self.logger.debug("evaluating: " + my_prop_str)
        try:
            my_pro = eval(my_prop_str)
        except Exception:
            self.logger.logDebug(
                "it was not possible to get the property, jumping to next one")
        return my_pro
    #-------------------------------------------------------------------------
            
    def start_recording(self):
        """
        Sends signal to start recording data
        """

        self.logger.logInfo("starting monitoring")

        if(self._isRecording.isSet()):
            self.logger.logInfo("monitoring already started")
            return

        self._isRecording.set()

        # self.__scanForProps()#so it take immediate action when the method is
        # issued
        self.logger.logInfo("monitoring started")
    #-------------------------------------------------------------------------

    def stop_recording(self):
        """
        Sends signal to stop recording,
        releases all components, and destroys monitors
        """
        self.logger.logInfo("stopping recording")

        self.logger.logDebug("take lock")
        self._lock.acquire()
        try:
            self._isRecording.clear()
            # Here I remove references, I could pause them as well but provides
            # extra complications in bookkeeping
            self._release_all_comps()

        finally:
            self.logger.logDebug("release lock")
            self._lock.release()

    #-------------------------------------------------------------------------

    def is_recording(self):
        """
        Returns:
        True     -- if recording is started, otherwise False
        """
        self.logger.logDebug("called...")

        return self._isRecording.isSet()
    
    def _release_component(self, component_id):
        '''
        Removes a particular reference

        Keyword arguments:
        component_id     -- string with the component ID
        '''
        
        self.logger.logDebug("called...")

        # loop over the componentMap
        # for compName, compInfo in self.__componentsMap().iteritems():
        try:
            comp_info = self._componentsMap.pop(component_id)
        except KeyError:
            self.logger.logWarning(
                "component does not exist in the list, nothing to be done")
            return
        except AssertionError as b:
            self.logger.logWarning(
                "assertionError " + b, " exiting method")
            return
        if comp_info is None:
            self.logger.logDebug(
                "component does not exist, nothing to be done")
            return

        self.logger.logInfo("releasing component: " + component_id)

        self._remove_monitors(comp_info)

    #-------------------------------------------------------------------------

    def _remove_monitors(self, comp_info):
        '''
        Destroy all the monitors belonging to a component
        '''
        if comp_info.monitors is not None:
            for monitor in comp_info.monitors:
                try:
                    monitor.destroy()
                except Exception:
                    self.logger.logWarning(
                        "exception when deactivating the monitor: "
                        + str(monitor))

        # release the reference to the component
        # self.releaseComponent(componentId)
    #-------------------------------------------------------------------------
    def _release_all_comps(self):
        """
        Private method to release all references and to destroy all monitors
        """

        self.logger.logDebug("called...") 

        # loop over the componentMap
        # for compName, compInfo in self.__componentsMap().iteritems():
        for compName in self._componentsMap.keys():
            self.logger.logInfo("deactivating component: " + compName)

            self._release_component(compName)

        # now empty the dictionary / map
        self._componentsMap.clear()

            
            
class ComponentWhatchdog(threading.Thread):

        """
        Defining a thread to the check available components
        The thread is activated if the recorder is recording, and performs
        a periodic check (at a rate according to the configuration of the
        recorder) for lost components The thread is stopped if the recorder
        is not recording anymore

        Attributes:
            sleep_event -- event to govern the periodic execution of the thread
                           read from the configuration at __init__
            self.daemon -- Is the thread a daemon (default True)
        """

        def __init__(self, recorder_instance):
            '''
            recorder_instance -- An active instance of PropertyRecorder
            '''
            threading.Thread.__init__(self)
            self._recorder_instance = recorder_instance
            self.sleep_event = threading.Event()
            self.daemon = True

        def run(self):
            while True:
                if not self._recorder_instance._isRecording.isSet():
                    self._recorder_instance.logger.logDebug(
                        "waiting for recording to start...")
                self._recorder_instance._isRecording.wait()
                threading.Thread(target=self._run).start()
                self.sleep_event.clear()
                self.sleep_event.wait(
                    self._recorder_instance.recorder_config.checking_period)

        def _run(self):
            # First check if we lost any component
            self._recorder_instance._remove_wrong_components()
            # now look for new component
            self._recorder_instance._scan_for_components()

        def reset(self):
            self.sleep_event.clear()

        def stop(self):
            self._recorder_instance.logger.logDebug(
                        "stopping")
            self._Thread__stop
            # I needed to add this stop because, even if a daemon, the Python
            # component logger would show errors (showing up up periodically) 
            # because this thread did not finished. With this it worked well.
#----------------------------------------------------------------------

class ComponentStore(collections.MutableMapping):
    '''
    Adds observers in the map for the component
    reporting the total number of components and properties
    for every insertion or deletion.
    
    In all the other respects, behaves as a dict
    '''
   
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))
        self._observers = []

    def bind_to(self, callback):
            self._observers.append(callback)
    
    def unbind_to(self, callback):
            self._observers.remove(callback)
    
    def __getitem__(self, key):
        for callback in self._observers:
                callback(self.store)
        return self.store[self.store]

    def __setitem__(self, key, value):
        self.store[key] = value
        for callback in self._observers:
                callback(value)
    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)


class RecorderSpaceMonitor(object):
    '''
    Is an observer for the ComponentContainer to check if the
    recorder gets full 
    
    isFull -- If the recorder is full
    '''
   
    def __init__(self, component_store, max_component, max_properties):
        '''
        @param param: component_store - map with component information
        @type component_store: ComponentStore
        @param param: max_component
        @type long
        @param param: max_properties
        @type long
        '''
        self._max_component = max_component
        self._max_properties = max_properties
        self.component_store = component_store
        self.component_store.bind_to(self.update_component_entries)
        self.isFull = False
    
    def __del__(self):
        self.component_store.unbind_to(self.update_component_entries)

    def update_component_entries(self, components):
        '''
        @param components: Contains the reference to the objects and the monitors
        @type comp_info: dict{comp_name, ComponentInfo}
        '''
        n_monitors = 0
        for compInfo in self._componentsMap.values():
            n_monitors += len(compInfo.monitors)
        
        n_components = len(components) > self._max_component 

        if (self._max_component > n_components) or (self._max_properties > n_monitors):
            self.isFull = True
        else:
            self.isFull = False
