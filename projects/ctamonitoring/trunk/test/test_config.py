#!/usr/bin/env python
__version__ = "$Id$"
'''
Unit test module for config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: unittest
@requires: ctamonitoring.property_recorder.config
@requires: ctamonitoring.property_recorder.config
@requires: mock
@requires: CORBA
'''
import unittest
from ctamonitoring.property_recorder.config import (
    RecorderConfig, PropertyAttributeHandler)
from ctamonitoring.property_recorder.config import BACKEND_TYPE
from ctamonitoring.property_recorder.constants import (
    ATTRIBUTE_INFO, DECODE_METHOD)
from mock import (create_autospec, MagicMock)
from ACS import _objref_ROdouble  # @UnresolvedImport
from CORBA import (Any, TC_string)  # @UnresolvedImport
from xml.dom.minidom import Element
from ACS import NoSuchCharacteristic  # @UnresolvedImport

__version__ = '$Id$'


class Defaults:
    '''
    Defauls values for the unir test
    '''
    default_timer_trigger = 60.0
    max_comps = 100
    max_props = 1000
    checking_period = 10  # seconds
    backend_type = BACKEND_TYPE.DUMMY
    components = set()
    backend_config = None
    is_include_mode = False


class RecorderConfigTest(unittest.TestCase):
    a_long = 150L
    a_float = 0.8
    a_neg_long = -1L
    a_string = 'a'
    a_string_set = set(['a', 'b'])
    a_hybrid_set = set(['a', 1])
    a_backend_type = BACKEND_TYPE.MONGODB

    def setUp(self):
        self.recoder_config = RecorderConfig()

    def test_default_timer_trigger(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.default_timer_trigger,
            Defaults.default_timer_trigger)

        self.recoder_config.default_timer_trigger = self.a_float
        self.assertEqual(
            self.recoder_config.default_timer_trigger,
            self.a_float)

        self.assertRaises(
            ValueError, setattr,
            self.recoder_config,
            'default_timer_trigger',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'default_timer_trigger',
            self.a_string)

    def test_max_comps(self):
        self.assertEqual(self.recoder_config.max_comps, Defaults.max_comps)

        self.recoder_config.max_comps = self.a_long
        self.assertEqual(self.recoder_config.max_comps, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_string)

    def test_max_props(self):
        # check the default value
        self.assertEqual(self.recoder_config.max_props, Defaults.max_props)

        self.recoder_config.max_props = self.a_long
        self.assertEqual(self.recoder_config.max_props, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_string)

    def test_checking_period(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.checking_period,
            Defaults.checking_period)

        self.recoder_config.checking_period = self.a_long
        self.assertEqual(self.recoder_config.checking_period, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'checking_period',
            self.a_neg_long)
        self.assertRaises(
            ValueError, setattr,
            self.recoder_config,
            'checking_period',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'checking_period',
            self.a_string)

    def test_backend_type(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.backend_type,
            Defaults.backend_type)

        self.recoder_config.backend_type = self.a_backend_type
        self.assertEqual(self.recoder_config.backend_type, self.a_backend_type)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'backend_type',
            self.a_string)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'backend_type',
            self.a_long)

    def test_is_include_mode(self):
        self.recoder_config.is_include_mode = True
        self.assertTrue(self.recoder_config.is_include_mode)

        self.recoder_config.is_include_mode = False
        self.assertFalse(self.recoder_config.is_include_mode)
        # should raise an exception for other data types
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_long)
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_float)
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_string)

    def test_components(self):

        self.assertRaises(
            NotImplementedError,
            setattr,
            self.recoder_config,
            'components',
            self.a_string_set)

        self.recoder_config.set_components(self.a_string_set)
        self.assertEquals(self.recoder_config.components, self.a_string_set)

        self.assertRaises(
            TypeError,
            self.recoder_config.set_components,
            self.a_float)

        self.assertRaises(
            TypeError,
            self.recoder_config.set_components,
            self.a_hybrid_set)


