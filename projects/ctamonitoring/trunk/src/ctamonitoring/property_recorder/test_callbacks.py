'''
Unit test module for callbacks

Here we test the base class for all these callbacks and 
also the factory for them

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_callbacks.py 1168 2015-04-13 18:42:27Z igoroya $
@change: $LastChangedDate: 2015-04-13 20:42:27 +0200 (Mon, 13 Apr 2015) $
@change: $LastChangedBy: igoroya $
'''
import unittest
from ctamonitoring.property_recorder.backend.dummy.registry import Buffer
from ctamonitoring.property_recorder  import callbacks
from ctamonitoring.property_recorder.frontend_exceptions import UnsupporterPropertyTypeError
from ctamonitoring.property_recorder.callbacks import CBFactory, BaseArchCB

from ACS import CBDescOut  # @UnresolvedImport
from ACSErr import Completion  # @UnresolvedImport
from ACS import (
    _objref_ROBool,  # @UnresolvedImport       
    _objref_RObooleanSeq,   # @UnresolvedImport
    _objref_ROfloat,       # @UnresolvedImport  
    _objref_ROlongLong,    # @UnresolvedImport 
    _objref_ROstring,      # @UnresolvedImport 
    _objref_ROuLongLong,    # @UnresolvedImport
    _objref_ROOnOffSwitch,  # @UnresolvedImport
    _objref_ROdouble,       # @UnresolvedImport
    _objref_ROfloatSeq,  # @UnresolvedImport
    _objref_ROlongSeq,      # @UnresolvedImport
    _objref_ROstringSeq,    # @UnresolvedImport
    _objref_ROuLongSeq,     # @UnresolvedImport
    _objref_ROboolean,      # @UnresolvedImport
    _objref_ROdoubleSeq,    # @UnresolvedImport
    _objref_ROlong,         # @UnresolvedImport
    _objref_ROpattern,     # @UnresolvedImport 
    _objref_ROuLong,    # @UnresolvedImport
    _objref_RWBool,         # @UnresolvedImport
    _objref_RWbooleanSeq,   # @UnresolvedImport
    _objref_RWfloat,        # @UnresolvedImport
    _objref_RWlongLong,     # @UnresolvedImport
    _objref_RWstring,       # @UnresolvedImport
    _objref_RWuLongSeq,     # @UnresolvedImport
    _objref_RWOnOffSwitch,  # @UnresolvedImport
    _objref_RWdouble,       # @UnresolvedImport
    _objref_RWfloatSeq,     # @UnresolvedImport
    _objref_RWlongSeq,      # @UnresolvedImport
    _objref_RWuLong,        # @UnresolvedImport
    _objref_RWboolean,      # @UnresolvedImport
    _objref_RWdoubleSeq,    # @UnresolvedImport
    _objref_RWlong,         # @UnresolvedImport
    _objref_RWpattern,      # @UnresolvedImport
    _objref_RWuLongLong    # @UnresolvedImport
)
import logging

__version__ = "$Id: test_callbacks.py 1168 2015-04-13 18:42:27Z igoroya $"



class BaseArchCBTest(unittest.TestCase):
    
    def setUp(self):
        
        self.my_property = 'prop'
        self.backend_buffer = Buffer()
        
        logging.basicConfig()
        logging.getLogger("test_logger").setLevel(logging.WARNING)
        self.dummy_logger = logging.getLogger("test_logger")
        
    def test_init(self): 
        
        cb = BaseArchCB(self.my_property, self.backend_buffer)
        cb._logger = self.dummy_logger
        self.assertEqual('INIT', cb.status)
  
    def test_working(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer)
        cb._logger = self.dummy_logger
        value = 1
        completion = Completion(1, 0, 0, [])
        desc = CBDescOut(1, "e")
        cb.working(value, completion, desc)
        self.assertEqual('WORKING', cb.status)
        
    def test_done(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer)
        cb._logger = self.dummy_logger
        value = 1
        completion = Completion(1, 0, 0, [])
        desc = CBDescOut(1, "e")
        cb.done(value, completion, desc)
        self.assertEqual('DONE', cb.status)
        
    def test_last(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer)
        cb._logger = self.dummy_logger
        self.assertRaises(NotImplementedError, cb.last)
        
class CBFactoryTest(unittest.TestCase):
    
    def setUp(self):
        
        self.backend_buffer = Buffer()
        
        #logging.basicConfig()
        #logging.getLogger("test_logger").setLevel(logging.WARNING)
        #self.dummy_logger = logging.getLogger("test_logger")
    
    def test_get_callback(self):
        # RObool seems to be an ACS mistake, ROboolean should be used instead
        prop = _objref_ROBool()
        self.assertRaises(
                UnsupporterPropertyTypeError,
                CBFactory.get_callback , prop, "",
                self.backend_buffer)        
        
        # RObool seems to be an ACS mistake 
        prop = _objref_ROboolean
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))
        
        prop = _objref_RObooleanSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)     
        self.assertTrue(isinstance(cb, callbacks.ArchCBboolSeq))
        
        prop = _objref_ROfloat()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)         
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloat))  
          
        prop = _objref_ROlongLong()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongLong))
               
        prop = _objref_ROstring()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstring))
                 
        prop = _objref_ROuLongLong()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongLong))
              
        prop = _objref_ROOnOffSwitch()
        self.assertRaises(
                UnsupporterPropertyTypeError,
                CBFactory.get_callback,
                prop, "", self.backend_buffer)        
            
        prop = _objref_ROdouble()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdouble))
                 
        prop = _objref_ROfloatSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloatSeq))
            
        prop = _objref_ROlongSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongSeq))
                
        prop = _objref_ROstringSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstringSeq))
              
        prop = _objref_ROuLongSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongSeq))
               
        prop = _objref_ROboolean()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))
                
        prop = _objref_ROdoubleSeq()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdoubleSeq)) 
             
        prop = _objref_ROlong()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlong))
                   
        prop = _objref_ROpattern()
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBpatternValueRep))
                
        prop = _objref_ROuLong() 
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLong))
             
        prop = _objref_RWBool() 
        self.assertRaises(
                UnsupporterPropertyTypeError,
                CBFactory.get_callback,
                prop, "",
                self.backend_buffer)        
                  
        prop = _objref_RWbooleanSeq()   
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBboolSeq))
          
        prop = _objref_RWfloat()   
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloat))       
        
        prop = _objref_RWlongLong()  
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongLong))
             
        prop = _objref_RWstring()  
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstring))
               
        prop = _objref_RWuLongSeq()   
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongSeq))
            
        prop = _objref_RWOnOffSwitch()   
        self.assertRaises(
                UnsupporterPropertyTypeError,
                CBFactory.get_callback , prop, "",
                self.backend_buffer)        
         
        prop = _objref_RWdouble()    
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdouble))
             
        prop = _objref_RWfloatSeq() 
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloatSeq))
              
        prop = _objref_RWlongSeq()   
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongSeq))
             
        prop = _objref_RWuLong()    
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLong))
              
        prop = _objref_RWboolean()    
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))
            
        prop = _objref_RWdoubleSeq()     
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdoubleSeq))
        
        prop = _objref_RWlong()         
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlong))
          
        prop = _objref_RWpattern()   
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBpatternValueRep))
             
        prop = _objref_RWuLongLong()  
        cb = CBFactory.get_callback(prop, "", self.backend_buffer)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongLong))
    
        
if __name__ == '__main__':
    unittest.main()

