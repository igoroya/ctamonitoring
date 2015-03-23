"""
Contains some helper classes to be of used in the module

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id: constants.py 566 2013-08-26 16:30:31Z igoroya $
@change: $LastChangedDate: 2013-08-26 18:30:31 +0200 (Mon, 26 Aug 2013) $, $LastChangedBy: igoroya $

"""
from ctamonitoring.property_recorder.backend.property_type import PropertyType
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.constants import DecodeMethod
import ast

class PropertyTypeUtil():

    '''
     Holds the property type enum according to the entry at the
     NP_Repository_ID of the property

    '''
    __cbMap = {}
    __cbMap[constants.RODOUBLE_NP_REP_ID] = PropertyType.DOUBLE
    __cbMap[constants.RWDOUBLE_NP_REP_ID] = PropertyType.DOUBLE
    __cbMap[constants.RODOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
    __cbMap[constants.RWDOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
    __cbMap[constants.ROFLOAT_NP_REP_ID] = PropertyType.FLOAT
    __cbMap[constants.RWFLOAT_NP_REP_ID] = PropertyType.FLOAT
    __cbMap[constants.ROFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
    __cbMap[constants.RWFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
    __cbMap[constants.ROLONG_NP_REP_ID] = PropertyType.LONG
    __cbMap[constants.RWLONG_NP_REP_ID] = PropertyType.LONG
    __cbMap[constants.ROLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    __cbMap[constants.RWLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    __cbMap[constants.ROULONG_NP_REP_ID] = PropertyType.LONG
    __cbMap[constants.RWULONG_NP_REP_ID] = PropertyType.LONG
    __cbMap[constants.ROULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    __cbMap[constants.RWULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
    __cbMap[constants.ROLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    __cbMap[constants.RWLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    # longLongSeq unsupported in ACS
    __cbMap[constants.ROLONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.RWLONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.ROULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    __cbMap[constants.RWULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
    __cbMap[constants.ROULONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.RWULONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.ROBOOLEAN_NP_REP_ID] = PropertyType.BOOL
    __cbMap[constants.RWBOOLEAN_NP_REP_ID] = PropertyType.BOOL
    #TODO: we should have PropertyType.BOOL_SEQ in the backend
    __cbMap[constants.ROBOOLEANSEQ_NP_REP_ID] = None
    __cbMap[constants.RWBOOLEANSEQ_NP_REP_ID] = None
    __cbMap[constants.ROPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
    __cbMap[constants.RWPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
    # patternSeq not supported
    __cbMap[constants.ROPATTERNSEQ_NP_REP_ID] = None
    __cbMap[constants.RWPATTERNSEQ_NP_REP_ID] = None
    __cbMap[constants.ROSTRING_NP_REP_ID] = PropertyType.STRING
    __cbMap[constants.RWSTRING_NP_REP_ID] = PropertyType.STRING
    __cbMap[constants.ROSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ
    __cbMap[constants.RWSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ
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
            if PropertyTypeUtil.__cbMap[repID] is None:
                raise TypeError("The type " + repID + " is not supported")
                # throw an unsuported exception
            else:
                return (
                    PropertyTypeUtil.__cbMap[repID]
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
        
        
