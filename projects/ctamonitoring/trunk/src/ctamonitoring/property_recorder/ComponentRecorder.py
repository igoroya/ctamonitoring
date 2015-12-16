__version__ = "$Id: ComponenrRecorder.py 1623 2015-12-15 17:39:32Z igoroya $"
# --CORBA STUBS-------recorder_config------------------------------------------
import actl__POA
import actl
# Module Imports
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.front_end import FrontEnd
from ctamonitoring.property_recorder.frontend_exceptions import (
    BadCdbRecorderConfig)
from ctamonitoring.property_recorder.util import EnumUtil
from ctamonitoring.property_recorder.config import BackendType
# --ACS Imports----------------------------------------------------------
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
import ast
import pprint
'''
Contains the code to run the property recorder as an ACS component

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id: frontend_exceptions.py 1623 2015-12-15 17:39:32Z igoroya $
@change: $LastChangedDate: 2015-12-15 18:39:32 +0100 (Tue, 15 Dec 2015) $
@change: $LastChangedBy: igoroya $

Note: the module name and the class name of the component must match
I judged that was less confusing to have the package name to follow the Class
naming convention than the other way around.
'''


class ComponentRecorder(
        actl__POA.PropertyRecorder,
        CharacteristicComponent,
        ContainerServices,
        ComponentLifecycle):
    """
    Implementation of the PropertyRecorder interface as an ACS component.
    For the standalone, application version see standalone_recorder.py

    TODO: Understand the warning "not an offshoot" warning in the logger
    TODO: get_characteristic_by_name raises a warning in the logger,
    coming from the container, when the field does not exist
    TODO: Seems that the maximum rate is ~40 Hz, check real maximum

    """

    def __init__(self):
        """
        Call superclass constructors and define private variables
        """

        CharacteristicComponent.__init__(self)

        ContainerServices.__init__(self)

    def initialize(self):
        '''
        Implementation of lifecycle method.
        Gets access to the CDB, and initializes the configuration
        to be used by this property recorder. If no access exists to the CDB
        then default values are used.
        '''

        self._logger = self.getLogger()

        self._recorder_config = RecorderConfigDecoder.get_cdb_data(
            self.getName())

        self._logger.debug(
            'Property Recorder Configuration'
            '\n--------------------------------------\n' +
            pprint.pformat(vars(self._recorder_config)) +
            '\n--------------------------------------')

        self._recorder = FrontEnd(self._recorder_config, self)

        self._logger.info('Property recorder up')

    def cleanUp(self):
        """
        Lifecycle method. Stops the checkThread, closes monitors and
        release all references.
        """
        self._logger.info('Switching off property recorder')
        self._recorder.cancel()
        self._recorder = None

    def startRecording(self):
        """
        CORBA Method implementation. Sends signal to start recording data
        """

        self._recorder.start_recording()
        self._logger.info('Recording start')

    def stopRecording(self):
        """
        CORBA Method implementation. Sends signal to stop recording,
        releases all components, and destroys monitors
        """

        self._recorder.stop_recording()
        self._logger.info('Recording stop')

    def isRecording(self):
        """
        CORBA Method

        Returns:
        TRUE     -- if recording is started, otherwise FALSE
        """

        if(self._recorder.is_recording()):
            return TRUE
        else:
            return FALSE

    def addComponent(self, componentId):
        """
        CORBA method that allows to insert one component from outside
        for monitoring the properties. Used by the distributer
        to insert components in a particular recorder

        Keyword arguments:
        componentId     -- string with the component ID

        Raises:
            ACSErrTypeCommon::CouldntPerformActionEx -- if component c
                                                        could not be added
        """

        if not self._recorder.process_component(componentId):
            ex = ACSErrTypeCommonImpl.CouldntPerformActionExImpl()
            ex.addData(
                "ErrorDesc",
                "The component "
                + componentId +
                " could not be added")
            raise ex

    def isFull(self):
        """
        CORBA method implementation to check if a property
        writer is full. Full recorders do not insert new components

        Returns: TRUE if it is full, FALSE otherwise
        """
        if self._recorder.recoder_space.isFull:
            return TRUE
        else:
            return FALSE


class RecorderConfigDecoder(object):

    """
    Decodes the configuration from the property recorder from the CDB
    and creates a RecorderConfig object

    raises:
            BadCdbRecorderConfig if the attribute to be read is in
            an incorrect format

    returns: recorder_config

    """

    @staticmethod
    def get_cdb_data(component_name):

        cdb = CDBAccess.cdb()

        try:
            componentCDB = XmlObjectifier.XmlObject(
                cdb.get_DAO('alma/%s' % (component_name)))
        except cdbErrType.CDBRecorDoesNotExistEx as e:
            raise BadCdbRecorderConfig(e)
        except ExpatError as e:
            raise BadCdbRecorderConfig(e)
        except Exception as e:
            raise BadCdbRecorderConfig(e)

        recorder_config = RecorderConfig()

        try:
            recorder_config.default_timer_trigger = float(
                componentCDB.firstChild.getAttribute(
                    "default_timer_trigger")
                )

        except Exception as e:
            raise BadCdbRecorderConfig(e, "default_timer_trigger")

        try:
            recorder_config.max_comps = int(
                componentCDB.firstChild.getAttribute(
                    "max_comps")
                )
        except Exception as e:
            raise BadCdbRecorderConfig(e, "max_comps")

        try:
            recorder_config.max_props = int(
                componentCDB.firstChild.getAttribute(
                    "max_props")
                )
        except Exception as e:
                raise BadCdbRecorderConfig(e, "max_props")

        try:
            recorder_config.backend_type = EnumUtil.from_string(
                BackendType,
                componentCDB.firstChild.getAttribute(
                    "backend").decode()
                )
        except Exception as e:
            raise BadCdbRecorderConfig(e, "backend")

        try:
            recorder_config.backend_config = ast.literal_eval(
                componentCDB.firstChild.getAttribute(
                    "backend_config").decode())
        except Exception as e:
            raise BadCdbRecorderConfig(e, "backend_config")

        try:
            recorder_config.checking_period = int(
                componentCDB.firstChild.getAttribute(
                    "checking_period")
                )
        except Exception as e:
            raise BadCdbRecorderConfig(e, "checking_period")

        try:

            if componentCDB.firstChild.getAttribute("is_include") == 'true':
                recorder_config.is_include_mode = True
            elif componentCDB.firstChild.getAttribute("is_include") == 'false':
                recorder_config.is_include_mode = False
            else:
                raise BadCdbRecorderConfig()
        except Exception as e:
            raise BadCdbRecorderConfig(e, "is_include")

        try:
            componentCDB.firstChild.getAttribute(
                "component_list")
            recorder_config.set_components(set(
                ast.literal_eval(componentCDB.firstChild.getAttribute(
                    "component_list").decode()
                )))
        except Exception as e:
            raise BadCdbRecorderConfig(e, "component_list")

        return recorder_config
