
"""
An application version of the property recorder

This is a version of the property recorder that is run as
a stand-alone application and not as an ACS component.
(see ComponentRecorder.py for the component version)

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: ast
@requires: logging
@requires: argparse
@requires: pprint
@requires: time
@requires: Acspy.Clients.SimpleClient
@requires: ctamonitoring.property_recorder.config
@requires: ctamonitoring.property_recorder.front_end
@requires: ctamonitoring.property_recorder.util
@requires: ACSErrTypeCommonImpl
"""

import logging
import argparse
import ast
import pprint
import time
from Acspy.Clients.SimpleClient import PySimpleClient
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.front_end import FrontEnd
from ctamonitoring.property_recorder.config import BACKEND_TYPE
from ctamonitoring.property_recorder.util import enum_util
from ACSErrTypeCommonImpl import CORBAProblemExImpl

__version__ = "$Id$"

CLIENT_REFRESH_TIME_SEC = 10


class StandaloneRecorder(object):
    """
    A property recorder that works as an stand-alone application

    """
    def __init__(self, recorder_config, verbosity):
        '''
        Ctor

        @param recorder_config: the configuration of the recorder
        @type recorder_config: RecorderConfig
        @param verbosity: the verbosity level
        (logging.WARNING, logging.DEBUG, etc) of the logger
        @type verbosity: int
        '''
        self._verbosity = verbosity
        self._recorder_config = recorder_config

        self._setup_acs_client()
        self._setup_front_end()
        self.__canceled = False

        self._logger.info('Property recorder up')

    def _setup_acs_client(self):
        self._my_acs_client = PySimpleClient()
        self._logger = self._my_acs_client.getLogger()
        self._logger.setLevel(self._verbosity)

    def _setup_front_end(self):
        self._front_end = FrontEnd(
            self._recorder_config,
            self._my_acs_client)

    def make_new_acs_client(self):
        '''
        Will make a new ACS client and replace the existing one

        To be used to recover from ACS restarts.
        @raise CORBAProblemExImpl: if the client cannot be created.
        '''
        self._setup_acs_client()
        self._front_end.update_acs_client(self._my_acs_client)

    def start(self):
        '''
        The property recorded will start to record properties

        @raises RuntimeError: if the recorder is cancelled
        '''
        if self.__canceled:
            raise RuntimeError("The recorded is cancelled")

        self._front_end.start_recording()
        self._logger.info('Recording start')

    def stop(self):
        '''
        The property recorded will stop to record properties

        All the monitors are stopped, the components are unregistered
        @raises RuntimeError: if the recorder is cancelled
        '''
        if self.__canceled:
            raise RuntimeError("The recorded is cancelled")
        self._front_end.stop_recording()
        self._logger.info('Recording stop')

    def close(self):
        '''
        Closes the property recorder, ready to be destroyed

        All the resources will be freed and the connection with
        ACS closed. The recorder will be cancelled from now on,
        Meaning that the recorder is not anymore usable and
        is ready to be destroyed
        '''
        if not self.__canceled:
            self._logger.info('Switching off property recorder')
            self.stop()
            self._front_end.cancel()
            self._front_end = None
            self._recorder_config = None
            self._my_acs_client.disconnect()
            self._my_acs_client = None
            self.__canceled = True

    def is_acs_client_ok(self):
        '''
        Checks if the ACS client is OK or not.

        When not OK, this typically means that ACS is
        down. This lets the client know when a new client should be created
        @return: if the client is OK or not
        @rtype: bool
        '''
        return self._front_end.is_acs_client_ok

    def print_config(self):
        '''
        Prints into the logger the existing configuration
        '''
        self._logger.debug(
            'Property Recorder Configuration'
            '\n--------------------------------------\n' +
            pprint.pformat(vars(self._recorder_config)) +
            '\n--------------------------------------')


class ConfigBackendAction(argparse.Action):
    """
    Action to interpret the user input for the configuration of backend
    """
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            backend_config_decoded = ast.literal_eval(values)
            assert isinstance(backend_config_decoded, dict)
        except (SyntaxError, ValueError, TypeError, AssertionError):
            parser.error("'%s' is not a valid backend config" % values)

        setattr(namespace, self.dest, backend_config_decoded)


class ValidBackendAction(argparse.Action):
    """
    Action to interpret the user input for the type of backend
    """
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            backend_type = enum_util.from_string(BACKEND_TYPE, values)
        except KeyError:
            allowed = str([e.name for e in BACKEND_TYPE])
            parser.error(
                "'%s' is not a valid backend type. Allowed values are: '%s'"
                % (values, allowed))

        setattr(
            namespace, self.dest,
            backend_type
            )


class ComponentAction(argparse.Action):
    """
    Action to interpret the user input for the list of components
    """
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            component_list_decoded = set(ast.literal_eval(values))
        except (SyntaxError, ValueError, TypeError):
            parser.error("'%s' is not a valid list of components" % values)

        setattr(namespace, self.dest, component_list_decoded)


