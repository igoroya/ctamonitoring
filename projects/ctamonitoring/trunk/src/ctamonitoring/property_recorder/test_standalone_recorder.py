__version__ = "$Id: test_standalone_recorder.py 1150 2015-03-20 18:31:51Z igoroya $"


'''
Unit test module for test_config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_standalone_recorder.py 1150 2015-03-20 18:31:51Z igoroya $
@change: $LastChangedDate: 2015-03-20 19:31:51 +0100 (Fri, 20 Mar 2015) $
@change: $LastChangedBy: igoroya $
'''


import unittest

from ctamonitoring.property_recorder.config import BackendType
from ctamonitoring.property_recorder.standalone_recorder import RecorderParser
from ctamonitoring.property_recorder.test_config import Defaults


class RecorderParserTest(unittest.TestCase):
    
    

    def setUp(self):
        "Values to be inserted"
        self.default_timer_trigger = 50
        self.max_comps = 80
        self.max_props = 300
        self.checking_period = 7  # seconds
        self.backend_type = BackendType.MONGODB
        self.backend_config = {'database' : 'ctamonitoring'}
        self.is_include_mode = True
        self.components = set(['a', 'b'])


        self.full_command_line_input =  ["--default_timer_trigger", "50",
                                              "--max_comps", "80",
                                              "--max_props", "300",
                                              "--checking_period", "7",
                                              "--backend_type", "MONGODB",
                                              "--backend_config", "{'database' : 'ctamonitoring'}",
                                              "--is_include_mode", "True",
                                              "--component_list", "['a', 'b']"]   
        
        
    def test_full_feed_config(self): 
        '''
        Test when providing the full list options in command line
        '''
        recoder_parser = RecorderParser(self.full_command_line_input)
        
        recorder_config = recoder_parser.feed_config()
       
        self.assertEqual(self.default_timer_trigger, recorder_config.default_timer_trigger)
        self.assertEqual(self.max_comps, recorder_config.max_comps)
        self.assertEqual(self.max_props, recorder_config.max_props)
        self.assertEqual(self.checking_period, recorder_config.checking_period)
        self.assertEqual(self.backend_type, recorder_config.backend_type)
        self.assertEqual(self.backend_config, recorder_config.backend_config)
        self.assertEqual(self.is_include_mode, recorder_config.is_include_mode)
        self.assertEqual(self.components, recorder_config.components)
        
    def test_empty_feed_config(self): 
        '''
        Test when providing the full list options in command line
        '''
        recoder_parser = RecorderParser()
        
        recorder_config = recoder_parser.feed_config()
       
        self.assertEqual(Defaults.default_timer_trigger, recorder_config.default_timer_trigger)
        self.assertEqual(Defaults.max_comps, recorder_config.max_comps)
        self.assertEqual(Defaults.max_props, recorder_config.max_props)
        self.assertEqual(Defaults.checking_period, recorder_config.checking_period)
        self.assertEqual(Defaults.backend_type, recorder_config.backend_type)
        self.assertEqual(Defaults.backend_config, recorder_config.backend_config)
        self.assertEqual(Defaults.is_include_mode, recorder_config.is_include_mode)
        self.assertEqual(Defaults.components, recorder_config.components)

    #test ConfigBackendAction
    
    
if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(RecorderConfigTest)
#unittest.TextTestRunner(verbosity=2).run(suite)