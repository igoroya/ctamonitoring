#!/usr/bin/env python
__version__ = "$Id$"

'''
Unit test module for test_config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: unittest
@requires: logging
@requires: ctamonitoring.property_recorder.config
@requires: ctamonitoring.property_recorder.standalone_recorder
@requires: ctamonitoring.property_recorder.test_config
@requires: contextlib
@requires: StringIO
@requires: sys
@requires: time
'''


import unittest
import logging
from ctamonitoring.property_recorder.config import (
    BACKEND_TYPE, RecorderConfig)
from ctamonitoring.property_recorder.standalone_recorder import (
    RecorderParser, StandaloneRecorder)
from ctamonitoring.property_recorder.front_end import FrontEnd
from ctamonitoring.property_recorder.test_config import Defaults
from Acspy.Clients.SimpleClient import PySimpleClient
from contextlib import contextmanager
from StringIO import StringIO
import sys
from mock import create_autospec

logging.basicConfig()


@contextmanager
def capture_sys_output():
    '''
    Prevents the standard output to show up in the console
    in certain tests.
    '''
    capture_out, capture_err = StringIO(), StringIO()
    current_out, current_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = capture_out, capture_err
        yield capture_out, capture_err
    finally:
        sys.stdout, sys.stderr = current_out, current_err


class MockedStandaloneRecorder(StandaloneRecorder):
    '''
    Mock a standalone recorder to make the unit test without requiring ACS up

    We mock the ACS Python client, the frontend, and use the standard
    logger instead of the ACS logger.
    '''
    def _setup_acs_client(self):
        self._my_acs_client = create_autospec(PySimpleClient)
        self._logger = logging.Logger("test_logger")
        self._logger.setLevel(self._verbosity)

    def _setup_front_end(self):
        self._front_end = FrontEnd(
            self._recorder_config,
            self._my_acs_client)


class StandaloneRecorderTest(unittest.TestCase):
    def setUp(self):
        recorder_config = RecorderConfig()
        self.recorder = MockedStandaloneRecorder(
            recorder_config, logging.CRITICAL)

    def test_make_new_acs_client(self):
        self.recorder.make_new_acs_client()
        self.assertTrue(self.recorder.is_acs_client_ok())

    def tests_start(self):
        self.recorder.start()
        self.recorder.stop()

    def tests_stop(self):
        self.recorder.stop()

    def test_print_config(self):
        self.recorder.print_config()

    def test_close(self):
        self.recorder.close()
        self.assertRaises(RuntimeError, self.recorder.start)
        self.assertRaises(RuntimeError, self.recorder.stop)


class RecorderParserTest(unittest.TestCase):

    def setUp(self):
        # Values to be inserted
        self.default_timer_trigger = 50
        self.max_comps = 80
        self.max_props = 300
        self.checking_period = 7  # seconds
        self.backend_type = BACKEND_TYPE.MONGODB
        self.backend_config = {'database': 'ctamonitoring'}
        self.is_include_mode = True
        self.components = set(['a', 'b'])

        self.full_command_line_input = [
            "--default_timer_trigger", "50",
            "--max_comps", "80",
            "--max_props", "300",
            "--checking_period", "7",
            "--backend_type", "MONGODB",
            "--backend_config", "{'database': 'ctamonitoring'}",
            "--include_mode",
            "--component_list", "['a', 'b']"]

        self.verbose_command_line_input = ["-v"]
        self.very_verbose_command_line_input = ["-vv"]

        self.bad_component_list_input = [
            "--component_list", "0"]
        self.bad_backend_input = [
            "--backend_type", "WRONG"]
        self.bad_backend_config_input = [
            "--backend_config", "WRONG"]

    def test_full_get_config(self):
        '''
        Test when providing the full list options in command line
        '''
        recoder_parser = RecorderParser(self.full_command_line_input)

        recorder_config = recoder_parser.get_config()

        self.assertEqual(self.default_timer_trigger,
                         recorder_config.default_timer_trigger)
        self.assertEqual(self.max_comps, recorder_config.max_comps)
        self.assertEqual(self.max_props, recorder_config.max_props)
        self.assertEqual(self.checking_period, recorder_config.checking_period)
        self.assertEqual(self.backend_type, recorder_config.backend_type)
        self.assertEqual(self.backend_config, recorder_config.backend_config)
        self.assertEqual(self.is_include_mode, recorder_config.is_include_mode)
        self.assertEqual(self.components, recorder_config.components)

    def test_empty_get_config(self):
        '''
        Test when providing the full list options in command line
        '''
        recoder_parser = RecorderParser()

        recorder_config = recoder_parser.get_config()

        self.assertEqual(Defaults.default_timer_trigger,
                         recorder_config.default_timer_trigger)
        self.assertEqual(Defaults.max_comps, recorder_config.max_comps)
        self.assertEqual(Defaults.max_props, recorder_config.max_props)
        self.assertEqual(Defaults.checking_period,
                         recorder_config.checking_period)
        self.assertEqual(Defaults.backend_type, recorder_config.backend_type)
        self.assertEqual(Defaults.backend_config,
                         recorder_config.backend_config)
        self.assertEqual(Defaults.is_include_mode,
                         recorder_config.is_include_mode)
        self.assertEqual(Defaults.components, recorder_config.components)

    def test_get_verbosity(self):
        '''
        Check if the verbosity level is loaded correctly
        '''
        recoder_parser = RecorderParser(self.full_command_line_input)
        self.assertEqual(logging.INFO, recoder_parser.get_verbosity())

        recoder_parser = RecorderParser(self.verbose_command_line_input)
        self.assertEqual(logging.DEBUG, recoder_parser.get_verbosity())

        recoder_parser = RecorderParser(self.very_verbose_command_line_input)
        self.assertEqual(logging.NOTSET, recoder_parser.get_verbosity())

    def test_bad_component_action(self):
        # The lines below prevent to show in the console the usual text
        # output from argparse during the unit test
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (sys.stdout, sys.stderr):
                RecorderParser(self.bad_component_list_input)

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)

    def test_bad_valid_backend_action(self):
        # The lines below prevent to show in the console the usual text
        # output from argparse during the unit test
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (sys.stdout, sys.stderr):
                RecorderParser(self.bad_backend_input)

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)

    def test_bad_backend_config_action(self):
        # The lines below prevent to show in the console the usual text
        # output from argparse during the unit test
        with self.assertRaises(SystemExit) as cm:
            with capture_sys_output() as (sys.stdout, sys.stderr):
                RecorderParser(self.bad_backend_config_input)

        exit_exception = cm.exception
        self.assertEqual(exit_exception.code, 2)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StandaloneRecorderTest))
    suite.addTest(unittest.makeSuite(RecorderParserTest))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
