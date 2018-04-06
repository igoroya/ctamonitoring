#!/usr/bin/env python
__version__ = "$Id: test_util.py 1654 2015-12-22 11:07:42Z igoroya $"
'''
Unit test module for util

This test requires a proper ACS component to run. For that,
the module testacsproperties is used.

@requires: testacsproperties

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_front_end.py 1168 2015-04-13 18:42:27Z igoroya $
@change: $LastChangedDate: 2015-04-13 20:42:27 +0200 (Mon, 13 Apr 2015) $
@change: $LastChangedBy: igoroya $
@requires: unittest
@requires: ctamonitoring.property_recorder.util
@requires: logging
@requires: ctamonitoring.property_recorder.backend
@requires: enum
@requires: ctamonitoring.property_recorder.constants
'''

import unittest
from ctamonitoring.property_recorder.util import (
    PropertyTypeUtil, ComponentUtil, AttributeDecoder, EnumUtil)
from ctamonitoring.property_recorder.frontend_exceptions import (
    UnsupporterPropertyTypeError)
from Acspy.Clients.SimpleClient import PySimpleClient
import logging
from ctamonitoring.property_recorder.backend import property_type
from enum import Enum
from ctamonitoring.property_recorder.constants import DECODE_METHOD


PropertyType = property_type.PropertyType


class PropertyTypeUtilTest(unittest.TestCase):
    '''
    This test requires ACS running with the testacsproperties CDB and
    the myC cpp container up
    '''
    def setUp(self):
        # For this test to work one needs to have ACS up and running and a set 
        # of ACS
        # components in the CDB, as well as proper containers running
        # TODO: Integrate this with TAT or other facility
        # I will assume that ACS is running, with the correct CDB, component
        # and container running

        # set the corresponding ACS CDB
        # os.environ["ACS_CDB"] = "/vagrant/actl/testacsproperties/test"
        # check that the CDB exists
        # print os.environ["ACS_CDB"] +'/CDB'

        # if os.path.isdir(os.environ['ACS_CDB']+'/CDB'):
        #    print "cdb dir found"
        # else:
        #    print "NO cdb dir found"
        #    self.fail("no CDB found, test failed")
        # check if ACS is running. If so, the the test is failed
        # if getManager() is None:
        #    print 'starting ACS'
        #    call(["acsStart", "-v"])
        # else:
        #    self.fail("ACS already running, should be stopped")
        # start the test container
        # Popen(["acsStartContainer", "-cpp", " myC"])
        # sleep to o let the container start
        # time.sleep(10)

        # create a client
        self._my_acs_client = PySimpleClient()
        logger = self._my_acs_client.getLogger()
        logger.setLevel(logging.WARNING)
        # disable annoying output from the tests

    def tearDown(self):
        self._my_acs_client.disconnect()
        # call(["acsStop"])

    def test_get_enum_prop_dict(self):

        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)

        enum_prop = my_component._get_EnumTestROProp()

        decoded = PropertyTypeUtil.get_enum_prop_dict(enum_prop)
        expected_value = {'0': 'STATE1', '1': 'STATE2', '2': 'STATE3'}
        self.assertEqual(expected_value, decoded)

        enum_prop = my_component._get_EnumTestRWProp()

        decoded = PropertyTypeUtil.get_enum_prop_dict(enum_prop)
        expected_value = {'0': 'STATE1', '1': 'STATE2', '2': 'STATE3'}
        self.assertEqual(expected_value, decoded)

        self._my_acs_client.releaseComponent("TEST_PROPERTIES_COMPONENT")

    def test_get_property_type(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT",
            True)

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_EnumTestROProp()._NP_RepositoryId),
            PropertyType.OBJECT
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_EnumTestRWProp()._NP_RepositoryId),
            PropertyType.OBJECT
            )

        PropertyType.OBJECT

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleROProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_floatSeqRWProp()._NP_RepositoryId),
            PropertyType.FLOAT_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longSeqRWProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )
        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongROProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_booleanROProp()._NP_RepositoryId),
            PropertyType.BOOL
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleSeqROProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longLongROProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_patternROProp()._NP_RepositoryId),
            PropertyType.BIT_FIELD
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongRWProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_booleanRWProp()._NP_RepositoryId),
            PropertyType.BOOL
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleSeqRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_patternRWProp()._NP_RepositoryId),
            PropertyType.BIT_FIELD
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongSeqROProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            PropertyTypeUtil.get_property_type,
            my_component._get_booleanSeqROProp()._NP_RepositoryId
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_floatROProp()._NP_RepositoryId),
            PropertyType.FLOAT
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longROProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_stringROProp()._NP_RepositoryId),
            PropertyType.STRING
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongSeqRWProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            PropertyTypeUtil.get_property_type,
            my_component._get_booleanSeqRWProp()._NP_RepositoryId
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_floatRWProp()._NP_RepositoryId),
            PropertyType.FLOAT
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longRWProp()._NP_RepositoryId),
            PropertyType.LONG
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_stringRWProp()._NP_RepositoryId),
            PropertyType.STRING
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_floatSeqROProp()._NP_RepositoryId),
            PropertyType.FLOAT_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_longSeqROProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )

        self.assertEqual(
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongLongROProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )

    def test_is_archive_delta_enabled(self):

        # First test the cases when it should be false
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled(None)
            )
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled(False)
            )
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled("0")
            )
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled("0.0")
            )
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled(0)
            )
        self.assertFalse(
            PropertyTypeUtil.is_archive_delta_enabled(0.0)
            )


