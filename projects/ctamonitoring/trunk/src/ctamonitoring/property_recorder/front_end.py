__version__ = "$Id$"
'''
Contains exceptions that could be raised by the front-end module

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''
import threading
import collections
from __builtin__ import str
from ctamonitoring.property_recorder.config import BACKEND_REGISTRIES
from ctamonitoring.property_recorder.config import PropertyAttributeHandler
from ctamonitoring.property_recorder.util import component_util
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder.callbacks import CBFactory
from ACS import CBDescIn  # @UnresolvedImport
from ctamonitoring.property_recorder.frontend_exceptions import UnsupporterPropertyTypeError,\
    ComponentNotFoundError, WrongComponentStateError, AcsIsDownError,\
    CannotAddComponentException
from CORBA import UNKNOWN, OBJECT_NOT_EXIST, OBJ_ADAPTER# @UnresolvedImport
from maciErrTypeImpl import CannotGetComponentExImpl

PROPERTY_TYPE = property_type.PropertyType

ComponentInfo = collections.namedtuple(
    'componentInfo',
    ['compReference',
     'managerId',
     'monitors'],
    verbose=False)
'''
compReference -- the CORBA reference to the component
managerId     -- ID as registered in the ACS manager
monitors      -- list with the monitor objects associated to the component
'''


class FrontEnd(object):
    '''
    The core class of the property recorder front-end
    Keeps a track of the existing components
    Takes care of opening buffers in the DB backends

    Monitors are created at a fixed rate and/or with a value change monitor.
    The fixed rate monitor is created according to the value of
    the CDB attribute "default_timer_trig". It is assumed that the
    default_timer_trig is in units of seconds. If default_timer_trig is
    missing then monitors are created at a configurable default rate,
    itself by default at 60 seconds. The monitor callbacks are defined
    at callbacks.py

    If the CDB or each component to be recorded contains the
    attributes archive_delta and/or
    archive_delta_percent, then the monitor will be triggered also by value
    changes according to these attributes (+ at the set fixed rate). If these
    attributes are not there, then the monitor will be only triggered with
    the rate fixed rate.

    The obtained references to components are non-sticky and therefore
    is not required to release them.

    Enum data string representation is passed to the backend as long as
    the corresponding description exists in the CDB, otherwise
    the integer representation is will be stored.

    Important Note: At least for C++, If the property does not have any
    value in the default_timer_trig attribute, then the default is
    set by the component itself to 10000000, equivalent to 1 second rate
    in this implementation. In addition, archive_suppress is set to
    "false". Therefore, properties without these two characteristics will
    be stored at 1Hz rate.

    '''

    def __init__(self, recorder_config, acs_client,
                 recorder_component_name=None):
        '''
        @param recorder_config: the setup parameters for the recorder
        @type recorder_config: ctamonitoring.property_recorder.RecorderConfig

        @param acs_client: the instance of the ACS client, or component where
                        the recorder is hosted, that provides access to
                        the ACS world
        @type acs_client: Acspy.Servants.ContainerServices.ContainerServices
        @param recorder_component_name: the name of the component hosting the
        @type recorder_component_name: str
        @ivar is_acs_client_ok: status of the ACS client
        @type is_acs_client_ok: bool
        '''

        self.name = recorder_component_name

        self.recoder_space = RecorderSpaceObserver(recorder_config.max_comps,
                                                   recorder_config.max_props)
        # dictionary to store the components with acquired references

        self._componentsMap = ComponentStore(value=None,
                                             observer=self.recoder_space)

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

        self._is_acs_client_ok = True

        self._canceled = False

    @property
    def is_acs_client_ok(self):
        return self._is_acs_client_ok

    @is_acs_client_ok.setter
    def is_acs_client_ok(self, components):
        raise NotImplementedError(
            "Cannot mutate, it is handled internally")

    def cancel(self):
        """
        Stops the check thread, releases the components and closes the registry

        The recorder will not be functional after calling this.
        """
        if not self._canceled:

            self.logger.logDebug("canceling...")

            self._component_whatchdog.stop()

            self._component_whatchdog = None

            # This step flushes all the data to the backend
            self._release_all_comps()

            # self._registry.close()

            self._registry = None

            self._canceled = True

            # TODO: check that cancellations are verified, i.e., check that
            # is not cancelled before start etc.

    def __del__(self):
        try:
            if not self._canceled:
                try:
                    self.cancel()
                except:
                    self.logger.logWarning("could not cancel")
        except:
            pass

    def update_acs_client(self, acs_client):
        if self.is_recording():
            self.start_recording()
            self.acs_client = acs_client
            self.start_recording()
        else:
            self.acs_client = acs_client
        self._is_acs_client_ok = True

    def _setup_backend(self):
        if self.recorder_config.backend_config is None:
            self._registry = BACKEND_REGISTRIES[
                self.recorder_config.backend_type]()
        else:
            self._registry = BACKEND_REGISTRIES[
                self.recorder_config.backend_type](
                    **self.recorder_config.backend_config)

    def _start_watchdog(self):
        # if it is an standalone recorder this will be created by the parent
        # class
        if self._component_whatchdog is None:
            self._component_whatchdog = self._create_component_whatchdog()
            self._component_whatchdog.start()

    def _create_component_whatchdog(self):
        return ComponentWatchdog(self)

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

            for compName, compInfo in self._componentsMap.items():

                comp_reference = compInfo.compReference

                self.logger.logDebug("checking component: " + compName)

                try:
                    component_util.is_component_state_ok(
                        comp_reference)
                except ComponentNotFoundError:
                    self.logger.logDebug(
                        "the component "
                        + compName
                        + " does not exists anymore")
                    self._componentsMap.pop(compName)
                except WrongComponentStateError:
                    self.logger.logDebug(
                        "the component "
                        + compName
                        + " is in a wrong state")
                    self._componentsMap.pop(compName)
                except Exception:
                    # TODO: next item should not raise an error but a log.
                    self.logger.exception(
                        "the component " + compName +
                        " is in a unexpected state, ")
                    self._componentsMap.pop(compName)
		else: 
		     if long(compInfo.managerId) != long(self.acs_client.availableComponents(compName)[0].h):
                     	self.logger.logDebug(
				"the component "
                        	+ compName
				+ " with Manager ID: "
				+ str(self.acs_client.availableComponents(compName)[0].h)
                        	+ " has a different ID from what it had before: "
				+ str(compInfo.managerId)
				+", taking it out")
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

        Raises:
            AcsIsDownError -- If the ACS client is reporting the problem
        """

        self.logger.logDebug("called...")

        if (self.recoder_space.isFull):
            self.logger.logWarning(
                "property recorder is full, "
                "will not accept more components/properties!")
            return

        try:
            activatedComponents = self.acs_client.findComponents(
                "*", "*", True)
        except Exception:
            self.logger.logWarning(
                "Cannot find activated components. Is ACS down?")
            self.logger.exception("")
            raise AcsIsDownError
            # This is a severe issue and all processes must be stopped

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
                self.logger.logDebug(
                    "Number of components was reduced, returning")
                return

            self.logger.logDebug(
                "inspecting component n. "
                + str(count_comp) + ": " + str(component_id))

            # If working in INCLUDE mode and it is in the include list, add it
            if self.recorder_config.is_include_mode:
                if component_id in self.recorder_config.components:
                    try:
                        self.process_component(component_id)
                    except CannotAddComponentException:
                        self.logger.exception("")
                else:
                    self.logger.logDebug(
                        'The component '
                        + str(component_id)
                        + ' is not in the include list, skipping')

            # If working in EXCLUDE mode and it is NOT in the list, add it
            if not self.recorder_config.is_include_mode:
                if component_id not in self.recorder_config.components:
                    try:
                        self.process_component(component_id)
                    except CannotAddComponentException:
                        self.logger.exception("")
                else:
                    self.logger.logDebug(
                        'The component ' +
                        str(component_id) +
                        ' is in the exclude list, skipping')

        self.logger.logDebug("done...")

    def process_component(self, component_id):
        """
        Try to insert a component in the recorder
        If it is not yet inserted, and it is OK insert it.
        The component will be inserted regardless if it is in the
        exclude/include list.

        @param component_id: the name of the component to insert
        @type component_id: str

        @raise CannotAddComponentException: if the component cannot be
        added by unexpected reasons
        """

        self.logger.logDebug("called...")

        self.logger.logDebug("take lock")
        self.__lock.acquire()

        try:

            if self._can_be_added(component_id):
                    # get no sticky so we do not
                    # prevent them of being deactivated
                component = self.acs_client.getComponentNonSticky(
                    component_id)
                if(component_util.is_a_property_recorder_component(component)):
                    self.logger.logDebug("skipping other property recorders")
                    return
	 	
	
		manager_id = self.acs_client.availableComponents(component_id)[0].h
		
                comp_info = ComponentInfo(
                    component,
		    manager_id,
                    self._get_component_characteristics(component)
                    )

		self._componentsMap[component_id] = comp_info

                self.logger.logDebug(
                    "Component " + component_id + " was added")

            else:
                self.logger.logDebug(
                    "Component " + component_id + " cannot be added")

        except CannotGetComponentExImpl:
            raise CannotAddComponentException(component_id)

        except Exception:
            raise CannotAddComponentException(component_id)

        finally:
            self.logger.logDebug("release lock")
            self.__lock.release()

    def _can_be_added(self, component_id):
        """
        Checks if the component can be stored

        @param component_id: the name of the component to check
        @type component_id: str

        @return: True if can be stored, False if not
        @rtype: bool

        returns True if can be stored, False if not
        """

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

        @param component_reference: CORBA reference of the component
        @type component_reference: CORBA reference
        @return list with all the monitors created
        @rtype: list
        """

        # TODO Can raise exception, document it

        component = component_reference
        monitor_list = []

        if not component_util.is_characteristic_component(component):
            self.logger.logDebug("Component is not characteristic")
            return monitor_list

        try:
            is_python = component_util.is_python_char_component(component)
            if is_python: 
	       self.logger.logDebug(
                'Python component found')
        except AttributeError:
            return monitor_list

        '''
        Explanation of what is done bellow:

        We check if the component is Python or not. This must be done because
        Python characteristic components have to be handled differently
        (I suspect that this is missing implementation and not intentional),
        as the attributes from the component and properties from the CDB are
        not accessible from the component/property objects. To get access to
        these, one needs to use the cdb access and the XML objectifier,
        seePropertyAttributeHandler.get_prop_attribs_cdb_xml
        This would work for any property type and implementation language,
        but creates a clearly worse performance and therefore is only used for
        Python
        '''

        if is_python:
            self.logger.logDebug(
                'probably is a property, trying to get the information '
                'for the archive')
            obj_chars = component_util.get_objectified_cdb(component)
            for obj_char in obj_chars:
                try:
                    acs_property = self._get_property_object(
                        component, obj_char.nodeName)
                except (AttributeError, ValueError):
                    continue

                property_attributes = (
                    PropertyAttributeHandler.get_prop_attribs_cdb_xml(
                        obj_char))
                try:
                    property_monitor = self._get_property_monitor(
                        acs_property,
                        property_attributes,
                        component_reference)
                except (UnsupporterPropertyTypeError, OBJECT_NOT_EXIST):
                    self.logger.exception("")
                    property_monitor = None
                if property_monitor is not None:
                    monitor_list.append(property_monitor)

        else:
            chars = component.find_characteristic("*")
            for count in range(0, len(chars)):
                try:
                    myCharList = component_reference.get_characteristic_by_name(
                        str(chars[count])).value().split(',')
                except OBJ_ADAPTER:
                    self.logger.exception("problem getting characterisic")
                    continue
                """
                As a way of discerning from a property to other type of
                characteristic, I check for the length of the char list.
                If it is longer than 5, then is probably a property
                """
                if (len(myCharList) > 5):
                    self.logger.logDebug(
                        'probably is a property, trying to get the '
                        'information for the archive')

                    # Check if the characteristic is a property
                    try:
                        acs_property = self._get_property_object(
                            component,
                            chars[count])
                    except (AttributeError, ValueError):
                        continue

                    property_attributes = (
                        PropertyAttributeHandler.get_prop_attribs_cdb(
                            acs_property)
                        )
                    try:
                        property_monitor = self._get_property_monitor(
                            acs_property,
                            property_attributes,
                            component_reference)
                        monitor_list.append(property_monitor)
                    except UnsupporterPropertyTypeError:
                        self.logger.exception(
                            "Property type not supported")

        return monitor_list

    def _get_property_object(self, component, property_name):
        '''
        @raises AttributeError: if the property could not be obtained
        due to a wrong property name
        @raises ValueError: if the property could be obtained, but is
        of none value
        @return: the ACS property object
        '''
        acs_property = self._get_acs_property(
            component, property_name)
        #  This can raise an AttributeError

        if acs_property is None:
            raise ValueError

        if not component_util.is_property_ok(acs_property):
            raise ValueError

        return acs_property

    def _get_property_monitor(
            self,
            acs_property,
            property_attributes,
            component_reference):
        '''
        @return: the monitor of the property
        @raise UnsupporterPropertyTypeError:
        if the property type is not supported
        @raise OBJECT_NOT_EXIST: if the property object does not exist
        '''
        #  This can raise a UnsupporterPropertyTypeError
        my_buffer = self._create_buffer(
            acs_property,
            property_attributes,
            component_reference
            )

        #  This can raise a UnsupporterPropertyTypeError
        property_monitor = self._create_monitor(
            acs_property,
            property_attributes,
            my_buffer)

        return property_monitor

    def _create_buffer(
            self, acs_property,
            property_attributes,
            component_reference):
        '''
        Creates a buffer in the backend and returns it

        @param acs_property: the ACS property
        @type acs_property: ACS._objref_<prop_type>
        @raise UnsupporterPropertyTypeError: if property type is not supported
        @raise OBJECT_NOT_EXIST: if the property object does not exist
        '''

        component_name = component_reference._get_name()
        component_type = component_reference._NP_RepositoryId

        #  This raises UnsupporterPropertyTypeError
        my_prop_type = component_util.get_property_type(
            acs_property._NP_RepositoryId)

        # TODO: Think in what to do with the enum states
        enumStates = None

        if (my_prop_type is None) or (my_prop_type is PROPERTY_TYPE.OBJECT):
                    my_prop_type = PROPERTY_TYPE.OBJECT
                    try:
                        enumStates = component_util.get_enum_prop_dict(
                            acs_property)
                        self.logger.logDebug(
                            "Enum States found: "+str(enumStates))
                    except AttributeError:
                        self.logger.logDebug(
                            "Enum states cannot be read,"
                            " use the int representation")
                    except ValueError:
                        self.logger.logDebug(
                            "Enum states do not make sense,"
                            "use the int representation")

	# FIXME: There is some sort of bug below in the backend: if MondoBD is off, it hangs
        try:
            my_buffer = self._registry.register(
                component_name=component_name,
                component_type=component_type,
                property_name=acs_property._get_name(),
                property_type=my_prop_type,
                property_type_desc=enumStates,
                **property_attributes)
        except UserWarning:
            self.logger.logWarning(
                "Warning of buffer being used received, forcing in")
            my_buffer = self._registry.register(
                component_name=component_name,
                component_type=component_type,
                property_name=acs_property._get_name(),
                property_type=my_prop_type,
                property_type_desc=enumStates,
                disable=False,
                force=True,
                **property_attributes)
	except ValueError:
	    self.logger.logWarning("++bla++")
	    self.logger.exception("")   
		
		


        self.logger.logDebug(
            "Create property with attributes: " +
            str(property_attributes)
            )

        return my_buffer

    def _create_monitor(self, acs_property, property_attributes, my_buffer):
        '''

        Raises -- UnsupporterPropertyTypeError If the property type
                  is not supported for monitors
        '''

        try:
            time_trigger_omg = long(10000000 * property_attributes.get(
                "default_timer_trig"))

        except Exception:
            self.logger.logDebug(
                "no time trigger found in the CDB, "
                "using the default value")
            time_trigger_omg = long(
                10000000 * self.recorder_config.default_timer_trigger)

        # This can rise a UnsupporterPropertyTypeError
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

        self.logger.logDebug(
            "Time trigger to use for the monitor: "
            + str(time_trigger_omg))

        # Note, here time should be OMG time
        property_monitor.set_timer_trigger(time_trigger_omg)

        archive_delta = property_attributes.get("archive_delta")
        if component_util.is_archive_delta_enabled(archive_delta):
            property_monitor.set_value_trigger(archive_delta, True)

        archive_delta_perc = property_attributes.get("archive_delta_percent")
        #TODO: Is this a bug? Asks for archive delta_perc but check archive_delta
        if component_util.is_archive_delta_enabled(archive_delta_perc):
            property_monitor.set_value_percent_trigger(
                archive_delta_perc, True)

        return property_monitor

    def _get_acs_property(self, component, chars):
        """
        Allows to evaluate a characteristic by using the capabilities of the
        Python ACS clients (in this case the recorder), in order to check
        if it is a property or not

        @param component: ACS characteristic component object
        @type component: Acspy.Servants.CharacteristicComponent.CharacteristicComponent
        @param chars: characteristic to be evaluated
        @type chars: str
        @return: The property object
        @raise AttributeError:
        If the property could not be evaluated in the component
        @raise ValueError: if the property value/state is not OK

        """
        my_prop_str = '_get_' + chars

        self.logger.debug(
            "evaluating: "
            + str(component)
            + '._get_' + chars + '()')
        try: 
            my_pro_attr = getattr(component, my_prop_str)  # this raises an UNKNOWN
            my_pro = my_pro_attr()  # this raises an attribute error
        except UNKNOWN:
            raise ValueError

        return my_pro

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

    def _remove_monitors(self, comp_info):
        '''
        Destroy all the monitors belonging to a component
        '''
        if comp_info.monitors is not None:
            for monitor in comp_info.monitors:
                try:
                    monitor.destroy()
                except Exception:
                    # TODO: use better the logger for the exception
                    self.logger.exception(
                        "exception when deactivating a monitor for: "
                        + str(comp_info.compReference._get_name()))

    def _release_all_comps(self):
        """
        Private method to release all references and to destroy all monitors
        """

        self.logger.logDebug("called...")

        # loop over the componentMap
        # for compName, compInfo in self.__componentsMap().iteritems():
        for compName in self._componentsMap.keys():
            self.logger.logDebug("deactivating component: " + compName)
            try:
                self._release_component(compName)
            except OBJECT_NOT_EXIST:
                self.logger.logDebug(
                    "component: "
                    + compName
                    + " does not exist")

        # now empty the dictionary / map
        self._componentsMap.clear()


class ComponentWatchdog(threading.Thread):

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
            try:
                self._recorder_instance._scan_for_components()
            except AcsIsDownError:
                self._recorder_instance._is_acs_client_ok = False
                # ACS is down, the client must be notified

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

    def __init__(self, value=None, observer=None):
        if value is None:
            value = {}
        dict.__init__(self, value)
        if observer is not None:
            self.set_observer(observer)
            self.observer.dict_init(self)

    def set_observer(self, observer):
        """
        All changes to this dictionary will trigger calls to observer methods
        """
        self.observer = observer

    def __setitem__(self, key, value):
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

    def __delitem__(self, key):
        oldvalue = dict.__getitem__(self, key)
        dict.__delitem__(self, key)
        self.observer.dict_del(key, oldvalue)

    def clear(self):
        oldvalue = self.copy()
        dict.clear(self)
        self.observer.dict_clear(self, oldvalue)

    def update(self, update_dict):
        replaced_key_values = []
        new_key_values = []
        for key, item in update_dict.items():
            if key in self:
                replaced_key_values.append((key, item, self[key]))
            else:
                new_key_values.append((key, item))
        dict.update(self, update_dict)
        self.observer.dict_update(new_key_values, replaced_key_values)

    def setdefault(self, key, value=None):
        if key not in self:
            dict.setdefault(self, key, value)
            self.observer.dict_setdefault(self, key, value)
            return value
        else:
            return self[key]

    def pop(self, k, x=None):
        if k in self:
            value = self[k]
            dict.pop(self, k, x)
            self.observer.dict_pop(k, value)
            return value
        else:
            return x

    def popitem(self):
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

        @Note: I keep here the components, oldvalue because I have an
        idea that this could be used for something else: when stopping
        the recorder. Will come back here
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
        if ((self._max_properties < self._actual_properties)
                or (self._max_components < self._actual_components)):
            self.isFull = True
        else:
            self.isFull = False

    def _evaluate_component_entries(self, components):
        '''
        @param components: Contains the reference to the objects and monitors
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

        @param oldvalue: Contains the reference to the old object and monitors
        @type oldvalue: ComponentInfo
        '''
        prev_monitors = 0

        if oldvalue is None:
            self._actual_components += 1
        else:
            prev_monitors += len(oldvalue.monitors)

        self._actual_properties = (
            self._actual_properties
            + len(value.monitors)
            - prev_monitors)

        self.check_if_full()

    def _remove_component_entry(self, key, oldvalue):
        '''
        @param key: Contains the name to the removed component
        @type key: str

        @param oldvalue: Contains the reference to the old object and monitors
        @type oldvalue: ComponentInfo
        '''

        prev_monitors = len(oldvalue.monitors)

        self._actual_properties -= prev_monitors

        self._actual_components -= 1

        self.check_if_full()
