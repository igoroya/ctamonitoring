#--CORBA STUBS-----------------------------------------------------------------
import actl__POA
import actl
import ACS
import ACS__POA
# Module Imports
from ctamonitoring.property_recorder.callbacks import CBFactory
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.util import PropertyTypeUtil
from ctamonitoring.property_recorder.util import DecodeUtil
from ctamonitoring.property_recorder.backend import dummy
from ctamonitoring.property_recorder.backend import log
from ctamonitoring.property_recorder.backend import mongodb
#from ctamonitoring.property_recorder.backend import sqlal
from ctamonitoring.property_recorder.backend import get_registry_class 
#from ctamonitoring.property_recorder.backend.log import registry
#from ctamonitoring.property_recorder.backend.mongodb import registry
#from ctamonitoring.property_recorder.backend.sqlal import registry
from ctamonitoring.property_recorder.backend.property_type import PropertyType
#--ACS Imports-----------------------------------------------------------------
from Acspy.Servants.CharacteristicComponent import CharacteristicComponent
from Acspy.Servants.ContainerServices import ContainerServices
from Acspy.Servants.ComponentLifecycle import ComponentLifecycle
from CORBA import TRUE, FALSE
# these are necessary for python components reading
from Acspy.Common import CDBAccess
from Acspy.Util import XmlObjectifier  # as before
import ACSErrTypeCommonImpl
import cdbErrType
from xml.parsers.expat import ExpatError
# Other Imports
import collections
import threading
import time
import ast
import datetime
#------------------------------------------------------------------------------
# Add something like enums to Python (Better ideas are welcome)


def enum(**enums):
    return type('Enum', (), enums)

# TODO: add mySQL when it is ready
STORAGE_TYPE = enum(
    DUMMY=get_registry_class("dummy"),
    LOG=get_registry_class("log") ,
    MYSQL=None,
    MONGODB=get_registry_class("mongodb"))  # this acts as an enum
BackendMap = {}
BackendMap["DUMMY"] = STORAGE_TYPE.DUMMY
BackendMap["LOG"] = STORAGE_TYPE.LOG
BackendMap["MYSQL"] = STORAGE_TYPE.MYSQL
BackendMap["MONGODB"] = STORAGE_TYPE.MONGODB