class PropertyAttributeHandlerTest(unittest.TestCase):
    def setUp(self):
        self.mocked_property = create_autospec(_objref_ROdouble)
        self.mocked_property.find_characteristic = MagicMock(
            side_effect=self.__side_effect_find_characteristic
            )
        self.mocked_property.get_characteristic_by_name = MagicMock(
            side_effect=self.__side_effect_get_characteristic
            )
        self.mocked_property._get_name = MagicMock(
            return_value="MockProperty"
            )

        self.mocked_cdb = create_autospec(Element)
        self.mocked_cdb.getAttribute = MagicMock(
            side_effect=self.__side_effect_cdb_xml)
        self.mocked_cdb.nodeName = MagicMock(
            return_value="MockProperty"
            )

    def __side_effect_find_characteristic(self, value):
        '''
        Needed to mock the CDB behavior
        '''
        if value is "default_timer_trig":
            return ['default_timer_trig']
        elif value is "default_value":
            return ['default_value']
        elif value is "units":
            return ['units']
        else:
            return []

    def __side_effect_get_characteristic(self, value):
        '''
        Needed to mock the CDB behavior
        '''
        if value is "default_timer_trig":
            return Any(TC_string, '10.0')
        elif value is "default_value":
            raise NoSuchCharacteristic("testing", "default_value")
            # failing intentionally at default_value
        elif value is "units":
            return Any(TC_string, 'celsius')
        else:
            raise NoSuchCharacteristic("testing", "testing")

    def __side_effect_cdb_xml(self, value):
        '''
        Needed to mock the CDB behavior
        '''
        if value is "default_timer_trig":
            return "15.0"
        elif value is "default_value":
            return "22.0"
        elif value is "units":
            return "celsius"
        else:
            return None

    def test_get_prop_attribs_cdb(self):
        attribs = PropertyAttributeHandler.get_prop_attribs_cdb(
            self.mocked_property)
        self.assertIsInstance(
            attribs,
            dict)
        self.assertEqual(attribs['default_timer_trig'], 10)
        self.assertEqual(attribs['default_value'], None)
        self.assertEqual(attribs['units'], "celsius")

    def test_get_cdb_entry(self):
        bad_attribute = ATTRIBUTE_INFO(
            'i_am_bad', DECODE_METHOD.AST_LITERAL,
            False, None)
        self.assertEqual(
            None,
            PropertyAttributeHandler._get_cdb_entry(
                bad_attribute, self.mocked_property))

    def test_get_prop_attribs_cdb_xml(self):
        attribs = PropertyAttributeHandler.get_prop_attribs_cdb_xml(
            self.mocked_cdb)
        self.assertIsInstance(
            attribs,
            dict)
        self.assertEqual(attribs['default_timer_trig'], 15.0)

    def test_process_attribute(self):
        '''
        Test to decode attributes that have problems
        '''
        good_atribute = ATTRIBUTE_INFO(
            'default_timer_trig',
            DECODE_METHOD.AST_LITERAL, True, None)
        synomim_atribute = ATTRIBUTE_INFO(
            'default_timer_trig',
            DECODE_METHOD.NONE, True, ['yes', 'true'])
        good_value = "1.1"
        negative_value = "-1.2"
        true_ok = "true"
        false_ok = "false"
        wrong_type = "nah"
        malformed_1 = 1.1
        malformed_2 = True
        synonym_true = "yes"
        synonym_bad = "plof"

        self.assertEqual(PropertyAttributeHandler._process_attribute(
            good_atribute, good_value), 1.1)
        self.assertEqual(PropertyAttributeHandler._process_attribute(
            good_atribute, negative_value), None)
        self.assertEqual(PropertyAttributeHandler._process_attribute(
            good_atribute, wrong_type), None)
        self.assertEqual(PropertyAttributeHandler._process_attribute(
            good_atribute, malformed_1), None)
        self.assertEqual(PropertyAttributeHandler._process_attribute(
            good_atribute, malformed_2), None)
        self.assertTrue(PropertyAttributeHandler._process_attribute(
            good_atribute, true_ok))
        self.assertFalse(PropertyAttributeHandler._process_attribute(
            good_atribute, false_ok))
        self.assertTrue(PropertyAttributeHandler._process_attribute(
            synomim_atribute, synonym_true))
        self.assertFalse(PropertyAttributeHandler._process_attribute(
            synomim_atribute, synonym_bad))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RecorderConfigTest))
    suite.addTest(unittest.makeSuite(PropertyAttributeHandlerTest))
    return suite


if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
