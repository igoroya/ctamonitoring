__version__ = "$Id: test_config.py 1 2015-01-01 00:40:12Z igoroya $"


'''
Unit test module for test_config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_config.py 1 2015-01-1 00:40:12Z igoroya $
@change: $LastChangedDate: 2015-01-1  02:40:12 +0200 (Wed, 25 Sep 2013) $
@change: $LastChangedBy: igoroya $
'''


import unittest
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.config import BackendType


class RecorderConfigTest(unittest.TestCase):
    
    default_monitor_rate = 60
    default_max_comps = 100
    default_max_props = 1000
    default_checking_period = 10  # seconds
    default_backend_type = BackendType.LOG
    a_long = 150L
    a_double = 0.2
    a_neg_long = -1L
    a_string = 'a'
    a_string_list = ['a', 'b']
    a_hybrid_list = ['a', 1]
    a_backend_type = BackendType.MONGODB
    
    
    
    def setUp(self):
        self.recoder_config = RecorderConfig()
        

    def test_default_monitor_rate(self): 
        #check the default value
        self.assertEqual(self.recoder_config.default_monitor_rate, self.default_monitor_rate)
        
        self.recoder_config.default_monitor_rate = self.a_long
        self.assertEqual(self.recoder_config.default_monitor_rate, self.a_long)
        
        self.assertRaises(ValueError, setattr, self.recoder_config, "default_monitor_rate", self.a_neg_long)
        self.assertRaises(ValueError, setattr, self.recoder_config, "default_monitor_rate", self.a_double)
        self.assertRaises(ValueError, setattr, self.recoder_config, "default_monitor_rate", self.a_string)

        
    def test_max_comps(self):
            #check the default value
        self.assertEqual(self.recoder_config.max_comps, self.default_max_comps)
        
        self.recoder_config.max_comps = self.a_long
        self.assertEqual(self.recoder_config.max_comps, self.a_long)
        
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_comps", self.a_neg_long)
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_comps", self.a_double)
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_comps", self.a_string)
    
    def test_max_props(self):
            #check the default value
        self.assertEqual(self.recoder_config.max_props, self.default_max_props)
        
        self.recoder_config.max_props = self.a_long
        self.assertEqual(self.recoder_config.max_props, self.a_long)
        
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_props", self.a_neg_long)
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_props", self.a_double)
        self.assertRaises(ValueError, setattr, self.recoder_config, "max_props", self.a_string)
    
    def test_checking_period(self): 
        #check the default value
        self.assertEqual(self.recoder_config.checking_period, self.default_checking_period)
        
        self.recoder_config.checking_period = self.a_long
        self.assertEqual(self.recoder_config.checking_period, self.a_long)
        
        self.assertRaises(ValueError, setattr, self.recoder_config, "checking_period", self.a_neg_long)
        self.assertRaises(ValueError, setattr, self.recoder_config, "checking_period", self.a_double)
        self.assertRaises(ValueError, setattr, self.recoder_config, "checking_period", self.a_string)

    def test_backend_type(self): 
        #check the default value
        self.assertEqual(self.recoder_config.backend_type, self.default_backend_type)
        
        self.recoder_config.backend_type = self.a_backend_type
        self.assertEqual(self.recoder_config.backend_type, self.a_backend_type)
       
        self.assertRaises(ValueError, setattr, self.recoder_config, "backend_type", self.a_string)
        self.assertRaises(ValueError, setattr, self.recoder_config, "backend_type", self.a_long)
    
    def test_is_include_mode(self):
        self.recoder_config.is_include_mode = True
        self.assertTrue(self.recoder_config.is_include_mode)
        
        self.recoder_config.is_include_mode = False
        self.assertFalse(self.recoder_config.is_include_mode)        
        # should raise an exception for other data types
        self.assertRaises(TypeError, setattr, self.recoder_config, "is_include_mode", self.a_long)
        self.assertRaises(TypeError, setattr, self.recoder_config, "is_include_mode", self.a_double)
        self.assertRaises(TypeError, setattr, self.recoder_config, "is_include_mode", self.a_string)    

    def test_components(self):
        
        self.assertRaises(NotImplementedError, setattr, self.recoder_config, "components", self.a_string_list)
        
        self.recoder_config.setComponentList(self.a_string_list)
        self.assertEquals(self.recoder_config.components, self.a_string_list)
        
        self.assertRaises(TypeError, self.recoder_config.setComponentList, self.a_double)
        
        self.assertRaises(TypeError, self.recoder_config.setComponentList, self.a_hybrid_list)
    
#    components
    
    

if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(RecorderConfigTest)
#unittest.TextTestRunner(verbosity=2).run(suite)