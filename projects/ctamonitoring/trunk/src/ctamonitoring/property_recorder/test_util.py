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
'''

import unittest
from ctamonitoring.property_recorder.util import PropertyTypeUtil 
from Acspy.Clients.SimpleClient import PySimpleClient
import logging
from ctamonitoring.property_recorder.backend import property_type

PropertyType = property_type.PropertyType

class getPropertyTypeTypeTest(unittest.TestCase):
   
    
    
    def setUp(self):
        # I was trying to make ACS up here fpr teh testbut does not work
        # Perhaps is better to use TAT or some util used in tat for this
        # I will assume that ACS is running, with the correct CDB, component and container runnint
        # TODO: Document!
                
        #set the corresponding ACS CDB
        #os.environ["ACS_CDB"] = "/vagrant/actl/testacsproperties/test"
        #check that the CDB exists
        #print os.environ["ACS_CDB"] +'/CDB'
       
        #if os.path.isdir(os.environ['ACS_CDB']+'/CDB'):
        #    print "cdb dir found"
        #else:
        #    print "NO cdb dir found"
        #    self.fail("no CDB found, test failed")
        #check if ACS is running. If so, the the test is failed
        #if getManager() is None:
        #    print 'starting ACS'
        #    call(["acsStart", "-v"])
        #else:
        #    self.fail("ACS already running, should be stopped")
        #start the test container
        #Popen(["acsStartContainer", "-cpp", " myC"])
        #sleep to o let the container start
        #time.sleep(10)
        
        #create a client
        self._my_acs_client = PySimpleClient()
        logger = self._my_acs_client.getLogger()
        logger.setLevel(logging.WARNING) # disable annoying output from te tests
        
        
    def tearDown(self):
        self._my_acs_client.disconnect()
        #call(["acsStop"])
    
    def test_get_enum_prop_dict(self):
        
        my_component = self._my_acs_client.getComponent("TEST_PROPERTIES_COMPONENT", True)
        
        
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
        my_component = self._my_acs_client.getComponent("TEST_PROPERTIES_COMPONENT", True)
        
        #I will check just the RO versions assu
 
         

        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_EnumTestROProp()._NP_RepositoryId),
            PropertyType.OBJECT
            ) 
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_EnumTestRWProp()._NP_RepositoryId),
            PropertyType.OBJECT
            ) 
                   
        PropertyType.OBJECT
                             
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleROProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            ) 
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_floatSeqRWProp()._NP_RepositoryId),
            PropertyType.FLOAT_SEQ
            ) 
        
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_longSeqRWProp()._NP_RepositoryId),
            PropertyType.LONG_SEQ
            )
       
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )  
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongROProp()._NP_RepositoryId),
            PropertyType.LONG
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_booleanROProp()._NP_RepositoryId),
            PropertyType.BOOL
            )         
      
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleSeqROProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_longLongROProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_patternROProp()._NP_RepositoryId),
            PropertyType.BIT_FIELD
            )      
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_uLongRWProp()._NP_RepositoryId),
            PropertyType.LONG
            )  
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_booleanRWProp()._NP_RepositoryId),
            PropertyType.BOOL
            )   
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                my_component._get_doubleSeqRWProp()._NP_RepositoryId),
            PropertyType.DOUBLE_SEQ
            )     
        
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                 my_component._get_longLongRWProp()._NP_RepositoryId),
            PropertyType.LONG_LONG
            )         
         
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                 my_component._get_patternRWProp()._NP_RepositoryId),  
            PropertyType.BIT_FIELD
            )         
       
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                 my_component._get_uLongSeqROProp()._NP_RepositoryId),  
            PropertyType.LONG_SEQ
            )   
        
        
        self.assertRaises(
                TypeError, 
                PropertyTypeUtil.get_property_type,
                    my_component._get_booleanSeqROProp()._NP_RepositoryId
                )
    
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                  my_component._get_floatROProp()._NP_RepositoryId),  
            PropertyType.FLOAT
            ) 
         
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                   my_component._get_longROProp()._NP_RepositoryId),  
            PropertyType.LONG
            ) 
         
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_stringROProp()._NP_RepositoryId),  
            PropertyType.STRING
            ) 
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_uLongSeqRWProp()._NP_RepositoryId),  
            PropertyType.LONG_SEQ
            )       
        
       
        self.assertRaises(
                TypeError, 
                PropertyTypeUtil.get_property_type,
                    my_component._get_booleanSeqRWProp()._NP_RepositoryId
                )
        
         
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_floatRWProp()._NP_RepositoryId),  
            PropertyType.FLOAT
            ) 
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_longRWProp()._NP_RepositoryId),  
            PropertyType.LONG
            )
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_stringRWProp()._NP_RepositoryId),  
            PropertyType.STRING
            )
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_floatSeqROProp()._NP_RepositoryId),  
            PropertyType.FLOAT_SEQ
            )      
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_longSeqROProp()._NP_RepositoryId),  
            PropertyType.LONG_SEQ
            )     
        
        self.assertEqual (
            PropertyTypeUtil.get_property_type(
                    my_component._get_uLongLongROProp()._NP_RepositoryId),  
            PropertyType.LONG_LONG
            )        
           

      
      
if __name__ == '__main__':
    unittest.main()

#suite = unittest.TestLoader().loadTestsFromTestCase(RecorderConfigTest)
#unittest.TextTestRunner(verbosity=2).run(suite)