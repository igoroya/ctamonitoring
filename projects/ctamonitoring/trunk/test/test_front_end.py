#!/usr/bin/env python
"""
Unit test module for test_config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
import unittest
import collections
import sys
import time
import logging
from StringIO import StringIO
from mock import Mock, MagicMock, create_autospec
from CORBA import UNKNOWN
from ACS import _objref_ROuLong  # @UnresolvedImport
from Acspy.Clients.SimpleClient import PySimpleClient
from ctamonitoring.property_recorder.config import RecorderConfig, BACKEND_TYPE
from ctamonitoring.property_recorder.backend.dummy.registry import Buffer
from ctamonitoring.property_recorder.constants import ROULONG_NP_REP_ID
from ctamonitoring.property_recorder.constants import PROPERTY_ATTRIBUTES
from ctamonitoring.property_recorder.callbacks import CBFactory
from ctamonitoring.property_recorder.front_end import (
    ComponentStore,
    ComponentInfo,
    RecorderSpaceObserver,
    FrontEnd)




__version__ = "$Id$"


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
        self.assertEqual(output, expected_reaction)
        self.assertIsNotNone(d)

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
                             " ([(3, 'three'), (4, 'four')], [])")
        self.assertEqual(output, expected_reaction)

        # Now with a replacement
        self.out.truncate(0)
        d.update({1: "one", 2: "dos"})
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_update +
                             " ([], [(1, 'one', 'one'), (2, 'dos', 'two')])")
        self.assertEqual(output, expected_reaction)

    def test_setdefault(self):
        d = ComponentStore(self.one_dict, self.observer)

        # Set a default that does not exist
        self.out.truncate(0)
        value = d.setdefault(5, "five")
        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_setdefault +
                             " ({1: 'one', 2: 'two', 5: 'five'}, 5, 'five')")
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
                             " (2, 'two')")
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
                             " (" + str(key) + ", '" + str(value) + "')")
        self.assertEqual(output, expected_reaction)

        # pop another item
        self.out.truncate(0)
        key, value = d.popitem()
        test_dict.pop(key)

        output = self.out.getvalue().strip()
        expected_reaction = (self.obs_dict_popitem +
                             " (" + ", " + str(key) + ", " + str(value) + ")")


class RecorderSpaceObserverTest(unittest.TestCase):

    comp_1_info = ComponentInfo(
        'component1_ref', 1, [
            'monitor1', 'monitor2', 'monitor3'])
    comp_2_info = ComponentInfo(
        'component2_ref', 1, [
            'monitor1', 'monito2', 'monitor3'])
    comp_3_info = ComponentInfo(
        'component3_ref', 1, [
            'monitor1', 'monito2', 'monitor3'])
    comp_4_info = ComponentInfo(
        'component4_ref', 1, [
            'monitor1', 'monito2', 'monitor3'])
    comp_3_info_new = ComponentInfo(
        'component3_ref', 1, [
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
        self.assertEqual(obs.if_full, False)

        # Test the insertion of a dictionary that fills the limit
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)
        self.assertEqual(obs.if_full, True)

    def test_dict_create(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        # check that adding an element makes the recorder full
        obs.dict_create('comp4', self.comp_4_info)
        self.assertEqual(obs.if_full, True)

    def test_dict_set(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        # check that adding an element makes the recorder full
        obs.dict_set('comp3', self.comp_3_info_new, self.comp_3_info)
        self.assertEqual(obs.if_full, True)

    def test_dict_del(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        # check that adding an element makes the recorder full
        obs.dict_del('comp4', self.comp_4_info)
        self.assertEqual(obs.if_full, False)

    def test_dict_clear(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        # check that adding an element makes the recorder full
        empty_dict = {}
        obs.dict_clear(empty_dict, self.comp_4_info)

        self.assertEqual(obs.if_full, False)
        self.assertEqual(obs._actual_components, 0)
        self.assertEqual(obs._actual_properties, 0)

    def test_dict_update(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_3_element)

        replaced_values = [('comp3', self.comp_3_info_new, self.comp_3_info)]

        new_values = []

        obs.dict_update(new_values, replaced_values)
        self.assertEqual(obs.if_full, True)

        replaced_values = [('comp3', self.comp_3_info, self.comp_3_info_new)]

        obs.dict_update(new_values, replaced_values)
        self.assertEqual(obs.if_full, False)

        new_values = [('comp4', self.comp_4_info)]
        replaced_values = []
        obs.dict_update(new_values, replaced_values)

        self.assertEqual(obs.if_full, True)

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
        self.assertEqual(obs.if_full, False)

    def test_dict_popitem(self):
        obs = RecorderSpaceObserver(self.max_comps, self.max_props)
        obs.dict_init(self.dict_4_element)

        obs.dict_popitem('comp4', self.comp_4_info)
        self.assertEqual(obs.if_full, False)


class FrontEndTest(unittest.TestCase):

    '''
    This test requires ACS running with the testacsproperties CDB and
    the myC cpp container up
    '''

    def setUp(self):

        self._my_acs_client = create_autospec(PySimpleClient)
        self._logger = logging.Logger("test_logger")
        self._logger.setLevel(logging.CRITICAL)
        #self._my_acs_client.getLogger = MagicMock(return_value=self._logger)
        config = RecorderConfig()
        config.backend_type = BACKEND_TYPE.DUMMY
        self._front_end = FrontEnd(
            config,
            self._my_acs_client)
        self._my_component_id = "TEST_PROPERTIES_COMPONENT"

    def test_is_acs_client_ok(self):
        self.assertTrue(self._front_end.is_acs_client_ok)

    def test_update_acs_client(self):
        other_client = create_autospec(PySimpleClient)
        other_client.getLogger().setLevel(logging.CRITICAL)
        self._front_end.update_acs_client(other_client)
        self.assertTrue(self._front_end.is_acs_client_ok)
        self._front_end.start_recording()
        yet_other_client = create_autospec(PySimpleClient)
        yet_other_client.getLogger().setLevel(logging.CRITICAL)
        self._front_end.update_acs_client(yet_other_client)
        self._front_end.stop_recording()

    def test_start_recording(self):
        self._front_end.start_recording()
        self.assertTrue(self._front_end.is_recording)
        self._front_end.stop_recording()

        self._my_acs_client.getComponent(
            self._my_component_id,
            True)
        self._front_end.start_recording()
        self.assertTrue(self._front_end.is_recording)
        self._front_end.stop_recording()
        self._my_acs_client.releaseComponent(
            self._my_component_id)

    def test_get_acs_property(self):
        chars = 'my_prop'
        attr = '_get_' + chars + '.return_value'
        out = 17
        attrs = {attr: out}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertEqual(
            out, self._front_end._get_acs_property(mock_component, chars))

        chars = 'my_bad_prop'
        attr = '_get_' + chars + '.side_effect'
        attrs = {attr: UNKNOWN}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertRaises(
            ValueError, self._front_end._get_acs_property, mock_component, chars)

    def test_remove_monitors(self):
        mock_comp_info = ComponentInfo(
            Mock(), Mock(), [Mock(), Mock(), Mock()])
        self._front_end._remove_monitors(mock_comp_info)

    def test_release_all_comps(self):
        self._front_end._components = {"a": ComponentInfo(Mock(), Mock(), [Mock(), Mock(
        ), Mock()]), "b": ComponentInfo(Mock(), Mock(), [Mock(), Mock(), Mock()])}
        self._front_end._release_all_comps()
        # TODO: Add test here

    def test_remove_wrong_components(self):
        self._front_end._components = {
            "a": ComponentInfo(Mock(), 1, Mock()), "b": ComponentInfo(Mock(), 2, Mock())}
        self._front_end._remove_wrong_components()
        self.assertEqual(0, len(self._front_end._components))

    def test_is_id_changed(self):
        name = "a"
        comp_info = ComponentInfo(Mock(), 1, Mock())
        self._front_end._components = {name: comp_info}
        self.assertFalse(self._front_end._is_id_changed(name, comp_info))

        # This trick could be replaced with a context manager
        old_method = self._my_acs_client.availableComponents

        def side_effect_availableComponents(value):
            values = collections.namedtuple('a', 'h', verbose=False)
            my_value = values(h='5')
            return [my_value]
        self._my_acs_client.availableComponents = MagicMock(
            side_effect=side_effect_availableComponents)
        self.assertTrue(self._front_end._is_id_changed(name, comp_info))
        self._my_acs_client.availableComponents = old_method
        self._front_end._components = {}

    def test_scan_for_component(self):
        self._front_end.recoder_space.if_full = True
        self._front_end._scan_for_components()
        self._front_end.recoder_space.if_full = False

    def test_loop_components_and_activate(self):
        activated_components = []
        self._front_end._loop_components_and_process(activated_components)

        activated_components = ['one', 'two']

        def side_effect_process(value):
            pass

        self._front_end.recorder_config.is_include_mode = False
        orig_process_component = self._front_end.process_component
        self._front_end.process_component = MagicMock(
            side_effect=side_effect_process)
        activated_components = ['one', 'two']
        self._front_end._loop_components_and_process(activated_components)

        self._front_end.recorder_config.is_include_mode = True
        self._front_end._loop_components_and_process(activated_components)

        self._front_end.process_component = orig_process_component

    def test_create_monitor(self):
        prop = _objref_ROuLong(None)
        prop._get_name = MagicMock(
            return_value="MockProperty"
        )

        monitor = Mock()
        attrs = {'name': 'IAmMonitor',
                 'set_timer_trigger.return_value': None,
                 'set_value_percent_trigger.return_value': None}
        monitor.configure_mock(**attrs)

        prop.create_monitor = MagicMock(
            return_value=monitor
        )

        cb = CBFactory.get_callback(prop, "", Buffer(),
                                    self._logger)
        my_buffer = Mock()

        property_attributes = {k.name: 5 for k in PROPERTY_ATTRIBUTES}

        monitor = self._front_end._create_monitor(
            prop, property_attributes, my_buffer)

        self.assertEqual('IAmMonitor', monitor.name)

    def test_create_buffer(self):
        acs_property = _objref_ROuLong(None)
        acs_property._get_name = MagicMock(
            return_value="MockProperty"
        )
        property_attributes = {k.name: 5 for k in PROPERTY_ATTRIBUTES}
        component_reference = Mock()
        attrs = {'_get_name.return_value': 'MockProperty',
                 'component_reference._NP_RepositoryId': ROULONG_NP_REP_ID}
        component_reference.configure_mock(**attrs)

        my_buffer = self._front_end._create_buffer(
            acs_property,
            property_attributes,
            component_reference)

        self.assertTrue(my_buffer)

    def tearDown(self):
        self._front_end.cancel()
        self._front_end = None


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ComponentStoreTest))
    suite.addTest(unittest.makeSuite(RecorderSpaceObserverTest))
    suite.addTest(unittest.makeSuite(FrontEndTest))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