class RecorderParser(object):
    """
    Parses command line arguments to configure the property recorder

    Also provides some textual help to the user
    """
    def __init__(self, config=None):
        """
        ctor

        @param config: configuration of the font-end
        to be used optionally to avoid the argparse itself
        and for the unit tests.
        @type config: string
        @see:
        ctamonitoring.property_recorder.test_standalone_recorder.RecorderParserTest
        for an example to set the config as an argument.
        """
        argparser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)

        argparser.add_argument(
            '--max_comps',
            action='store',
            dest='max_comps',
            type=long,
            help='Maximum number of components to be stored in'
                 ' the recorder, no matter how many properties')
        argparser.add_argument(
            '--default_timer_trigger',
            action='store',
            dest='default_timer_trigger',
            type=float,
            help='The monitoring period for the properties when no specific'
                 ' entry exists in the CDB')
        argparser.add_argument(
            '--max_props',
            action='store',
            dest='max_props',
            type=long,
            help='Maximum number of properties being monitored')
        argparser.add_argument(
            '--checking_period',
            action='store',
            dest='checking_period',
            type=long,
            help='Period in seconds to check for lost components or '
                 'new components (default 10 s)')
        argparser.add_argument(
            '--include_mode',
            dest='is_include_mode',
            action='store_true',
            help='If set the recorder will only consider the components '
                 'included in list components and reject all the others '
                 ', using the provided list with --components as '
                 'an "include list". This is NOT used by default')
        argparser.add_argument(
            '--exclude_mode',
            dest='is_include_mode',
            action='store_false',
            help='If set the recorder will the provided list is considered as '
                 'an "exclude list, using the provided list with --components'
                 ' as the "exclude list". Used by default')
        argparser.set_defaults(is_include_mode=False)
        argparser.add_argument(
            '--components',
            action='store',
            dest='components',
            type=list,
            help='The include or exclude list, depending on the '
                 '--is_include_mode value, of component represented'
                 'by their string names')
        argparser.add_argument(
            '--backend_type',
            action=ValidBackendAction,
            dest='backend_type',
            type=str,
            help='The backends to be used, available ones are ' +
                 str([e.name for e in BACKEND_TYPE]))
        argparser.add_argument(
            '--backend_config', action=ConfigBackendAction,
            dest='backend_config',
            type=str,
            help='String using Python encoding with a map configuration '
                 'parameters for the backend e.g. "' +
                 str({'database': 'ctamonitoring'}) + '"')
        argparser.add_argument(
            '--component_list',
            action=ComponentAction,
            dest='component_list',
            type=str,
            help='The include or exclude list, using the Python encoding '
                 'depending of component represented by their string names. '
                 'on the include_mode, e.g. "' +
                 str(['Component1', 'Component2']) + '"')
        argparser.add_argument(
            '-v', dest='verbose',
            action='store_true',
            help='to display in the console debug level messages')
        argparser.add_argument(
            '-vv', dest='more_verbose',
            action='store_true',
            help='to display in the console for all level messages')

        if config is not None:
            args = argparser.parse_args(config)
        else:
            args = argparser.parse_args()

        self._args = vars(args)

    def get_verbosity(self):
        """
        Gets the verbosity level of the logs by standalone recorder console

        @return: verbosity level
        @rtype: int
        """
        if 'more_verbose' in self._args:
            return logging.NOTSET
        elif 'verbose' in self._args:
            return logging.DEBUG
        else:
            return logging.INFO

    def get_config(self):
        """
        Factory to create the configuration of the recorder

        The configuration will be created from the parsed configuration data.
        @return: Configuration of the recorder.
        @rtype: ctamonitoring.property_recorder.config.RecorderConfig
        """
        recorder_config = RecorderConfig()

        if 'default_timer_trigger' in self._args:
            recorder_config.default_timer_trigger = (
                self._args['default_timer_trigger']
                )
        if 'max_comps' in self._args:
            recorder_config.max_comps = self._args['max_comps']
        if 'max_props' in self._args:
            recorder_config.max_props = self._args['max_props']
        if 'checking_period' in self._args:
            recorder_config.checking_period = self._args['checking_period']
        if 'backend_type' in self._args:
            recorder_config.backend_type = self._args['backend_type']
        if 'backend_config' in self._args:
            recorder_config.backend_config = self._args['backend_config']
        if 'is_include_mode' in self._args:
            recorder_config.is_include_mode = self._args['is_include_mode']
        if 'component_list' in self._args:
            recorder_config.set_components(self._args['component_list'])

        return recorder_config


def get_input_config():
    """
    Obtains and sets the recorder config from the parser
    """
    my_parser = RecorderParser()
    my_recorder_config = my_parser.get_config()
    my_verbosity = my_parser.get_verbosity()
    config = (my_recorder_config, my_verbosity)
    return config


def _run_until_interrupted(recorder, client_refresh_sec):
    """
    Makes the main thread to work until keyboard interruption

    @param recorder: property recorder object.
    @type recorder: StandaloneRecorder
    @param client_refresh_sec: rate to refresh ACS client.
    @type client_refresh_sec: int
    """
    try:
        while True:
            time.sleep(client_refresh_sec)
            if not recorder.is_acs_client_ok():
                try:
                    recorder.make_new_acs_client()
                except CORBAProblemExImpl:
                    # Exception means ACS is down, so we give time to recover
                    print('ACS is down, will wait 10 sec. for its recovery')
    except KeyboardInterrupt:
        print('Command to stop the recorder')

    finally:
        recorder.close()
        recorder = None


def run_standlone_recorder(config, client_refresh_sec):
    recorder = StandaloneRecorder(*config)
    recorder.print_config()
    recorder.start()
    _run_until_interrupted(recorder, client_refresh_sec)


if __name__ == "__main__":
    application_config = get_input_config()
    run_standlone_recorder(application_config, CLIENT_REFRESH_TIME_SEC)
    print('Exit application')
