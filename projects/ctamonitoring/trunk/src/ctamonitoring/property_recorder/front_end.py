import threading
import collections
from __builtin__ import str
from ctamonitoring.property_recorder.config import backend_registries
from ctamonitoring.property_recorder.config import PropertyAttributeHandler
from ctamonitoring.property_recorder.util import  PropertyTypeUtil
from ctamonitoring.property_recorder.util import ComponentUtil
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder.callbacks import CBFactory
from ACS import CBDescIn  # @UnresolvedImport
from ctamonitoring.property_recorder.frontend_exceptions import UnsupporterPropertyTypeError,\
    ComponenNotFoundError, WrongComponenStateError

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



class FrontEnd(object):
    '''
    The core class of the property recorder front-end
    Keeps a track of the existing components
    Takes care of opening buffers in the DB backends
    
    Requires to have ACS up and running to run
    '''
    
    def __init__(self, recorder_config, acs_client, recorder_component_name = None):
        '''
        recorder_config -- the setup parameters for the recorder
        acs_client      -- the instance of the ACS client, or component where the 
                           recorder is hosted, that provides access to the ACS world
        '''
        
        self.name = recorder_component_name
        
        self.recoder_space = RecorderSpaceObserver(recorder_config.max_comps,  
                                                    recorder_config.max_props)
        # dictionary to store the components with acquired references
        
        self._componentsMap = ComponentStore(value = None, 
                                            observer = self.recoder_space)

        self._isRecording = threading.Event()

        # get threading lock to make some methods synchronized
        self.__lock = threading.RLock()

        self._component_whatchdog = None
        
        self.recorder_config = recorder_config
        
        self.logger = acs_client.getLogger()
        
        self.acs_client = acs_client
        
        self._registry = None
        
        self._setup_backend()
        
        self._start_watchdog()
        
        self._canceled = False 

    def cancel(self):
        """
        Stops the check thread, releases the components and closes the registry
        """
        if not self._canceled:
        
            self.logger.logDebug("canceling...")
            
            #self._component_whatchdog.reset()
            
            self._component_whatchdog.stop()
            
            self._component_whatchdog = None
    
            #This step flushes all the data to the backend
            self._release_all_comps()
                    
            #self._registry.close()
                    
            self._registry = None;
            
            self._canceled = True
            
            #TODO: check that cancellations are verified, i.e., check that is not cancelled before start etc.
    
    def __del__(self):
        try:
            if not self._canceled:
                try:
                    self.cancel()
                except:
                    self.logger.logWarning("could not cancel")
        except:
            pass    
    
    def _setup_backend(self):
        if self.recorder_config.backend_config is None:
            self._registry = backend_registries[self.recorder_config.backend_type]()   
        else :
            self._registry = backend_registries[self.recorder_config.backend_type](**self.recorder_config.backend_config)   
        
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
        self.__lock.acquire()
        try:
            length = len(self._componentsMap)

            for compName, compInfo in self._componentsMap.items() :

                comp_reference = compInfo.compReference
                
                self.logger.logDebug("checking component: " + compName)
                
                try: 
                    ComponentUtil.is_component_state_ok(comp_reference, compName)
                except ComponenNotFoundError:
                    self.logger.logDebug(
                                         "the component " 
                                         + compName 
                                         + " does not exists anymore")
                    self._componentsMap.pop(compName)
                except WrongComponenStateError:
                    self.logger.logDebug(
                                         "the component " 
                                         + compName 
                                         + " is in a wrong state")
                    self._componentsMap.pop(compName)    
                except Exception:
                    #TODO: next item should not raise an error but a low level log. See how to do that
                    self.logger.exception(
                                        "the component " + compName + 
                                        " is in a unexpected state, ")
                    
                    self._componentsMap.pop(compName)

            length -= len(self._componentsMap)

            if length > 0:
                self.logger.logDebug(
                    "%d component(s) removed from the records" %
                    (length,))
            else:
                self.logger.logDebug(
                    "no component was removed from the records")

            self.logger.logDebug("release lock")
        finally:
            self.__lock.release()   
            
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
        activatedComponents = self.acs_client.findComponents("*", "*", True)

        n_components = len(activatedComponents)

        if n_components is 0:
            self.logger.logDebug("No components active")
            return
        
        self.logger.logDebug('found ' + str(n_components) + ' components')

        # Check the availableComponent, only those which are already activated
        for count_comp in range(0, n_components):
            try:
                component_id = activatedComponents[count_comp]
            except IndexError:
                self.logger.logDebug("Number of components was reduced, returning")
                return
            
            self.logger.logDebug(
                "inspecting component n. " + str(count_comp) + ": " + str(component_id))

            #If working in INCLUDE mode and it is in the include list, add it
            if self.recorder_config.is_include_mode:
                if component_id in self.recorder_config.components:
                    self.process_component(component_id)
                else:
                    self.logger.logDebug('The component ' +
                        str(component_id) +
                        ' is not in the include list, skipping')
            
            #If working in EXCLUDE mode and it is NOT in the EXCLUDE list, add it
            if not self.recorder_config.is_include_mode:
                if not component_id in self.recorder_config.components:
                    self.process_component(component_id)
                else:
                    self.logger.logDebug('The component ' +
                        str(component_id) +
                        ' is in the exclude list, skipping')
            
        self.logger.logDebug("done...")
        
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
                    component = self.acs_client.getComponentNonSticky(component_id)
                except Exception:
                    self.logger.exception("could not get a reference to the component "+ 
                                        str(component_id))
                                        
                    return
        
                # skip other property recorders
                if(ComponentUtil.is_a_property_recorder_component(component)):
                    self.logger.logDebug("skipping other property recorders")
                    return
                
                comp_info = ComponentInfo(component, self._get_component_characteristics(component))

                self._componentsMap[component_id] = comp_info
                
                self.logger.logDebug("Component " +component_id 
                                  + " was added")
                              
                result = True
            
            else:
                self.logger.logDebug("Component " +component_id 
                                  + " cannot be added")
                return 
         
        except Exception:
                    self.logger.exception(str(component_id) +
                        " could not be added ")
                
        finally:
            self.logger.logDebug("release lock")
            self.__lock.release()
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
         
        if(component_id == self.name):
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
        
        component = component_reference
        monitor_list = []

        if not ComponentUtil.is_characteristic_component(component):
            self.logger.logDebug("Component is not characteristic")
            return monitor_list

        
        chars = component.find_characteristic("*")
        
        for count in range(0, len(chars)):
            myCharList = component_reference.get_characteristic_by_name(
                str(chars[count])).value().split(',')
            # As a way of discerning from a property to other type of
            # characteristic, I check for the length of the char list. If it is
            # longer than 5, then is probably a property
            if (len(myCharList) > 5):
                self.logger.logDebug(
                    'probably is a property, trying to get the information ' 
                    'for the archive')

                # Check if the characteristic is a property

                try:
                    acs_property = self._get_acs_property(component,
                                                    chars[count])
                except AttributeError:
                    continue
                
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
                    my_buffer = self._create_buffer(acs_property, 
                                    property_attributes, 
                                    component_reference)
                except Exception:
                    self.logger.exception(
                        "The buffer could not be created")
                    continue
                
  
                try: 
                    property_monitor = self._create_monitor(
                                            acs_property, 
                                            property_attributes, 
                                            my_buffer)
                
                except UnsupporterPropertyTypeError:
                    self.logger.exception("")
                    property_monitor = None
              
                if property_monitor is not None:
                    monitor_list.append(property_monitor)

        return monitor_list   
      
    
       
            
    def _create_buffer(self, acs_property, property_attributes, component_reference):
        '''
        Creates a buffer in the backend and returns it
   
        @param acs_property: the ACS property
        @type acs_property: ACS._objref_<prop_type>
        
        
        
        Raises:
        TypeError -- If the property type is not supported
        Exception  -- If any other problem happened when creating the buffers  
        '''
        my_prop_type = None
     
        component_name = component_reference._get_name()
        component_type = component_reference._NP_RepositoryId               
        
        try:
            my_prop_type = PropertyTypeUtil.get_property_type(
                acs_property._NP_RepositoryId)
        except Exception, e:
            self.logger.logWarning(
                "Property type not supported, skipping")
            raise TypeError(e)
        
        
        #TODO: Think in what to do with the enum states
        enumStates = None
          
        if (my_prop_type is None) or (my_prop_type is PropertyType.OBJECT):
                    my_prop_type = PropertyType.OBJECT 
                    try:
                        enumStates = PropertyTypeUtil.get_enum_prop_dict(acs_property)
                        self.logger.logDebug("Enum States found: "+str(enumStates))                        
                    except AttributeError:
                        self.logger.logDebug(
                            "Enum states cannot be read, use the int representation")
                    except ValueError:
                        self.logger.logDebug(
                            "Enum states do not make sense, use the int representation")
                    except Exception:
                        self.logger.exception("")

        try:         
            
            my_buffer = self._registry.register(component_name = component_name,
                               component_type = component_type,
                               property_name = acs_property._get_name(),
                               property_type = my_prop_type,
                               property_type_desc = enumStates, 
                               **property_attributes) 
        
        except UserWarning: 
            self.logger.logWarning(
                "Warning of buffer being used received, forcing in")
            my_buffer = self._registry.register(component_name = component_name,
                                component_type = component_type,
                                property_name = acs_property._get_name(),
                                property_type = my_prop_type,
                                property_type_desc = enumStates, 
                                disable = False, 
                                force = True,
                                **property_attributes) 
            
        self.logger.logDebug(
                "Create property with attributes: "+
                str(property_attributes)
                )
        
        return my_buffer
        
        
    def _create_monitor(self, acs_property, property_attributes, my_buffer):
        '''
        
        Raises -- UnsupporterPropertyTypeError If the property type is not supported
                  for monitors
        '''
    
        try:
            time_trigger_omg = long(10000000 * my_buffer.get("default_timer_trig"))
           
        except Exception:
            self.logger.logDebug("no time trigger found in the CDB, "
                                  "using the default value")
            time_trigger_omg = long(10000000 * self.recorder_config.default_timer_trigger)

       
        #This can rise a UnsupporterPropertyTypeError
        cbMon = CBFactory.get_callback(
            acs_property,
            acs_property._get_name(),
            my_buffer,
            self.logger
            )

        # Activate the callback monitor
        cbMonServant = self.acs_client.activateOffShoot(cbMon)
        # Create the real monitor registered with the component

        desc = CBDescIn(0, 0, 0)
        # CBDescIn(0, 0, 0)
        property_monitor = acs_property.create_monitor(cbMonServant, desc)

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
            component -- acs characteristic component object
            chars     -- characteristic to be evaluated
        Returns:
            Property  -- The property object
        Raises:
            AttributeError -- If the property could not be evaluated
                              in the component
        """
        #my_prop_str = 'component' + '._get_' + chars + '()'
        my_prop_str = '_get_' + chars
       
        #my_pro = None

        self.logger.debug("evaluating: " + 
                        str(component) + 
                        '._get_' + chars + '()')
        try:
            #my_pro = eval(my_prop_str)
            my_pro_attr = getattr(component, my_prop_str)
            my_pro = my_pro_attr()
        except AttributeError as e: 
            self.logger.logDebug(
                "it was not possible to get the property, jumping to next one")
            self.logger.exception("")
            raise AttributeError(e)
        #except Exception:
        #    self.logger.logDebug(
        #        "it was not possible to get the property, jumping to next one")
        #    self.logger.exception("")
        #    return None
        return my_pro
    #-------------------------------------------------------------------------
            
    def start_recording(self):
        """
        Sends signal to start recording data
        """

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
        self.__lock.acquire()
        try:
            self._isRecording.clear()
            # Here I remove references, I could pause them as well but provides
            # extra complications in bookkeeping
            self._release_all_comps()
        finally:
            self.__lock.release()

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

        self.logger.logDebug("releasing component: " + component_id)

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
                    self.logger.exception("exception when deactivating a monitor for: "
                        + str(comp_info.compReference._get_name()))
                    

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
            self.logger.logDebug("deactivating component: " + compName)

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
            self.sleep_event.clear()
            # I needed to add this stop because, even if a daemon, the Python
            # component logger would show errors (showing up up periodically) 
            # because this thread did not finished. With this it worked well.
#----------------------------------------------------------------------

class ComponentStore(dict):
    '''
    Adds one observer to the map for the component
    reporting the total number of components and properties
    for every insertion or deletion.
    
    In all the other respects, behaves as a dict
    
    Note: I did not found any need to have more that one observer 
    at the moment, so only one observer can be added at the time
    
    Based on a solution found at:
    http://code.activestate.com/recipes/306864-list-and-dictionary-observer/
    
    '''
   
   
    def __init__ (self, value = None, observer = None):
        if value is None:
            value = {}
        dict.__init__(self, value)
        if observer is not None:
            self.set_observer(observer)
            self.observer.dict_init(self)
    
    def set_observer (self, observer):
        """
        All changes to this dictionary will trigger calls to observer methods
        """
        self.observer = observer 
    
    def __setitem__ (self, key, value):
        """
        Intercept the l[key]=value operations.
        Also covers slice assignment.
        """
        try:
            oldvalue = self.__getitem__(key)
        except KeyError:
            dict.__setitem__(self, key, value)
            self.observer.dict_create(key, value)
        else:
            dict.__setitem__(self, key, value)
            self.observer.dict_set(key, value, oldvalue)
    
    def __delitem__ (self, key):
        oldvalue = dict.__getitem__(self, key)
        dict.__delitem__(self, key)
        self.observer.dict_del(key, oldvalue)
    
    def clear (self):
        oldvalue = self.copy()
        dict.clear(self)
        self.observer.dict_clear(self, oldvalue)
    
    def update (self, update_dict):
        replaced_key_values =[]
        new_key_values =[]
        for key, item in update_dict.items():
            if key in self:
                replaced_key_values.append((key, item, self[key]))
            else:
                new_key_values.append((key, item)) 
        dict.update(self, update_dict)
        self.observer.dict_update(new_key_values, replaced_key_values)
    
    def setdefault (self, key, value=None):
        if key not in self:
            dict.setdefault(self, key, value)
            self.observer.dict_setdefault(self, key, value)
            return value
        else:
            return self[key]
    
    def pop (self, k, x=None):
        if k in self:
            value = self[k]
            dict.pop(self, k, x)
            self.observer.dict_pop(k, value)
            return value
        else:
            return x
    
    def popitem (self):
        key, value = dict.popitem(self)
        self.observer.dict_popitem(key, value)
        return key, value 




class RecorderSpaceObserver(object):
    '''
    Is an observer for the ComponentContainer to check if the
    recorder gets full 
    
    isFull -- If the recorder is full
    '''
   
    def __init__(self, max_components, max_properties):
        '''
        @param param: component_store - map with component information
        @type component_store: ComponentStore
        @param param: max_components
        @type long
        @param param: max_properties
        @type long
        '''
        self._max_components = max_components
        self._max_properties = max_properties
        self._actual_components = 0
        self._actual_properties = 0
        
        self.isFull = False
    
    def dict_init(self, components):
        '''
        Called when a new dictionary is created with content on it
        
        components is a dict
        with compName, compInfo
        '''
        self._evaluate_component_entries(components)
        
    def dict_create(self, key, value):
        '''
        Called when one entry is added
        
        value is a compInfo
        
        key is the name of the components new entry created
        '''
        self._update_component_entry(key, value)
    
    def dict_set(self, key, value, oldvalue):
        '''
        Called when an entry is replaced
        
        key is the name of the updated entry 
        
        value is the current value 
        
        oldvalue is the previous value it had
        '''
        self._update_component_entry(key, value, oldvalue)


    def dict_del(self, key, oldvalue): 
        '''
        Called when an item is deleted
        
        key is the name of the deleted entry 
        
        old value is the  value that it had
        '''
        self._remove_component_entry(key, oldvalue)

    def dict_clear(self, components, oldvalue):
        '''
        Called when the dict is emptied
        
        components is a dict with all the stored values
        with compName, compInfo, should be empty
                
        old value is the just deleted component dictionary that it had
        
        @Note: I keep here the components, oldvalue because I have an Idea that this could 
        Be used for something else: when stopping the recorder. Will come back here
        '''
        
        self._actual_components = 0
        self._actual_properties = 0
        
        self.isFull = False
    
    
    def dict_update(self, new_key_values, replaced_key_value):
        '''
       
        new_keys are the new (keys, values) that have been added 
        
        replaced_key_values are those (key, value, oldvalue) that were replaced
        '''
       
        for (key, value) in new_key_values:
            self._update_component_entry(key, value)
       
        for (key, value, oldvalue) in replaced_key_value:
            self._update_component_entry(key, value, oldvalue)
        

    def dict_setdefault(self, components, key, value):
        '''
        components is a dict with all the stored values
        with compName, compInfo, should be empty
                
        key is the component that will get a default
        
        value is the associated value
        '''
        raise NotImplementedError

    def dict_pop(self, key, value):
        '''
        components is a dict with all the stored values
        with compName, compInfo, should be empty
                
        key is the component name popped out
        
        value is the associated value of that component
        '''
        self._remove_component_entry(key, value)
        
        
    def dict_popitem(self, key, value):
        '''
        components is a dict with all the stored values
        with compName, compInfo, should be empty
                
        k is the component name popped out
        
        value is the associated value of that component
        '''
        self._remove_component_entry(key, value)

    def check_if_full(self):
        if (self._max_properties < self._actual_properties) or (self._max_components < self._actual_components):
            self.isFull = True
        else:
            self.isFull = False

    def _evaluate_component_entries(self, components):
        '''
        @param components: Contains the reference to the objects and the monitors
        @type components: dict{comp_name, ComponentInfo}
        '''
        
        self._actual_components = len(components) 
        
        n_monitors = 0
        for compInfo in components.values():
            n_monitors += len(compInfo.monitors)
                
        self._actual_properties = n_monitors
        
        self.check_if_full()
    
    def _update_component_entry(self, key, value, oldvalue=None):
        '''
        @param key: Contains the name to the updated component
        @type key: str
         
        @param value: Contains the reference to the new object and its monitors
        @type value: ComponentInfo
        
        @param oldvalue: Contains the reference to the old object and its monitors
        @type oldvalue: ComponentInfo
        '''
        prev_monitors = 0
        
        if oldvalue is None:
            self._actual_components += 1
        else:
            prev_monitors += len(oldvalue.monitors)
        
        
        self._actual_properties = self._actual_properties + len(value.monitors) - prev_monitors
        
        self.check_if_full()
    
    def _remove_component_entry(self, key, oldvalue):
        '''
        @param key: Contains the name to the removed component
        @type key: str
       
        @param oldvalue: Contains the reference to the old object and its monitors
        @type oldvalue: ComponentInfo
        '''
        
        
        prev_monitors = len(oldvalue.monitors)
        
        self._actual_properties -= prev_monitors
        
        self._actual_components -= 1
        
        self.check_if_full()
        