__version__ = "$Id$"


'''
Unit test module for test_config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''


import unittest
from ctamonitoring.property_recorder.front_end import (
    ComponentStore,
    ComponentInfo,
    RecorderSpaceObserver,
    FrontEnd)
from ctamonitoring.property_recorder.frontend_exceptions import (
    CannotAddComponentException)

from Acspy.Clients.SimpleClient import PySimpleClient
from ctamonitoring.property_recorder.config import RecorderConfig

import sys
import time
import logging
from StringIO import StringIO


class PrintArgs(object):

    """
    If a call to a method is made, this class prints the name of the method
    and all arguments.

    The out will be sys.stdout is nothing is stated.
    For unit test, StringIO can be used to check that the
    observer is correctly called

    Used to test the ComponentStore
    """

    def __init__(self, out=sys.stdout):
        self.out = out

    def p(self, *args):
        self.out.write(str(self.attr) + ' ' +
                       str(args) + '\n')

    def __getattr__(self, attr):
        self.attr = attr
        return self.p


class ComponentStoreTest(unittest.TestCase):
    one_dict = {1: "one", 2: "two"}
    other_dict = {3: "three", 4: "four"}
    # dict_init(self)
    obs_dict_init = "dict_init"
    obs_dict_create = "dict_create"
    # dict_set(self, key, old value)
    obs_dict_set = "dict_set"
    # dict_del(self, key, old value)
    obs_dict_del = "dict_del"
    # dict_clear(self, old value)
    obs_dict_clear = "dict_clear"
    obs_dict_update = "dict_update"
    obs_dict_setdefault = "dict_setdefault"
    obs_dict_pop = "dict_pop"
    obs_dict_popitem = "dict_popitem"

    def setUp(self):
        self.out = StringIO()
        self.observer = PrintArgs(out=self.out)

    def test_constructor_with_arguments(self):
        self.out.truncate(0)
        d = ComponentStore(self.one_dict, self.observer)
        # When using arguments, the constructor needs to inform the observer
        # that the dict was initialized
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_init + \
            ' (' + str(self.one_dict) + (',)')
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)
        # In Python 2.7 I would use assertIsNotNone but for now we are in 2.6
        self.assertNotEqual(d, None)

    def test_setitem(self):

        d = ComponentStore(observer=self.observer)

        # Set a new item. We need to clear the buffer if the StringIO as well
        self.out.truncate(0)
        d[1] = "one"
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_create + " (1, 'one')"
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)

        # Set a second item
        self.out.truncate(0)
        d[2] = "two"
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_create + " (2, 'two')"
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)

        # Now replace a value
        self.out.truncate(0)
        d[2] = "dos"
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_set + " (2, 'dos', 'two')"
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)

        # Now check the case when

    def test_delitem(self):
        d = ComponentStore(self.one_dict, self.observer)
        self.out.truncate(0)

        del d[2]
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_del + " (2, 'two')"
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)

    def test_clear(self):
        d = ComponentStore(self.one_dict, self.observer)
        self.out.truncate(0)
        d.clear()
        output = self.out.getvalue().strip()
        expected_reaction = self.obs_dict_clear + \
            " ({}, " + str(self.one_dict) + ")"
        # Check that the correct method is issued to the observer
        self.assertEqual(output, expected_reaction)

    def test_update(self):
        d = ComponentStore(self.one_dict, self.observer)

        # Update without replacement
        self.out.truncate(0)
        d.update(self.other_dict)
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_update +
                             " ([(3, 'three'), (4, 'four')], [])"
                             )
        self.assertEqual(output, expected_reaction)

        # Now with a replacement
        self.out.truncate(0)
        d.update({1: "one", 2: "dos"})
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_update +
                             " ([], [(1, 'one', 'one'), (2, 'dos', 'two')])"
                             )
        self.assertEqual(output, expected_reaction)

    def test_setdefault(self):
        d = ComponentStore(self.one_dict, self.observer)

        # Set a default that does not exist
        self.out.truncate(0)
        value = d.setdefault(5, "five")
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_setdefault +
                             " ({1: 'one', 2: 'two', 5: 'five'}, 5, 'five')"
                             )
        self.assertEqual(output, expected_reaction)
        self.assertEqual("five", value)

        # now set one that exists
        value = d.setdefault(5, "cinco")
        self.assertEqual("five", value)

    def test_pop(self):
        d = ComponentStore(self.one_dict, self.observer)

        # Pop an existing value
        self.out.truncate(0)
        value = d.pop(2)
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_pop +
                             " (2, 'two')"
                             )
        self.assertEqual(output, expected_reaction)
        self.assertEqual('two', value)

        # pop a missing value
        value = d.pop(2)
        self.assertEqual(None, value)

    def test_popitem(self):
        d = ComponentStore(self.one_dict, self.observer)

        test_dict = self.one_dict.copy()

        # Pop a value, Python decides
        self.out.truncate(0)
        key, value = d.popitem()
        test_dict.pop(key)

        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_popitem +
                             " (" + str(key) + ", '" + str(value) + "')"
                             )
        self.assertEqual(output, expected_reaction)

        # pop another item
        self.out.truncate(0)
        key, value = d.popitem()
        test_dict.pop(key)

        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_popitem +
                             " (" + ", " + str(key) + ", " + str(value) + ")"
                             )


class RecorderSpaceObserverTest(unittest.TestCase):

    comp_1_info = ComponentInfo(
        'component1_ref', [
            'monitor1', 'monitor2', 'monitor3'])
    comp_2_info = ComponentInfo(
        'component2_ref', [
            'monitor1', 'monito2', 'monitor3'])
    comp_3_info = ComponentInfo(
        'component3_ref', [
            'monitor1', 'monito2', 'monitor3'])
    comp_4_info = ComponentInfo(
        'component4_ref', [
            'monitor1', 'monito2', 'monitor3'])
    comp_3_info_new = ComponentInfo(
        'component3_ref', [
            'monitor1', 'monito2', 'monitor3', 'monito4', 'monitor5'])

    dict_3_element = {
        'comp1': comp_1_info,
        'comp2': comp_2_info,
        'comp3': comp_3_info}
    dict_4_element = {'comp1': comp_1_info, 'comp2': comp_2_info,
                      'comp3': comp_3_info, 'comp4': comp_4_info}

    max_comps = 3
    max_props = 10

    def test_dict_init(self):

        # Test the insertion of a dictionary that does not fill the limit
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        self.assertEqual(obs._max_components, self.max_comps)
        self.assertEqual(obs._max_properties, self.max_props)
        self.assertEqual(obs._actual_components, 3)
        self.assertEqual(obs._actual_properties, 9)
        self.assertEqual(obs.isFull, False)

        # Test the insertion of a dictionary that fills the limit
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)
        self.assertEqual(obs.isFull, True)

    def test_dict_create(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        # check that adding an element makes the recorder full
        obs.dict_create('comp4', self.comp_4_info)
        self.assertEqual(obs.isFull, True)

    def test_dict_set(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        # check that adding an element makes the recorder full
        obs.dict_set('comp3', self.comp_3_info_new, self.comp_3_info)
        self.assertEqual(obs.isFull, True)

    def test_dict_del(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        # check that adding an element makes the recorder full
        obs.dict_del('comp4', self.comp_4_info)
        self.assertEqual(obs.isFull, False)

    def test_dict_clear(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        # check that adding an element makes the recorder full
        empty_dict = {}
        obs.dict_clear(empty_dict, self.comp_4_info)

        self.assertEqual(obs.isFull, False)
        self.assertEqual(obs._actual_components, 0)
        self.assertEqual(obs._actual_properties, 0)

    def test_dict_update(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        replaced_values = [('comp3', self.comp_3_info_new, self.comp_3_info)]

        new_values = []

        obs.dict_update(new_values, replaced_values)
        self.assertEqual(obs.isFull, True)

        replaced_values = [('comp3', self.comp_3_info, self.comp_3_info_new)]

        obs.dict_update(new_values, replaced_values)
        self.assertEqual(obs.isFull, False)

        new_values = [('comp4', self.comp_4_info)]
        replaced_values = []
        obs.dict_update(new_values, replaced_values)

        self.assertEqual(obs.isFull, True)

    def test_dict_setdefault(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        self.assertRaises(
            NotImplementedError,
            obs.dict_setdefault,
            "a",
            "a",
            "a")

    def test_dict_pop(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        obs.dict_pop('comp4', self.comp_4_info)
        self.assertEqual(obs.isFull, False)

    def test_dict_popitem(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        obs.dict_popitem('comp4', self.comp_4_info)
        self.assertEqual(obs.isFull, False)


class FrontEndTest(unittest.TestCase):
    '''
    This test requires ACS running with the testacsproperties CDB and
    the myC cpp container up
    '''
    def setUp(self):
        self.__my_acs_client = PySimpleClient()
        self.__my_acs_client.getLogger().setLevel(logging.CRITICAL)
        self.__front_end = FrontEnd(
            RecorderConfig(),
            self.__my_acs_client)
        self.__my_component_id = "TEST_PROPERTIES_COMPONENT"

    def test_is_acs_client_ok(self):
        self.assertTrue(self.__front_end.is_acs_client_ok)

    def test_update_acs_client(self):
        other_client = PySimpleClient()
        other_client.getLogger().setLevel(logging.CRITICAL)
        self.__front_end.update_acs_client(other_client)
        self.assertTrue(self.__front_end.is_acs_client_ok)
        self.__front_end.start_recording()
        yet_other_client = PySimpleClient()
        yet_other_client.getLogger().setLevel(logging.CRITICAL)
        self.__front_end.update_acs_client(yet_other_client)
        self.__front_end.stop_recording()

    def test_start_recording(self):
        self.__front_end.start_recording()
        self.assertTrue(self.__front_end.is_recording)
        self.__front_end.stop_recording()

        self.__my_acs_client.getComponent(
            self.__my_component_id,
            True)
        self.__front_end.start_recording()
        self.assertTrue(self.__front_end.is_recording)
        self.__front_end.stop_recording()
        self.__my_acs_client.releaseComponent(
            self.__my_component_id)

    def test_process_component(self):
        self.__my_acs_client.getComponent(
            self.__my_component_id,
            True)

        self.__front_end.process_component(
            self.__my_component_id
            )

        self.__my_acs_client.releaseComponent(
            self.__my_component_id)

        self.assertRaises(
            CannotAddComponentException,
            self.__front_end.process_component,
            "I_DO_NOT_EXIST"
            )

    def test_remove_wrong_components(self):
        self.__my_acs_client.getComponent(
            self.__my_component_id,
            True)
        self.__front_end.start_recording()

        time.sleep(3)

        self.__my_acs_client.releaseComponent(
            self.__my_component_id)

        time.sleep(10)

        self.__front_end.stop_recording()

    def tearDown(self):
        self.__front_end.cancel()
        self.__front_end = None

if __name__ == '__main__':
    unittest.main()