class recorder(actl__POA.PropertyRecorder,
               CharacteristicComponent,
               ContainerServices,
               ComponentLifecycle):

    """
    Implementation of the PropertyRecorder interface

    It provides two flavors, one working as an stand-alone tool for small
    setups, and the other better suited for large setups when several
    PropertyRecorder instances will be created by the Property Recorder
    Distributer (see: distributer.py).

    The stand-alone version can be initiated via creating an instance
    of standalone.py,
    while for the scalable version via the constructor of this class

    Monitors are created at a fixed rate and or with a value change monitor.
    The fixed rate monitor is created according to the value of
    the CDB attribute "default_timer_trig". It is assumed that the
    default_timer_trig is in units of seconds. If default_timer_trig is
    missing then monitors are created at a configurable default rate,
    itself by default at 60 seconds. The monitor callbacks are defined
    at callbacks.py

    If the CDB contains the attributes archive_delta and/or
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

    TODO: Understand the warning "not an offshoot" warning in the logger
    TODO: get_characteristic_by_name raises a warning in the logger,
    coming from the container, when the field does not exist
    TODO: Seems that the maximum rate is ~40 Hz, check real maximum

    @author: igoroya
    @organization: HU Berlin
    @copyright: cta-observatory.org
    @version: $Id$
    @change: $LastChangedDate$, $LastChangedBy$
    """
    #-------------------------------------------------------------------------

    def __init__(self):
        """
        Call superclass constructors and define private variables
        """
        CharacteristicComponent.__init__(self)
        ContainerServices.__init__(self)

        # dictionary to store the components with acquired references
        self.__componentsMap = {}

        self.__lostComponents = set()  # set of lost components

        self._isRecording = threading.Event()

        # is the recorder full?
        self._isFull = False

        self.__totalStoredProps = 0

        # get threading lock to make some methods synchronized
        self.__lock = threading.RLock()

        self._checkThread = None

    #-------------------------------------------------------------------------
    def initialize(self):
        """
        Implementation of lifecycle method.
        Tries to gets access to the CDB, and initializes the configuration
        to be used by this property recorder. If no access exists to the CDB
        then default values are used.
        """
        self.getLogger().logDebug("called...")

        # I create the config object here because at __init__ there is no ACS
        # logger
        # stores the configuration (maximum number of componets etc.)
        self.__config = recorder_config(self.getLogger())

        # Get access to the CDB
        cdb = CDBAccess.cdb()

        # try:
        try:
            componentCDBXML = cdb.get_DAO('alma/%s' % (self.getName()))
            componentCDB = XmlObjectifier.XmlObject(componentCDBXML)
        except cdbErrType.CDBRecordDoesNotExistEx:
            self.getLogger().logInfo(
                "The DAO could not get for the property recorder, using the default values")
        except ExpatError as e:
            self.getLogger().logInfo(
                "The CDB expression could not be decoded: "
                + str(e) +
                " .Using the default values")
        except Exception:
            self.getLogger().logInfo(
                "Problem reading CDB information, using the default values")
        else:
            try:
                self.__config.getCDBData(componentCDB)
            except Exception:
                self.getLogger().logInfo(
                    "Problem when decoding the CDB information, using defaults")

        self.__config.printConfigs()

        # Create the registry object
        self._storage = self.__config.storage
        if self.__config.storage_config is None:
            self._registry = self._storage()   
        else :
            self._registry = self._storage(**self.__config.storage_config)   
        
        # if it is an standalone recorder this will be created by the parent
        # class
        if self._checkThread is None:
            self._checkThread = self._createComponentCheckThread()
            self._checkThread.start()
        # How to check for new component being activated? One possibility would
        # be to have a componentListener
        # as available in the Java implementation:
        # services.registerComponentListener(listener);
        # It is not available for ACS python, therefore the developed
        # solution uses  periodically check
        # for new components, as well as for dead ones, with a timer
        # start after one second and then do periodically according to
        # self.__checkingPeriod
    #-------------------------------------------------------------------------

    def cleanUp(self):
        """
        Lifecycle method. Stops the checkThread, closes monitors and
        release all references.
        """
        self.getLogger().logDebug("called...")
        

        self._checkThread.stop()

        self.__releaseComponents()
        
        self._registry = None;
      
       
    #-------------------------------------------------------------------------

    def startRecording(self):
        """
        CORBA Method implementation. Sends signal to start recording data
        """

        self.getLogger().logInfo("starting monitoring")

        if(self._isRecording.isSet()):
            self.getLogger().logInfo("monitoring already started")
            return

        self._isRecording.set()

        # self.__scanForProps()#so it take immediate action when the method is
        # issued
        self.getLogger().logInfo("monitoring started")
    #-------------------------------------------------------------------------

    def stopRecording(self):
        """
        CORBA Method implementation. Sends signal to stop recording,
        releases all components, and destroys monitors
        """
        self.getLogger().logInfo("stopping recording")

        self.getLogger().logDebug("take lock")
        self.__lock.acquire()
        try:
            self._isRecording.clear()
            # Here I remove references, I could pause them as well but provides
            # extra complications in bookkeeping
            self.__releaseComponents()

        finally:
            self.getLogger().logDebug("release lock")
            self.__lock.release()

   #-------------------------------------------------------------------------

    def isRecording(self):
        """
        CORBA Method

        Returns:
        TRUE     -- if recording is started, otherwise FALSE
        """
        self.getLogger().logDebug("called...")

        if(self._isRecording.isSet()):
            return TRUE
        else:
            return FALSE

    #-------------------------------------------------------------------------
    def addComponent(self, componentId):
        """
        CORBA method that allows to insert one component from outside
        for monitoring the properties. Used by the distributer
        to insert components in a particular recorder

        Keyword arguments:
        componentId     -- string with the component ID

        returns TRUE or FALSE if it managed to insert or not the component
        """

        self.getLogger().logDebug("called...")

        self.getLogger().logDebug("take lock")
        self.__lock.acquire()

        try:

            if not self.__checkComponent(componentId):
                return FALSE

            # check that the propertyRecorder is not full
            if (self._isFull):
                self.getLogger().logInfo("recorder is full")
                return FALSE

            try:
                # get no sticky so we do not prevent them of being deactivated
                component = self.getComponentNonSticky(componentId)
            except Exception:
                self.getLogger().logCritical(
                    "could not get a reference to the component due to an exception: "
                    + str(componentId))
                return FALSE

            # skip other property recorders
            if(component._NP_RepositoryId == constants.RECORDER_NP_REP_ID):
                self.getLogger().logDebug("skipping property recorders")
                return FALSE

            # store the component data into the dict  comp name :: component
            # curl
            compInfo = collections.namedtuple(
                'componentInfo',
                ['compReference',
                 'monitors'],
                verbose=False)

            compInfo.compReference = component

            # Gets properties, get the list of monitors, store them into the
            # componentInfo

            compInfo.monitors = self.__getComponentCharacteristics(compInfo)

            self.__componentsMap[componentId] = compInfo

            if compInfo.monitors is not None:
                self.__totalStoredProps = self.__totalStoredProps + \
                    len(compInfo.monitors)

            # check if now the recorder is full
            if len(self.__componentsMap) >= self.__config.maxComps:
                self._isFull = True
                self.getLogger().logWarning(
                    "recorder is full, max num of components")
            if self.__totalStoredProps >= self.__config.maxProps:
                self._isFull = True
                self.getLogger().logWarning(
                    "recorder is full, max num of properties")
        finally:
            self.getLogger().logDebug("release lock")
            self.__lock.release()

        return TRUE
    #-------------------------------------------------------------------------

    def setBackend(self, type, config):
        """
        CORBA method implementation to set a backend

        Keyword arguments:
        type -- CORBA enum with the backend type
        config -- Python encoding string representing a map
                  with the backend configuration

        Raises
            CouldntPerformActionEx
        """
        self.getLogger().logDebug("called...")

        if self._isRecording.isSet():
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData(
                "ErrorDesc",
                "The component is recording and the backend"
                " cannot be changed")
            raise ex

        self.getLogger().logDebug("Selected backend:" + str(type))

        try:
            storage = BackendMap[str(type)]
        except KeyError:
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData(
                "KeyError",
                "The backend type " + str(type) +
                " is not recognized")
            raise ex

        if storage is None:
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData(
                "Unsupported",
                "The backend type " + str(type) +
                " is not supported yet")
            raise ex

        if config is not None:
            try:
                #self.storage_config = str(attribute)
                self.__config.storage_config = ast.literal_eval(config)
            except Exception:
                self.__logger.warning(
                    "the backend_config string could not be decoded")
                raise Exception

        self._storage = storage
        self.__config.storage = self._storage
        self._registry = self._storage()
    #-------------------------------------------------------------------------

    def __checkComponent(self, componentId):
        """
        Checks if the component is already stored, and if can be stored

        If it is already stored but has wrong state, remove from
        the global list and feed the
        self.__lostComponents set for the PropertyDistributerRecorder

        Keyword arguments:
        componentId     -- string with the component ID

        returns True if can be stored, False if not
        """

        if componentId in self.__componentsMap:
            self.getLogger().logInfo(
                "the component " + componentId + " is already registered")

            compEntry = self.__componentsMap.get(componentId)

            # check if is still reachable, if not remove from the list. TODO:
            # these lines are repeated somewhere else, unify
            state = None
            try:
                state = compEntry.compReference._get_componentState()
            except Exception:
                self.getLogger().logInfo(
                    "the reference of " + componentId +
                    " does not exists any more , removing it")
                self.__componentsMap.pop(componentId)
                self.__lostComponents.add(componentId)
                return False

            if (str(state) != "COMPSTATE_OPERATIONAL"):
                self.getLogger().logInfo(
                    "the component  " + componentId +
                    " is not any more operational, removing it")
                self.__componentsMap.pop(componentId)
                self.__lostComponents.add(componentId)
                return False

            else:
                return False  # it is operational but registered, so exist

        # Skipping the self component to avoid getting a self-reference
        if(componentId == self.getName()):
            self.getLogger().logDebug("skipping myself")
            return False

        return True
    #-------------------------------------------------------------------------

    def setMaxComponents(self, maxComp):
        """
        CORBA method implementation to set the maximum number
        of components for the particular recorder.

        Keyword arguments:
        maxComp     -- integer for the maximum number of components
        """
        self.__config.maxComps = maxComp
    #-------------------------------------------------------------------------

    def setMaxProperties(self, maxProp):
        """
        CORBA method implementation to set the maximum number of
        properties for the particular recorder.

        Keyword arguments:
        maxProp     -- integer for the total maximum number of properties
        """
        self.__config.maxProps = maxProp
    #-------------------------------------------------------------------------

    def setMonitorDefaultRate(self, rate):
        """
        CORBA method implementation to set the default
        monitor rate for the new properties to be created.

        The default rate will be only applied for those properties
        without a value in 'default_timer_trig' characteristic.
        Only can be called if the recorder is not recording, in order
        to avoid having a mixture of properties with default monitor rates.

        Keyword arguments:
        rate     -- integer in seconds

        Raises:
        CouldntPerformActionEx    -- If the recorder is recording
        """
        if self._isRecording.isSet():
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData(
                "ErrorDesc",
                "The component is recording and the default"
                "value cannot be changed")
            raise ex

        self.__config.defaultMonitorRate = rate * \
            10000000  # convert to OMG time, that is 100 ns

    def getMonitorDefaultRate(self):
        """
        CORBA method implementation to get the value of
        the default monitor rate for the new properties to be created

        Returns:
        monitoring rate in seconds
        """
        return (
            # convert to OMG time, that is 100 ns
            self.__config.defaultMonitorRate / 10000000
        )
    #-------------------------------------------------------------------------

    def isFull(self):
        """
        CORBA method implementation to check if a property
        writer is full. Full recorders do not insert new components

        Returns: TRUE if it is full, FALSE otherwise
        """
        if self._isFull:
            return TRUE
        else:
            return FALSE
    #-------------------------------------------------------------------------

    def getLostComponent(self):
        """
        CORBA method implementation to get the components lost since the
        last call of this method

        Mainly designed to work together with the PropertyRecorderDistributer

        Returns: list of strings with the IDs of lost components
        """
        # make it thread-safe
        self.getLogger().logDebug("take lock")

        self.__lock.acquire()
        try:
            lostComponents = self.__lostComponents

            # reset the list
            self.__lostComponents.clear()
        finally:
            self.getLogger().logDebug("release lock")
            self.__lock.release()

        return lostComponents

    #-------------------------------------------------------------------------

    def __releaseComponent(self, componentId):
        """
        Removes a particular reference

        Keyword arguments:
        componentId     -- string with the component ID
        """
        self.getLogger().logInfo("__releaseComponent() called...")

          # loop over the componentMap
        # for compName, compInfo in self.__componentsMap().iteritems():
        try:
            compInfo = self.__componentsMap.pop(componentId)
        except KeyError:
            self.getLogger().logWarning(
                "component does not exist in the list, nothing to be done")
            return
        except AssertionError as b:
            self.getLogger().logWarning(
                "assertionError " + b, " exiting method")
            return
        if compInfo is None:
            self.getLogger().logWarning(
                "component does not exist, nothing to be done")
            return

        self.getLogger().logInfo("releasing component: " + componentId)

        self.__removeMonitors(compInfo)

        self.__lostComponents.add(componentId)
    #-------------------------------------------------------------------------

    def __removeMonitors(self, compInfo):
            # destroy all the monitors belonging that component
        if compInfo.monitors is not None:
            for monitor in compInfo.monitors:
                try:
                    monitor.destroy()
                except Exception:
                    self.getLogger().logWarning(
                        "exception when deactivating the monitor: "
                        + str(monitor))
                if (self.__totalStoredProps > 0):
                    self.__totalStoredProps = self.__totalStoredProps - 1
                else:
                    self.getLogger().logWarning("no stored properties found")
                if self.__totalStoredProps < self.__config.maxProps:
                    self._isFull = False

        # release the reference to the component
        # self.releaseComponent(componentId)
   #-------------------------------------------------------------------------
    def __releaseComponents(self):
        """
        Private method to release all references and to destroy all monitors
        """

        self.getLogger().logDebug("called...")

        # debugging stuff
        self.getLogger().logDebug(
            "length of the dictionary:  " + str(len(self.__componentsMap)))

        # loop over the componentMap
        # for compName, compInfo in self.__componentsMap().iteritems():
        for compName, compInfo in self.__componentsMap.items():
            self.getLogger().logInfo("deactivating component: " + compName)

            self.__releaseComponent(compName)

        # now empty the dictionary / map
        self.__componentsMap.clear()

        self._isFull = False
        self.__totalStoredProps = 0

    #-------------------------------------------------------------------------
    def __getComponentCharacteristics(self, compInfo):
        """
        Private method to find and evaluate the properties
        and characteristics of a Component
        It reads the CDB entry of the component and
        decoded and interprets it.

        Keyword arguments:
        property     -- compInfo a namedTuple object

        Returns monitorList with all the monitors created, or None if not possible
        """
        self.getLogger().logDebug("called...")

        component = compInfo.compReference

        # Next try/catch should check if the component is actually a
        # characteristic component. Otherwise will exit
        try:
            chars = component.find_characteristic("*")
        except Exception:
            self.getLogger().logInfo(
                "the component " + component._get_name() +
                " does not have characteristics")
            return None

        nChars = len(chars)
        self.getLogger().logDebug("number of Chars = " + str(nChars))

        # prepare a list to store all the created monitors
        monitorList = []

        if (nChars == 0):  # If nchars==0 we believe that it is a Python comp.
            self.getLogger().logInfo(
                "number of chars is 0: It could be a Python component")

            characteristics = property_characteristics_xml_objectifier(
                component, self.getLogger(), self.__config.defaultMonitorRate,
                self)  # this is used because we believe it is a Python component

            monitorList = characteristics.getMonitorList()

        else:  # Then it is either Java or C++
            characteristics = property_characteristics(
                component,
                self.getLogger(),
                self.__config.defaultMonitorRate,
                self)

            monitorList = characteristics.getMonitorList()

        return monitorList
    #-------------------------------------------------------------------------

    def _createMonitor(self, property, timeTrigger, delta, deltaPerc, buffer):
        """
        Method to create the monitors of the properties of a Component

        Keyword arguments:
        property     -- property object
        timeTrigger  -- time trigger for the monitor in OMG time (100 of ns)
        delta        -- value change, in absolute units to trigger the monitor
        deltaPerc    -- value change, in percentage, to trigger the monitor

        Returns: the monitor
        may raise a TypeError exception
        """
        self.getLogger().logDebug("createMonitor() called...")

        cbMon = CBFactory.getCallback(
            property,
            buffer,
            self.getLogger())

        # Activate the callback monitor
        cbMonServant = self.activateOffShoot(cbMon)
        # Create the real monitor registered with the component

        desc = ACS.CBDescIn(0, 0, 0)
        propMon = property.create_monitor(cbMonServant, desc)

        self.getLogger().logInfo("Time trigger to use: " + str(timeTrigger))

        # Note, here time should be OMG time!
        propMon.set_timer_trigger(timeTrigger)

        if (delta != 0 and delta != "0"
                and delta != "false"
                and delta
                and delta is not None):
            propMon.set_value_trigger(delta, True)

        if (deltaPerc != 0 and deltaPerc != "0"
                and deltaPerc != "false"
                and deltaPerc
                and deltaPerc is not None):
            propMon.set_value_percent_trigger(deltaPerc, True)

        return propMon
    #-------------------------------------------------------------------------

    def _checkLostComponents(self):
        """
        Check is we lost any component before last check
        Take action if it is the case
        """
        self.getLogger().logDebug("called...")

        self.getLogger().logDebug("take lock")
        self.__lock.acquire()
        try:
            length = len(self.__componentsMap)

            # Already done when adding components
            # if length >= self.__config.maxComps:
            #    self._isFull = True

            for compName, compInfo in self.__componentsMap.items():
                self.getLogger().logDebug("checking component: " + compName)

                state = None

                try:
                    state = compInfo.compReference._get_componentState()
                except Exception:
                    self.getLogger(
                    ).logInfo(
                        "The reference of the component " +
                        compName +
                        "  is not valid any more, removing it")
                    # I think that the monitors will be destroyed when the
                    # component is destroyed so I no not need to do myself
                    self.__componentsMap.pop(compName)

                    self.__lostComponents.add(compName)

                    continue

                if (str(state) != "COMPSTATE_OPERATIONAL"):
                    self.getLogger().logInfo("The component "
                                             + compName
                                             + " if found to be in the state "
                                             + str(state) + ", removing it")
                    if compInfo.monitors is not None:
                        for monitor in compInfo.monitors:
                            monitor.destroy()
                            self.__totalStoredProps = self.__totalStoredProps - 1
                        self.__componentsMap.pop(componentId)

                    self.__lostComponents.add(componentId)

            # print number of removed comps
            length -= len(self.__componentsMap)

            if length > 0:
                self.getLogger(
                ).logInfo("%d component(s) removed from the records" %
                          (length,))
            else:
                self.getLogger().logDebug(
                    "no component was removed from the records")

            self.getLogger().logDebug("release lock")
        finally:
            self.__lock.release()

    #-------------------------------------------------------------------------

    def __pauseMonitors(self):
        """
        To pause monitors instead of stopping them.
        It is not tested, and not used at the moment,
        perhaps we do not need it
        """
        # TODO:Remove method?
        self.getLogger().logDebug("called...")

        # loop over the componentMap
        for compName, compInfo in self.__componentsMap.items():

            # pause all the monitors
            if compInfo.monitors is not None:
                for monitor in compInfo.monitors:
                    try:
                        self.getLogger().logInfo(
                            "pausing the monitor: " + str(monitor))
                        monitor.pause()

                    except Exception:
                        self.getLogger().logInfo(
                            "exception when pausing the monitor: "
                            + str(monitor), " try to destroy it")
                        try:
                            self.getLogger().logInfo(
                                "destroying the monitor: " + str(monitor))
                            compInfo.monitors.remove[monitor]
                        except Exception:
                            self.getLogger().logInfo(
                                "Exception when destroying the monitor: " + str(monitor))

            else:
                self.getLogger().logInfo(
                    "no monitors existed in the component: " + compName)

        # now empty the dictionary / map
        # self.__componentsMap.clear()

    def _getProperty(self, component, chars):
        """
        Allows to evaluate a characteristic by using the capabilities of the
        Python ACS components (in this case the recorder), in order to check
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
        myPropStr = 'component' + '._get_' + chars + '()'
        myPro = None

        self.getLogger().logDebug("evaluating: " + myPropStr)
        try:
            myPro = eval(myPropStr)
        except Exception:
            self.getLogger().logDebug(
                "it was not possible to get the property, jumping to next one")
        return myPro
    #-------------------------------------------------------------------------

    def _createComponentCheckThread(self):
        return recorder.ComponentCheckThread(self)

    #-------------------------------------------------------------------------
    class ComponentCheckThread(threading.Thread):

        """
        Inner class defining a thread to the check components
        The thread is activated if the recorder is recording, and performs
        a periodic check (at a rate according to the configuration of the
        recorder) for lost components The thread is stopped if the recorder
        is not recording anymore

        Attributes:
            sleep_event -- event to govern the periodic execution of the thread
                           read from the configuration at __init__
            self.daemon -- Is the thread a daemon (default True)
        """

        def __init__(self, recorderInstance):
            threading.Thread.__init__(self)
            self._recorderInstance = recorderInstance
            self.sleep_event = threading.Event()
            self.daemon = True

        def run(self):
            while True:
                if not self._recorderInstance._isRecording.isSet():
                    self._recorderInstance.getLogger().logDebug(
                        "waiting for recording to start...")
                self._recorderInstance._isRecording.wait()
                threading.Thread(target=self._run).start()
                self.sleep_event.clear()
                self.sleep_event.wait(
                    self._recorderInstance._recorder__config.checkingPeriod)

        def _run(self):
            # Check if we lost any property
            self._recorderInstance._checkLostComponents()

        def reset(self):
            self.sleep_event.clear()

        def stop(self):
            self._Thread__stop
            # I needed to add this stop because, even if a daemon, the Python
            # component would show errors (showing up up periodically) due to a
            # because this thread did not finished. With this it worked well.
    #----------------------------------------------------------------------


class recorder_config:

    """
    Holds the configuration from the property recorder

    Attributes:
    defaultMonitorRate -- Monitoring rate for those properties
                          with no CDB entry for the monitoring rate
                          in ACS time units
                          (default 600000000; eq. 1 minute )
    maxComps           -- Maximum number of components accepted by this
                          property recorder (default 100)
    maxProps           -- Maximum number of properties being monitored
                          (default 1000)
    checkingPeriod     -- Period to check for lost components or new components
                          (in standalone mode)
    storage            -- Backend type (Default STORAGE_TYPE.LOG)
    storage_config     -- Map with configuration parameters for the backend
                          (Default None)
    """
    #-------------------------------------------------------------------------

    def __init__(self, logger):
        """
        Initializes the values to those defined as default
        These are the values to be used with the dynamic components
        """
        self.__logger = logger

        # Default values in case not CDB entry exists or it is faulty, and more
        # important, used for the dynamic components
        # 1/min, units in in 100 of ns, OMG time
        self.defaultMonitorRate = 600000000
        # will not accept more components if this number is exceeded
        self.maxComps = 100
        # will accept more components if the total number of props is this
        # number or more
        self.maxProps = 1000
        self.checkingPeriod = 20  # seconds
        self.storage = STORAGE_TYPE.LOG
        self.storage_config = None

        #----------------------------------------------------------------------

    def getCDBData(self, componentCDB):
        """
        Initializes the values to those from the CDB

        raises:
            Exception if the read attribute cannot be read
        """
        try:
            val = ast.literal_eval(
                componentCDB.firstChild.getAttribute(
                    "default_monitor_rate").decode(
                    ))
            self.defaultMonitorRate = int(val)
        except Exception:
            self.__logger.logInfo(
                "no CDB information for default_monitor_rate retrieved")
            return

        attribute = None

        try:
            attribute = componentCDB.firstChild.getAttribute(
                "max_comps").decode()
        except Exception:
            self.__logger.logInfo(
                "no CDB information for max_comps, use default")
        else:
            try:
                val = ast.literal_eval(attribute)
                self.maxComps = int(val)
            except Exception:
                self.__logger.critical(
                    "the CDB information for max_comps could not be decoded")
                raise Exception  # Todo: use my own defined exceptions here?
        try:
            attribute = componentCDB.firstChild.getAttribute(
                "backend").decode()
        except Exception:
            self.__logger.logInfo(
                "no CDB information for backend, use default")
        else:
            try:
                self.storage = BackendMap[str(attribute)]
            except Exception:
                self.__logger.logCritical(
                    "the CDB information for the backend could not be decoded")
                raise Exception
        try:
            attribute = componentCDB.firstChild.getAttribute(
                "backend_config").decode()
        except Exception:
            self.__logger.logInfo(
                "no CDB information for backend, use no configuration")
        else:
            try:
                #self.storage_config = str(attribute)
                self.storage_config = ast.literal_eval(attribute)
            except Exception:
                self.__logger.warning(
                    "the CDB information for backend_config could not be decoded")
                raise Exception
        try:
            attribute = componentCDB.firstChild.getAttribute(
                "max_props").decode()
        except Exception:
            self.__logger.logInfo(
                "no CDB information for max_props, use default")
        else:
            try:
                val = ast.literal_eval(attribute)
                self.maxComps = int(val)
            except Exception:
                self.__logger.critical(
                    "the CDB information for max_props could not be decoded")
                raise Exception  # Todo: use my own defined exceptiosn here?

        try:
            attribute = componentCDB.firstChild.getAttribute(
                "checking_period").decode()
        except Exception:
            self.__logger.logInfo(
                "no CDB information for checking_period, use default")
        else:
            try:
                val = ast.literal_eval(attribute)
                self.maxComps = int(val)
            except Exception:
                self.__logger.critical(
                    "the CDB information for checking_period could not be decoded")
                raise Exception

    def printConfigs(self):
        "Prints the configs in the logger"
        self.__logger.logInfo(
            "====================================================")
        self.__logger.logInfo("Configuration parameters")
        self.__logger.logInfo(
            "defaultMonitorRate = " + str(
                self.defaultMonitorRate))
        self.__logger.logInfo("maxComps = " + str(self.maxComps))
        self.__logger.logInfo("maxProps = " + str(self.maxProps))
        self.__logger.logInfo("checkingPeriod = " + str(self.checkingPeriod))
        self.__logger.logInfo("storage = " + str(self.storage))
        self.__logger.logInfo("storage_config = " + str(self.storage_config))
        self.__logger.logInfo(
            "====================================================")
#------------------------------------------------------------------------------


class property_characteristics():

    '''
    Holds the characteristics of a property of a component
    of C++ or Java implementation

    It uses the component.get_characteristic_by_name method
    that is much faster than the alternative
    property_characteristics_xml_objectifier

    '''

    def __init__(self, component, logger, defaultMonitorRate, recorder):
        '''
        Constructor
        variables component
        '''
        self.__monitorList = []
        self._component = component
        self._logger = logger
        self.__defaultMonitorRate = defaultMonitorRate
        self._recorder = recorder
        self.__registry = recorder._registry
        self._createBuffers()

    def getMonitorList(self):
        """
        Returns a List of the created monitors
        """
        return self.__monitorList
    #-------------------------------------------------------------------------

    def _createBuffers(self):
        '''
        Raises:
            AttributeError -- no states description is found in the CDB
        '''
        try:
            chars = self._component.find_characteristic("*")
        except Exception:
            self._logger.logInfo(
                "the component " + self._component._get_name() +
                " does not have characteristics")
            return

        nChars = len(chars)

        count = 0
        while (count < nChars):
            myCharList = self._component.get_characteristic_by_name(
                str(chars[count])).value().split(',')
            #self._logger.logInfo('The entry has '+str(len(myCharList))+' characteristics')
            # As a way of discerning from a property to other type of
            # characteristic, I check for the length of the char list. If it is
            # longer than 5, then is probably a property
            if (len(myCharList) > 5):
                self._logger.logDebug(
                    "probably is a property, trying the information of the archive")

                # Check if the characteristic is a property

                myPro = self._recorder._getProperty(self._component,
                                                    chars[count])
                if myPro is None:
                    count = count + 1
                    continue

                # Try that the property is actually readable before proceeding
                # There is a funny behavior with the patter properties in Java
                # implementation (TODO: Find a solution): is crashes with
                # get_sync! I try here without proceeding
                try:
                    (myPro.get_sync()[0])
                except Exception:
                    self._logger.logDebug(
                        "it was not possible to call get_sync in the property"
                        ", this is typically happening with pattern"
                        "properties OR when the property exists in the CDB"
                        "but it is not implemented in the component")
                    count = count + 1
                    continue

                # getting all the CDB info and archiving
                propDict = {}

                propDict['name'] = myPro._get_name()
                propDict['timestamp'] = myPro.get_sync()[1].timeStamp
                try:
                    propDict['archive_priority'] = str(
                        myPro.get_characteristic_by_name(
                            "archive_priority").value())
                except Exception:
                    propDict['archive_priority'] = None
                try:
                    propDict['archive_min_int'] = str(
                        myPro.get_characteristic_by_name(
                            "archive_min_int").value())
                except Exception:
                    propDict['archive_min_int'] = None
                try:
                    propDict['archive_max_int'] = str(
                        myPro.get_characteristic_by_name("archive_max_int").value())
                except Exception:
                    propDict['archive_max_int'] = None
                try:
                    archiveSString = myPro.get_characteristic_by_name(
                        "archive_suppress").value()
                    if archiveSString.lower() == "true" or archiveSString.lower() == "yes":
                        propDict['archive_suppress'] = True
                    else:
                        propDict['archive_suppress'] = False
                except Exception:
                    propDict['archive_suppress'] = False
                try:
                    propDict['archive_mechanism'] = myPro.get_characteristic_by_name(
                        "archive_mechanism").value()
                except Exception:
                    propDict['archive_mechanism'] = None
                try:
                    propDict['archive_delta'] = myPro.get_characteristic_by_name(
                        'archive_delta').value()
                except Exception:
                    propDict['archive_delta'] = None
                try:
                    propDict['archive_delta_percent'] = myPro.get_characteristic_by_name(
                        'archive_delta_percent').value()
                except Exception:
                    propDict['archive_delta_percent'] = None
                try:
                    defaultTime = myPro.get_characteristic_by_name(
                        'default_timer_trig').value()
                    # make sure that we handle 0s or negative values, as this
                    # is important
                    if ast.literal_eval(defaultTime) <= 0.0:
                        propDict['default_timer_trig'] = None
                    else:
                        propDict['default_timer_trig'] = defaultTime
                except Exception:
                    propDict['default_timer_trig'] = None
                try:
                    propDict['default_value'] = myPro.get_characteristic_by_name(
                        'default_value').value()
                except Exception:
                    propDict['default_value'] = None
                try:
                    propDict['description'] = myPro.get_characteristic_by_name(
                        'description').value()
                except Exception:
                    propDict['description'] = None
                try:
                    propDict['format'] = myPro.get_characteristic_by_name(
                        'format').value()
                except Exception:
                    propDict['format'] = None
                try:
                    propDict['graph_max'] = myPro.get_characteristic_by_name(
                        'graph_max').value()
                except Exception:
                    propDict['graph_max'] = None
                try:
                    propDict['graph_min'] = myPro.get_characteristic_by_name(
                        'graph_min').value()
                except Exception:
                    propDict['graph_min'] = None
                try:
                    propDict['min_delta_trig'] = myPro.get_characteristic_by_name(
                        'min_delta_trig').value()
                except Exception:
                    propDict['min_delta_trig'] = None
                try:
                    propDict['min_step'] = myPro.get_characteristic_by_name(
                        'min_step').value()
                except Exception:
                    propDict['min_step'] = None
                try:
                    propDict['min_timer_trig'] = myPro.get_characteristic_by_name(
                        'min_timer_trig').value()
                except Exception:
                    propDict['min_timer_trig'] = None
                try:
                    propDict['resolution'] = myPro.get_characteristic_by_name(
                        'resolution').value()
                except Exception:
                    propDict['resolution'] = None
                try:
                    data = myPro.get_characteristic_by_name(
                        'units').value()
                    #MongoDB backend can only handle utf8 data, so we check that 
                    #TODO: Use with other attributes?
                    udata = DecodeUtil.try_utf8(data)
                    if udata is None:
                        self._logger.logWarning("units is not using UTF-8 data format, ignoring")
                    propDict['units'] = udata
                except Exception:
                    propDict['units'] = None
                try:
                    propDict['type'] = myPro.get_characteristic_by_name(
                        'type').value()
                except Exception:
                    propDict['type'] = None
                try:
                    propDict['condition'] = myPro.get_characteristic_by_name(
                        'condition').value()
                except Exception:
                    propDict['condition'] = None
                try:
                    propDict['bitDescription'] = myPro.get_characteristic_by_name(
                        'bitDescription').value()
                except Exception:
                    propDict['bitDescription'] = None
                try:
                    propDict['statesDescription'] = myPro.get_characteristic_by_name(
                        'statesDescription').value()
                except Exception:
                    propDict['statesDescription'] = None
                try:
                    propDict['whenCleared'] = myPro.get_characteristic_by_name(
                        'statesDescription').value()
                except Exception:
                    propDict['whenCleared'] = None
                try:
                    propDict['whenSet'] = myPro.get_characteristic_by_name(
                        'statesDescription').value()
                except Exception:
                    propDict['whenSet'] = None

                if propDict.get("archive_suppress") is True:
                    count = count + 1
                    continue  # be

                propertyType = None
                               
                try:
                    propertyType = PropertyTypeUtil.getPropertyType(
                        myPro._NP_RepositoryId)
                # If key error, then it is probably an enum
                except TypeError:
                    self._logger.logWarning(
                        "Property type not supported, skipping")
                    count = count + 1
                    continue

                except KeyError:
                    count = count + 1
                    continue
               
                #TODO: Think in what to do with the enum states
                enumStates = None
                
                if (propertyType is None) or (propertyType is PropertyType.OBJECT):
                    propertyType = PropertyType.OBJECT #TODO: Try to get this from the PropertyUtil 
                    try:
                        enumStates = PropertyTypeUtil.getEnumPropDict(myPro, self._logger)
                        self._logger.logDebug("Enum States found: "+str(enumStates))
                        
                    except Exception:
                        self._logger.logDebug(
                            "Enum states cannot be read, use the int representation")

                try:         
                    buffer = self.__registry.register(component_name=self._component._get_name(),
                                       component_type = self._component._NP_RepositoryId,
                                       property_name = myPro._get_name(),
                                       property_type = propertyType,
                                       property_type_desc = enumStates, 
                                       **propDict) 
                except Exception:
                    self._logger.logWarning(
                        "could not create buffer, skipping")
                else:
                    self._createMonitor(myPro, propDict, buffer)
                # Creating monitors
                          # end if
            count = count + 1
    #-------------------------------------------------------------------------

    def _createMonitor(self, property, propDict, buffer):
        monitor = None

        timeTriggerOmg = self.__defaultMonitorRate

        try:
            timeTriggerCasted = ast.literal_eval(
                propDict.get("default_timer_trig"))
            # threre were getting cast problems and annoying behavior so went
            # to the safe side
            # change to OMG time
            timeTriggerOmg = long(timeTriggerCasted * 10000000)
        except Exception:
            self._logger.logDebug("no time trigger found in the CDB, "
                                  "using the default value of %l"
                                  % self.__defaultMonitorRate)
            timeTriggerOmg = self.__defaultMonitorRate

        # archive_delta and archive_delta_percent can come in several
        # flavors depending on the property type, if not handled with care
        # then exception will happen when creating the monitors
        if propDict.get("archive_delta") == "false":
            aDelta = False
        elif (propDict.get("archive_delta") == "0"
              or propDict.get("archive_delta") == "0.0"):
            aDelta = False
        elif propDict.get("archive_delta") is not None:
            aDelta = ast.literal_eval(propDict.get("archive_delta"))

        if propDict.get("archive_delta_percent") == "false":
            aDeltaPerc = False
        elif (propDict.get("archive_delta") == "0"
              or propDict.get("archive_delta") == "0.0"
              or propDict.get("archive_delta") == 0
              or propDict.get("archive_delta") == 0.0):
            aDeltaPerc = False
        elif propDict.get("archive_delta_percent") is not None:
            aDeltaPerc = ast.literal_eval(
                propDict.get("archive_delta_percent"))

        monitor = self._recorder._createMonitor(
            property, timeTriggerOmg, aDelta, aDeltaPerc, buffer)

        if monitor is not None:
            self.__monitorList.append(monitor)
#------------------------------------------------------------------------------


class property_characteristics_xml_objectifier(property_characteristics):

    """
    Holds the characteristics of a property of a component
    of any implementation language (also Python).
    It is much slower than the propertyCharacteristics class
    (because it uses the XmlObjectifier), but for Python
    is the only option.
    """

    def __init__(self, component, logger, defaultMonitorRate, recorder):
        '''
        Constructor
        variables component
        '''
        property_characteristics.__init__(self, component, logger,
                                          defaultMonitorRate, recorder)

    #-------------------------------------------------------------------------
    def _createBuffers(self):
        """
        Loads the CDB data, creates the buffers and starts the monitors
        Overrides property_characteristics._createBuffers

        Raises:
            AttributeError -- no states description is found in the CDB
        """
        myCompName = self._component._get_name()

        # this was learned from D. Muders, and is the only
        # way I know to get all the chars from a Python component
        # My the way, looks somewhat slow when comparing to the
        # way done with Java and Python (see below), but probably
        # will have few python comps
        cdb = CDBAccess.cdb()

        try:
            componentCDBXML = cdb.get_DAO('alma/%s' % (myCompName))
        except Exception:
            self._logger.logWarning("could not get the component DAO")
            raise AttributeError  # TODO: ValueError?

        componentCDB = XmlObjectifier.XmlObject(componentCDBXML)
        elementList = (componentCDB.getElementsByTagName("*"))

        myPro = None

        for element in elementList:
            nodeString = element.nodeName

            myPro = self._recorder._getProperty(self._component, nodeString)

            if myPro is None:
                continue

            try:
                (myPro.get_sync()[0])
                self._logger.logDebug("could set get_sync, it IS a property")
            except Exception:
                self._logger.logDebug(
                    "could not set get_sync, it  IS NOT a property")
                continue

            propNode = str('alma/%s/%s' % (myCompName, nodeString))
            propertyCDBXML = cdb.get_DAO(propNode)
            propertyCDB = XmlObjectifier.XmlObject(propertyCDBXML)

            propDict = {}

            propDict['name'] = myPro._get_name()
            propDict['timestamp'] = myPro.get_sync()[1].timeStamp

            try:
                propDict['archive_priority'] = propertyCDB.firstChild.getAttribute(
                    "archive_priority").decode()
            except Exception:
                propDict['archive_priority'] = None
            try:
                propDict['archive_min_int'] = propertyCDB.firstChild.getAttribute(
                    "archive_min_int").decode()
            except Exception:
                propDict['archive_min_int'] = None
            try:
                propDict['archive_max_int'] = propertyCDB.firstChild.getAttribute(
                    "archive_max_int").decode()
            except Exception:
                propDict['archive_max_int'] = None
            try:
                archiveSString = propertyCDB.firstChild.getAttribute(
                    "archive_suppress").decode()
                if (archiveSString.lower() == "true"
                        or archiveSString.lower() == "yes"):
                    propDict['archive_suppress'] = True
                else:
                    propDict['archive_suppress'] = False
            except Exception:
                propDict['archive_suppress'] = False
            try:
                propDict['archive_mechanism'] = propertyCDB.firstChild.getAttribute(
                    "archive_mechanism").decode()
            except Exception:
                propDict['archive_mechanism'] = None
            try:
                propDict['archive_delta'] = propertyCDB.firstChild.getAttribute(
                    'archive_delta').decode()
            except Exception:
                propDict['archive_delta'] = None
            try:
                propDict['archive_delta_percent'] = propertyCDB.firstChild.getAttribute(
                    'archive_delta_percent').decode()
            except Exception:
                propDict['archive_delta_percent'] = None
            try:
                defaultTime = propertyCDB.firstChild.getAttribute(
                    'default_timer_trig').decode()
                # make sure that we handle 0s or negative values, as this is
                # important
                if defaultTime <= 0.0:
                    propDict['default_timer_trig'] = None
                else:
                    propDict['default_timer_trig'] = defaultTime
            except Exception:
                propDict['default_timer_trig'] = None
            try:
                propDict['default_value'] = propertyCDB.firstChild.getAttribute(
                    'default_value').decode()
            except Exception:
                propDict['default_value'] = None
            try:
                propDict['description'] = propertyCDB.firstChild.getAttribute(
                    'description').decode()
            except Exception:
                propDict['description'] = None
            try:
                propDict['format'] = propertyCDB.firstChild.getAttribute(
                    'format').decode()
            except Exception:
                propDict['format'] = None
            try:
                propDict['graph_max'] = propertyCDB.firstChild.getAttribute(
                    'graph_max').decode()
            except Exception:
                propDict['graph_max'] = None
            try:
                propDict['graph_min'] = propertyCDB.firstChild.getAttribute(
                    'graph_min').decode()
            except Exception:
                propDict['graph_min'] = None
            try:
                propDict['min_delta_trig'] = propertyCDB.firstChild.getAttribute(
                    'min_delta_trig').decode()
            except Exception:
                propDict['min_delta_trig'] = None
            try:
                propDict['min_step'] = propertyCDB.firstChild.getAttribute(
                    'min_step').decode()
            except Exception:
                propDict['min_step'] = None
            try:
                propDict['min_timer_trig'] = propertyCDB.firstChild.getAttribute(
                    'min_timer_trig').decode()
            except Exception:
                propDict['min_timer_trig'] = None
            try:
                propDict['resolution'] = propertyCDB.firstChild.getAttribute(
                    'resolution').decode()
            except Exception:
                propDict['resolution'] = None
            try:
                data = propertyCDB.firstChild.getAttribute(
                    'units').decode()
                    #MongoDB backend can only handle utf8 data, so we check that 
                udata = DecodeUtil.try_utf8(data)
                if udata is None:
                    self._logger.logWarning("units is not using UTF-8 data format, ignoring")
                propDict['units'] = udata
            except Exception:
                propDict['units'] = None
            try:
                propDict['type'] = propertyCDB.firstChild.getAttribute(
                    'type').decode()
            except Exception:
                propDict['type'] = None
            try:
                propDict['condition'] = propertyCDB.firstChild.getAttribute(
                    'condition').decode()
            except Exception:
                propDict['condition'] = None
            try:
                # this is only happening in pattern props
                propDict['bitDescription'] = propertyCDB.firstChild.getAttribute(
                    'bitDescription').decode()
            except Exception:
                propDict['bitDescription'] = None
            try:
                # this is only happening in enum props
                propDict['statesDescription'] = propertyCDB.firstChild.getAttribute(
                    'statesDescription').decode()
            except Exception:
                propDict['statesDescription'] = None
            try:
                propDict['whenCleared'] = propertyCDB.firstChild.getAttribute(
                    'statesDescription').decode()
            except Exception:
                propDict['whenCleared'] = None
            try:
                propDict['whenSet'] = propertyCDB.firstChild.getAttribute(
                    'statesDescription').decode()
            except Exception:
                propDict['whenSet'] = None

            if propDict.get("archive_suppress") is True:
                return

#             buffer = self._property_characteristics__registry.register(
#                 self._component._get_name(),
#                 self._component._NP_RepositoryId,
#                 myPro._get_name(),
#                 PropertyTypeUtil.getPropertyType(
#                     myPro._NP_RepositoryId),
#                 None,
#                 False,
#                 **propDict)
            
            buffer = self.__registry.register(component_name=self._component._get_name(),
                                       component_type=self._component._NP_RepositoryId,
                                       property_name=myPro._get_name(),
                                       property_type=propertyType, 
                                       **propDict) 
            # TODO:for enums, the above line could use "States" instead of
            # None. Check
            self._createMonitor(myPro, propDict, buffer)

    #-------------------------------------------------------------------------
# ___oOo___
