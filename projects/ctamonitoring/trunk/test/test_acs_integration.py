#!/usr/bin/env python
"""
ACS Integration test for Property Recorder

This tests require ACS and certain components up to run,
the module testacsproperties is used. These are typically run only
ad the continuous integration steps and not during development

@requires: testacsproperties

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: unittest
@requires: ctamonitoring.property_recorder.util
@requires: logging
@requires: ctamonitoring.property_recorder.backend
@requires: enum
@requires: ctamonitoring.property_recorder.constants
"""
import unittest
import time
import logging
from ctamonitoring.property_recorder.util import component_util
from ctamonitoring.property_recorder.frontend_exceptions import (
    UnsupporterPropertyTypeError, CannotAddComponentException)
from Acspy.Clients.SimpleClient import PySimpleClient
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder.front_end import FrontEnd
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.front_end import FrontEnd

__version__ = "$Id$"

PropertyType = property_type.PropertyType


class ComponentUtilTest(unittest.TestCase):
    """
    This test requires ACS running with the testacsproperties CDB and
    the myC cpp container up
    """
    def setUp(self):
        self._my_acs_client = PySimpleClient()
        logger = self._my_acs_client.getLogger()
        logger.setLevel(logging.WARNING)
        # disable annoying output from the tests

    def tearDown(self):
        self._my_acs_client.disconnect()

    def test_get_enum_prop_dict(self):

        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)

        enum_prop = my_component._get_EnumTestROProp()

        decoded = component_util.get_enum_prop_dict(enum_prop)
        expected_value = {'0': 'STATE1', '1': 'STATE2', '2': 'STATE3'}
        self.assertEqual(expected_value, decoded)

        enum_prop = my_component._get_EnumTestRWProp()

        decoded = component_util.get_enum_prop_dict(enum_prop)
        expected_value = {'0': 'STATE1', '1': 'STATE2', '2': 'STATE3'}
        self.assertEqual(expected_value, decoded)

        self._my_acs_client.releaseComponent("TEST_PROPERTIES_COMPONENT")

    def test_get_property_type(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT",
            True)

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_EnumTestROProp()._NP_RepositoryId),
            PropertyType.OBJECT
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_EnumTestRWProp()._NP_RepositoryId),
            PropertyType.OBJECT
            )

        PropertyType.OBJECT

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleROProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatSeqRWProp()._NP_RepositoryId),
            PropertyType.FLOAT_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longSeqRWProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )
        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongROProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_booleanROProp()._NP_RepositoryId),
            PropertyType.BOOL
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleSeqROProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longLongROProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_patternROProp()._NP_RepositoryId),
            PropertyType.BIT_FIELD
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongRWProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_booleanRWProp()._NP_RepositoryId),
            PropertyType.BOOL
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleSeqRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_patternRWProp()._NP_RepositoryId),
            PropertyType.BIT_FIELD
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongSeqROProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            component_util.get_property_type,
            my_component._get_booleanSeqROProp()._NP_RepositoryId
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatROProp()._NP_RepositoryId),
            PropertyType.FLOAT
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longROProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_stringROProp()._NP_RepositoryId),
            PropertyType.STRING
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongSeqRWProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            component_util.get_property_type,
            my_component._get_booleanSeqRWProp()._NP_RepositoryId
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatRWProp()._NP_RepositoryId),
            PropertyType.FLOAT
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longRWProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_stringRWProp()._NP_RepositoryId),
            PropertyType.STRING
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatSeqROProp()._NP_RepositoryId),
            PropertyType.FLOAT_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longSeqROProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongROProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

    def test_is_archive_delta_enabled(self):

        # First test the cases when it should be false
        self.assertFalse(
            component_util.is_archive_delta_enabled(None)
            )
        self.assertFalse(
            component_util.is_archive_delta_enabled(False)
            )
        self.assertFalse(
            component_util.is_archive_delta_enabled("0")
            )
        self.assertFalse(
            component_util.is_archive_delta_enabled("0.0")
            )
        self.assertFalse(
            component_util.is_archive_delta_enabled(0)
            )
        self.assertFalse(
            component_util.is_archive_delta_enabled(0.0)
            )