class ComponentUtilTest(unittest.TestCase):
    '''
    WRITE

    @TODO: create my own test CDB including the components that I need
    '''
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
            ComponentUtil.is_characteristic_component(my_component)
            )
        # Now check a component that is not characteristic
        my_component2 = self._my_acs_client.getComponent("TIMER1", True)
        self.assertFalse(
            ComponentUtil.is_characteristic_component(my_component2)
            )

    def test_is_python_char_component(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_PYTHON", True)
        self.assertTrue(
            ComponentUtil.is_python_char_component(my_component)
            )
        # Now check a component that is not characteristic

        my_component2 = self._my_acs_client.getComponent(
            "TIMER1", True)

        self.assertRaises(
            AttributeError,
            ComponentUtil.is_python_char_component,
            my_component2
            )

        my_component3 = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)

        self.assertFalse(
            ComponentUtil.is_python_char_component(my_component3)
            )

    def test_is_a_property_recorder_component(self):
        my_component = self._my_acs_client.getComponent(
            "propertyRecorder1", True)
        self.assertTrue(
            ComponentUtil.is_a_property_recorder_component(my_component)
            )
        # Now check a component that is not characteristic
        my_component2 = self._my_acs_client.getComponent("TIMER1", True)
        self.assertFalse(
            ComponentUtil.is_a_property_recorder_component(my_component2)
            )

    def test_is_component_state_ok(self):
        my_component = self._my_acs_client.getComponent(
            "TEST_PROPERTIES_COMPONENT", True)
        self.assertTrue(
            ComponentUtil.is_component_state_ok(
                my_component, "TEST_PROPERTIES_COMPONENT")
            )


class AttributeDecoderTest(unittest.TestCase):

    def test_decode_boolean(self):
        cdb_boolean = 'true'
        self.assertTrue(AttributeDecoder.decode_boolean(cdb_boolean))
        cdb_boolean = 'false'
        self.assertFalse(AttributeDecoder.decode_boolean(cdb_boolean))

    def test_decode_attribute(self):
        a_num = '1'
        a_no_decode = 'hello'
        a_utf_8 = "my_text".encode('utf-8')

        self.assertEqual(
            1,
            AttributeDecoder.decode_attribute(
                a_num,
                DECODE_METHOD.AST_LITERAL
                )
            )

        self.assertEqual(
            1,
            AttributeDecoder.decode_attribute(
                a_num,
                DECODE_METHOD.AST_LITERAL_HYBRID
                )
            )

        self.assertEqual(
            'hello',
            AttributeDecoder.decode_attribute(
                a_no_decode,
                DECODE_METHOD.NONE
                )
            )

        self.assertEqual(
            'hello',
            AttributeDecoder.decode_attribute(
                a_no_decode,
                DECODE_METHOD.AST_LITERAL_HYBRID
                )
            )

        self.assertEqual(
            'my_text',
            AttributeDecoder.decode_attribute(
                a_utf_8,
                DECODE_METHOD.UTF8
                )
            )


class EnumUtilTest(unittest.TestCase):

    def test_to_string(self):
        test_enum = Enum('test_enum', 'DUMMY LOG MYSQL MONGODB')
        self.assertEqual(
            'DUMMY',
            EnumUtil.to_string(test_enum.DUMMY)
            )

    def test_from_string(self):
        test_enum = Enum('test_enum', 'DUMMY LOG MYSQL MONGODB')
        self.assertEqual(
            test_enum.LOG,
            EnumUtil.from_string(test_enum, 'LOG')
            )

        self.assertRaises(
            KeyError,
            EnumUtil.from_string,
            test_enum, 'NOPE')

if __name__ == '__main__':
    unittest.main()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(EnumUtilTest))
    suite.addTest(unittest.makeSuite(AttributeDecoderTest))
    suite.addTest(unittest.makeSuite(PropertyTypeUtilTest))
    suite.addTest(unittest.makeSuite(ComponentUtilTest))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
