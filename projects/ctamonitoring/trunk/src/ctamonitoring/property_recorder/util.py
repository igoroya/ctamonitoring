__version__ = "$Id: util.py 1152 2015-03-23 18:03:44Z igoroya $"

'''
Contains some helper classes to be of used in the module

I have tried to put here all the "hacks" I needed to add for the property
recorder to work 

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id: constants.py 566 2013-08-26 16:30:31Z igoroya $
@change: $LastChangedDate: 2013-08-26 18:30:31 +0200 (Mon, 26 Aug 2013) $, $LastChangedBy: igoroya $
'''

from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.constants import DecodeMethod
from ctamonitoring.property_recorder.recorder_exceptions import *

import ast


PropertyType = property_type.PropertyType

class PropertyTypeUtil():
    
    '''
     Holds the property type enum according to the entry at the
     NP_Repository_ID of the property

    '''
    _cbMap = {}
    _cbMap[constants.RODOUBLE_NP_REP_ID] = PropertyType.DOUBLE
    _cbMap[constants.RWDOUBLE_NP_REP_ID] = PropertyType.DOUBLE
    _cbMap[constants.RODOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
    _cbMap[constants.RWDOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
    _cbMap[constants.ROFLOAT_NP_REP_ID] = PropertyType.FLOAT
    _cbMap[constants.RWFLOAT_NP_REP_ID] = PropertyType.FLOAT
    _cbMap[constants.ROFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
    _cbMap[constants.RWFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
    _cbMap[constants.ROLONG_NP_REP_ID] = PropertyType.LONG
    _cbMap[constants.RWLONG_NP_REP_ID] = PropertyType.LONG
    _cbMap[constants.ROLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    _cbMap[constants.RWLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    _cbMap[constants.ROULONG_NP_REP_ID] = PropertyType.LONG
    _cbMap[constants.RWULONG_NP_REP_ID] = PropertyType.LONG
    _cbMap[constants.ROULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    _cbMap[constants.RWULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    _cbMap[constants.ROLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    _cbMap[constants.RWLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    # longLongSeq unsupported in ACS
    _cbMap[constants.ROLONGLONGSEQ_NP_REP_ID] = None
    _cbMap[constants.RWLONGLONGSEQ_NP_REP_ID] = None
    _cbMap[constants.ROULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    _cbMap[constants.RWULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    _cbMap[constants.ROULONGLONGSEQ_NP_REP_ID] = None
    _cbMap[constants.RWULONGLONGSEQ_NP_REP_ID] = None
    _cbMap[constants.ROBOOLEAN_NP_REP_ID] = PropertyType.BOOL
    _cbMap[constants.RWBOOLEAN_NP_REP_ID] = PropertyType.BOOL
    #TODO: we should have PropertyType.BOOL_SEQ in the backend
    _cbMap[constants.ROBOOLEANSEQ_NP_REP_ID] = None
    _cbMap[constants.RWBOOLEANSEQ_NP_REP_ID] = None
    _cbMap[constants.ROPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
    _cbMap[constants.RWPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
    # patternSeq not supported
    _cbMap[constants.ROPATTERNSEQ_NP_REP_ID] = None
    _cbMap[constants.RWPATTERNSEQ_NP_REP_ID] = None
    _cbMap[constants.ROSTRING_NP_REP_ID] = PropertyType.STRING
    _cbMap[constants.RWSTRING_NP_REP_ID] = PropertyType.STRING
    _cbMap[constants.ROSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ
    _cbMap[constants.RWSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ
#------------------------------------------------------------------------------

    @staticmethod
    def getPropertyType(repID):
        """
        Returns the enum type of the property for the
        ND_Repository_ID of the property

        Returns:
        PropertyType -- from the Enum at
                        ctamonitoring.property_recorder.backend.property_type
        Raises:
        TypeError -- if the property type is not supported
        """
        try:
            if PropertyTypeUtil._cbMap[repID] is None:
                raise TypeError("The type " + repID + " is not supported")
                # throw an unsuported exception
            else:
                return (
                    PropertyTypeUtil._cbMap[repID]
                )

        # If key error, then it is probably an enum
        except KeyError:
            PropertyType.OBJECT
#------------------------------------------------------------------------------

    @staticmethod
    def getEnumPropDict(prop, logger):
        """
        Creates an dictionary with  int_rep:str_rep

        This is needed in order to store the string representation of
        an enumeration, as the monitors use the integer
        representation by default.

        Keyword arguments:
        property     -- property object

        Raises:
        ValueError -- if less than 2 states are found
        AttributeError -- no states description is found in the CDB


        Returns: enumDict dictionary of pair int_rep:str_rep of the enum
        """
        try:
            enumValues = prop.get_characteristic_by_name(
                "statesDescription").value().split(', ')
        except Exception:
            logger.logWarning('No statesDescription found in the CDB')
            raise AttributeError

        enumDict = {}
        i = 0
        for item in enumValues:
            string = str(i)
            enumDict[string] = enumValues[i]
            i = i + 1
        if len(enumDict) < 2:
            logger.logWarning(
                'Less than 2 states found, no sense on using a string rep.')
            raise ValueError

        return enumDict
    
    @staticmethod
    def is_property_ok(acs_property):
        '''
        This methods checks the case when some properties seem to be present in
        the list of characteristics but the property is faulty
        this is typically happening with pattern
        properties OR when the property exists in the CDB
        but it is not implemented in the component
        '''
        try:
            (acs_property.get_sync()[0])
        except Exception:
            return False        
        else:
            return True
        
    @staticmethod
    def is_archive_delta_enabled(archive_delta):
        '''
        To determine when archive delta is indeed disabled
        (Can be done in different ways)
        
        attributes - property attributes for"archive_delta" or "archive_delta_percent"
        '''
        if (archive_delta is None 
              or archive_delta == "0"
              or archive_delta == "0.0"
              or archive_delta == 0
              or archive_delta == 0.0
              ):
            
            return False
        else:
            return True
    

#TODO: Will becme redundant, remove when possible
class DecodeUtil():
    """
    Holds utilities to decode data from the CDB
    """
    @staticmethod
    def try_utf8(data):
        "Returns a Unicode object on success, or None on failure"
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return None
        
class ComponentUtil(object):
    '''
    Used to determine if a component is characteristic,
    and if it is Python.
    
    Encapsulates some "hacking" wich could be oplimized later  
    '''

    @staticmethod
    def is_characteristic_component(component):
        '''
        Checks is we can get the characteristics. 
        
        Returns True is it is a characteristic coomponent
        '''
        try:
            component.find_characteristic("*")
        except Exception:
            return False
        else:
            return True

    @staticmethod
    def is_python_char_component(component):
        '''
        Check if the component is a Python characteristic
        component.
        
        Returns true if it is the case
        
        Raise an exception if it is not a characteristic component
        '''
        return (component.find_characteristic("*") == 0)
    
    @staticmethod
    def is_a_property_recorder_component(component):
        return (component._NP_RepositoryId == constants.RECORDER_NP_REP_ID)
    
    @staticmethod                
    def verify_component_state(self, comp_reference, component_id):
        '''
        Check if the component is still operational
        
        component -- the reference to an ACS component 
      
        returns True is OK
          
        Raises:
        ComponenNotFoundError -- component is not present
        WrongComponenStateError -- component is present, but in wrong state
        '''
        
            
        state = None
       
        try:
            state = str(comp_reference._get_componentState())
        except Exception:
            raise ComponenNotFoundError(component_id)

        if (state != "COMPSTATE_OPERATIONAL"):
            raise WrongComponenStateError(component_id, state)
    
        return True
    
    

class AttributeDecoder(object):
    
    @staticmethod
    def _decode_none(value):
        '''
        This is used with strings that do not need any decoding
        '''
        return value
    
    @staticmethod
    def _decode_ast_literal(value):
        '''
        This is used with variables that are no strings, that need
        to be decoded
        '''
        return ast.literal_eval(value)

    @staticmethod
    def _decode_ast_literal_hybrid(value):
        '''
        This is used with variables can be strings or numbers
        '''
        try: 
            return AttributeDecoder.decode_ast_literal(value)
        #If exception then it is a string
        except Exception:
            return value
    @staticmethod
    def _decode_utf8(value):    
        '''
        Returns a Unicode object on success, or None on failure
        '''
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return None
    @staticmethod
    def decode_attribute(value, decode_method):
        '''
        Picks the correct decoding method
        Raises an exception when the decoding method is not supported
        '''
        if decode_method is DecodeMethod.NONE : AttributeDecoder._decode_none(value)
        elif decode_method is DecodeMethod.AST_LITERAL : AttributeDecoder._decode_ast_literal(value)
        elif decode_method is DecodeMethod.AST_LITERAL_HYBRID : AttributeDecoder._decode_ast_literal_hybrid(value)
        elif decode_method is DecodeMethod.UTF8 : AttributeDecoder._decode_utf8(value)
        else:  raise ValueError("decode_method is not supported") 
        
        
class EnumUtil(object):
    
    @staticmethod
    def fromString(enum_type, name):
        '''
        To obtain the enum object from  astring rep.
        
        Raises ValueError if type/value not recognized
        '''
        return enum_type._values[enum_type._keys.index(name)]

    @staticmethod
    def toString(enum_value):
        return enum_value.key