class MoreComponentUtilTest(unittest.TestCase):
    """
    Test the integration of the component utilities
    """
    def setUp(self):
        self._my_acs_client = PySimpleClient()
        logger = self._my_acs_client.getLogger()
        logger.setLevel(logging.WARNING)

    def tearDown(self):
        self._my_acs_client.disconnect()

    def test_is_characteristic_component(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)
        self.assertTrue(
            component_util.is_characteristic_component(my_component)
            )
        # Now check a component that is not characteristic
        my_component2 = self._my_acs_client.getComponent("TIMER1", True)
        self.assertFalse(
            component_util.is_characteristic_component(my_component2)
            )

    def test_is_python_char_component(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_PYTHON", True)
        self.assertTrue(
            component_util.is_python_char_component(my_component)
            )
        # Now check a component that is not characteristic

        my_component2 = self._my_acs_client.getComponent(
            "TIMER1", True)

        self.assertRaises(
            AttributeError,
            component_util.is_python_char_component,
            my_component2
            )

        my_component3 = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)

        self.assertFalse(
            component_util.is_python_char_component(my_component3)
            )

    def test_is_a_property_recorder_component(self):
        my_component = self._my_acs_client.getComponent(
            "propertyRecorder1", True)
        self.assertTrue(
            component_util.is_a_property_recorder_component(my_component)
            )
        # Now check a component that is not characteristic
        my_component2 = self._my_acs_client.getComponent("TIMER1", True)
        self.assertFalse(
            component_util.is_a_property_recorder_component(my_component2)
            )

    def test_is_component_state_ok(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)
        self.assertTrue(
            component_util.is_component_state_ok(
                my_component)
            )


class FrontEndTest(unittest.TestCase):
    """
    This test requires ACS running with the testacsproperties CDB and
    the myC cpp container up
    """
    def setUp(self):
        self._my_acs_client = PySimpleClient()
        self._my_acs_client.getLogger().setLevel(logging.CRITICAL)
        self._front_end = FrontEnd(
            RecorderConfig(),
            self._my_acs_client)
        self.__my_component_id = "TEST_PROPERTIES_COMPONENT"

    def test_is_acs_client_ok(self):
        self.assertTrue(self._front_end.is_acs_client_ok)

    def test_update_acs_client(self):
        other_client = PySimpleClient()
        other_client.getLogger().setLevel(logging.CRITICAL)
        self._front_end.update_acs_client(other_client)
        self.assertTrue(self._front_end.is_acs_client_ok)
        self._front_end.start_recording()
        yet_other_client = PySimpleClient()
        yet_other_client.getLogger().setLevel(logging.CRITICAL)
        self._front_end.update_acs_client(yet_other_client)
        self._front_end.stop_recording()

    def test_start_recording(self):
        self._front_end.start_recording()
        self.assertTrue(self._front_end.is_recording)
        self._front_end.stop_recording()

        self._my_acs_client.getComponent(
            self.__my_component_id,
            True)
        self._front_end.start_recording()
        self.assertTrue(self._front_end.is_recording)
        self._front_end.stop_recording()
        self._my_acs_client.releaseComponent(
            self.__my_component_id)

    def test_process_component(self):
        self._my_acs_client.getComponent(
            self.__my_component_id,
            True)

        self._front_end.process_component(
            self.__my_component_id
            )

        self._my_acs_client.releaseComponent(
            self.__my_component_id)

        self.assertRaises(
            CannotAddComponentException,
            self._front_end.process_component,
            "I_DO_NOT_EXIST"
            )

    def test_remove_wrong_components(self):
        self._my_acs_client.getComponent(
            self.__my_component_id,
            True)
        self._front_end.start_recording()

        time.sleep(3)

        self._my_acs_client.releaseComponent(
            self.__my_component_id)

        time.sleep(10)

        self._front_end.stop_recording()

    def tearDown(self):
        self._front_end.cancel()
        self._front_end = None


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(ComponentUtilTest))
suite.addTest(unittest.makeSuite(MoreComponentUtilTest))
suite.addTest(unittest.makeSuite(FrontEndTest))

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
