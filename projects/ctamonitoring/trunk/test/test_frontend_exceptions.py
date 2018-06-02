#!/usr/bin/env python
"""
Unit test module for frontend exceptions

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_frontend_exceptions.py 2096 2018-05-23 17:16:11Z igoroya $
@change: $LastChangedDate: 2018-05-23 19:16:11 +0200 (Wed, 23 May 2018) $
@change: $LastChangedBy: igoroya $
"""
import unittest
from ctamonitoring.property_recorder import frontend_exceptions

__version__ = "$Id: test_frontend_exceptions.py 2096 2018-05-23 17:16:11Z igoroya $"


class TestFrontEndExceptions(unittest.TestCase):


    def test_component_not_found(self):
        comp_id = "one"
        text = "I fail"
        error = frontend_exceptions.ComponentNotFoundError(comp_id, text)
        expected = "component, " + comp_id + " not found: " + text
        self.assertEqual(expected, str(error))


    def test_cannot_add_component(self):
        comp_id = "one"
        text = "I don't go"
        error = frontend_exceptions.CannotAddComponentException(comp_id, text)
        expected = "component, " + comp_id + " cannot be added: " + text
        self.assertEqual(expected, str(error))

    def test_wrong_component_state(self):
        comp_id = "one"
        text = "I am not good"
        state = "ILL"
        error = frontend_exceptions.WrongComponentStateError(comp_id, state, text)
        expected = "component, " + comp_id + " found in wrong state: " + state + ": " + text
        self.assertEqual(expected, str(error))

    def test_unsupporter_property_type(self):
        prop_type = "nah"
        text = "I am not fitting here"
        error = frontend_exceptions.UnsupporterPropertyTypeError(prop_type, text)
        expected = "Property type: " + prop_type + " is not supported: " + text
        self.assertEqual(expected, str(error))


    def test_bad_cdb_recorder_config(self):
        exception = Exception()
        cdb_entry_id = "my entry"
        text = "I am bad"
        error = frontend_exceptions.BadCdbRecorderConfig(exception, cdb_entry_id, text)
        expected = str(exception)+ ": The entry for " + cdb_entry_id + " is not correct in the component CDB: " + text
        self.assertEqual(expected, str(error))
    
    def test_acs_is_down(self):
        text = "I am down"
        error = frontend_exceptions.AcsIsDownError(text)
        expected = "ACS is in a wrong state: " + text
        self.assertEqual(expected, str(error))
    

if __name__ == '__main__':
    unittest.main()


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestFrontEndExceptions))



if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
