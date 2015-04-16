import logging
import argparse
import ast
import pprint
from Acspy.Clients.SimpleClient import PySimpleClient
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.front_end import FrontEnd
from ctamonitoring.property_recorder.config import BackendType
from ctamonitoring.property_recorder.util import EnumUtil
'''
Module with all what is related to the configuration holding for the property 
recorder frontend

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''
'''
This is a version of the property recorder that is run as an application and not as an ACS component.
In primary meant for test but may be useful later also to run as an alternative for the component version
'''



__version__ = "$Id$"



class ConfigBackendAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            backend_config_decoded = ast.literal_eval(values)
            assert(type(backend_config_decoded) is dict)
        except:
            parser.error("'%s' is not a valid backend config" % values)
            #raise argparse.ArgumentError("Minimum bandwidth is 12")

        setattr(namespace, self.dest, backend_config_decoded)
    


class ValidBackendAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            assert(values in BackendType)
        except:
            allowed = str(BackendType._keys)
            parser.error("'%s' is not a valid backend type. Allowed values are: '%s'" % (values, allowed))
            #raise argparse.ArgumentError("Minimum bandwidth is 12")

        setattr(namespace, self.dest, EnumUtil.from_string(BackendType, values))




class ComponentAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            component_list_decoded = set(ast.literal_eval(values))
        except:
            parser.error("'%s' is not a valid list of components" % values)
            #raise argparse.ArgumentError("Minimum bandwidth is 12")

        setattr(namespace, self.dest, component_list_decoded)


class RecorderParser(object):
    '''
    Parses command line arguments to configure the property recorder
    Also provides some textual help to the user 
    '''
    def __init__(self , cmdline=None):
    
        argparser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
        
        argparser.add_argument('--max_comps', action = 'store', dest = 'max_comps', 
                        type=long, 
                        help='Maximum number of components to be stored in' 
                            ' the recorder, no matter how many properties')
        argparser.add_argument('--default_timer_trigger', action = 'store',
                        dest='default_timer_trigger', type = float, 
                        help='The monitoring period for the properties when no specific entry' 
                            ' exists in the CDB')
        argparser.add_argument('--max_props', action = 'store',
                        dest='max_props', type = long, 
                        help='Maximum number of properties being monitored') 
        argparser.add_argument('--checking_period', action = 'store',
                        dest='checking_period', type = long, 
                        help='Period in seconds to check for lost components or new components '
                            '(default 10 s)')
        argparser.add_argument('--include_mode', dest='is_include_mode', action='store_true',
                        help='If set the recorder will only consider the components '
                        'included in list components and reject all the others '
                        ', using the provided list with --components as an "include list". '
                        'This is NOT used by default')
        argparser.add_argument('--exclude_mode', dest='is_include_mode', action='store_false',
                        help='If set the recorder will the provided list is considered as an "exclude list". '
                        ', using the provided list with --components as the "exclude list". '
                        'Used by default')   
        argparser.set_defaults(is_include_mode=False)
        argparser.add_argument('--components', action = 'store',
                        dest='components', type = list, 
                        help='The include or exclude list, depending on the --is_include_mode value, '
                            'of component represented by their string names')   
        argparser.add_argument('--backend_type', action=ValidBackendAction,
                        dest='backend_type', type = str, 
                        help='The backends to be used, available one are '+
                        str(BackendType._keys))
        argparser.add_argument('--backend_config', action = ConfigBackendAction,
                        dest='backend_config', type = str, 
                        help='String using Python encoding with a map configuration '
                        'parameters for the backend e.g. "' +str({'database' : 'ctamonitoring'})+'"')
        argparser.add_argument('--component_list', action = ComponentAction,
                        dest='component_list', type = str,
                        help='The include or exclude list, using the Python encoding depending '
                            'of component represented by their string names. '
                            'on the include_mode, e.g. "'+str(['Component1', 'Component2']) + '"')
        argparser.add_argument('-v', dest='verbose', action='store_true',
                        help='to display in the console debug level messages')
        argparser.add_argument('-vv', dest='more_verbose', action='store_true',
                        help='to display in the console for all level messages')                    
  
        if cmdline is not None:
            args = argparser.parse_args(cmdline)
        else:
            args = argparser.parse_args()

        
        #self._args = vars(argparser.parse_args())
        self._args = vars(args)
   
    def get_verbosity(self):
        '''
        Gets the verbosity level of the logs provided by standalone recorder
        console
        
        
        @return: verbosity level 
        @rtype: int 
        '''
        if 'more_verbose'  in self._args :
            return 0
        elif 'verbose'  in self._args :
            return logging.DEBUG
        else:
            return logging.INFO
   
    def feed_config(self): 
        '''
        Factory to create, from the parsed configuration data, 
        an object RecorderConfig 
        
        returns RecorderConfig
        '''
        recorder_config = RecorderConfig()
               
        if 'default_timer_trigger' in self._args :
            recorder_config.default_timer_trigger = self._args['default_timer_trigger']
        if 'max_comps'  in self._args :
            recorder_config.max_comps = self._args['max_comps']  
        if 'max_props'  in self._args :
            recorder_config.max_props = self._args['max_props']  
        if 'checking_period'  in self._args :
            recorder_config.checking_period = self._args['checking_period']      
        if 'backend_type'  in self._args :
            recorder_config.backend_type = self._args['backend_type']
        if 'backend_config'  in self._args :
            recorder_config.backend_config = self._args['backend_config']  
        if 'is_include_mode'  in self._args :
            recorder_config.is_include_mode = self._args['is_include_mode']  
        if 'component_list'  in self._args :
            recorder_config.set_components(self._args['component_list'])              
    
        return recorder_config
    
class StandaloneRecorder(object):

    def __init__(self, recorder_config, verbosity):
        '''
        @var recorder_config: the configuration of the recorder
        @type recorder_config: RecorderConfig
        '''
        
        
        # Create the ACS simple client. This allows the communication with ACS
        self._my_acs_client = PySimpleClient()
        
        self._logger = self._my_acs_client.getLogger()
        
        self._logger.setLevel(verbosity)
       
        self.recorder_config = recorder_config
        #create recorder object 

        self.recorder = FrontEnd(recorder_config, self._my_acs_client)
        
        self._logger.info('Property recorder up')

    def start(self):
        self.recorder.start_recording()
        self._logger.info('Recording start')
        
    def stop(self):
        self.recorder.stop_recording()
        self._logger.info('Recording stop')

    def __del__(self):
        self._logger.info('Switching off property recorder')
        self.stop()
        self.recorder = None
        self.recorder_config = None
        self._my_acs_client.disconnect()
        self._my_acs_client = None

    def print_config(self):
        
        self._logger.debug(
                'Property Recorder Configuration'
                '\n--------------------------------------\n' +
                pprint.pformat(vars(self.recorder_config)) +
                '\n--------------------------------------')
        
      
        

if __name__ == "__main__":

    #Configure
    parser = RecorderParser()
    recorder_config = parser.feed_config()
    verbosity = parser.get_verbosity()


    #Create a recorder. 
    recorder = StandaloneRecorder(recorder_config, verbosity)
    
    
    
    
    #Show the configuration
    recorder.print_config()    

    #Start recording
    recorder.start()

    #Work until user stops
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print 'Command to stop the recorder'
        
    finally:
        recorder.stop()
        recorder = None
           
    print 'Exit application'
    



