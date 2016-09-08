'''
Contains some helper classes to be of used in the module

Most of the "hacks" that are needed to make the property
recorder to work are included here

@author: igoroya
@organization: DESY
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.constants import DECODE_METHOD
from ctamonitoring.property_recorder.frontend_exceptions import (
    ComponenNotFoundError,
    WrongComponenStateError,
    UnsupporterPropertyTypeError
    )
from Acspy.Common.Log import getLogger
import ast
from Acspy.Common import CDBAccess  # these are necessary for python components
from Acspy.Util import XmlObjectifier  # as before

__version__ = "$Id$"


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
    # TODO: we should have PropertyType.BOOL_SEQ in the backend, but we don't
    # , so I remove support from them
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

    @staticmethod
    def get_property_type(rep_id):
        '''
        Returns the enum type of the property for the
        ND_Repository_ID of the property

        @param repID: The Np_Repository_Id of a property
        @type repID: string
        @return: The property following the backend definition
        @rtype: ctamonitoring.property_recorder.backend.property_type

        '''
        try:
            if PropertyTypeUtil._cbMap[rep_id] is None:
                raise UnsupporterPropertyTypeError(rep_id)
            else:
                return (
                    PropertyTypeUtil._cbMap[rep_id]
                )

        # If key error, then it is probably an enum
        except KeyError:
            return PropertyType.OBJECT

    @staticmethod
    def get_enum_prop_dict(prop):
        '''
        Creates an dictionary with  int_rep:str_rep

        This is needed in order to store the string representation of
        an enumeration, as the monitors use the integer
        representation by default.

        @param property: property object
        @type property: ACS._objref_<prop_type>
        @raise ValueError: if less than 2 states are found
        @raise AttributeError: no states description is found in the CDB
        @return: pair int_rep:str_rep of the enum
        @rtype: dict

        '''

        # TODO: make a logger at module level. Then activate the warninigd below
        logger = getLogger('ctamonitoring.property_recorder.util')

        try:
            enumValues = prop.get_characteristic_by_name(
                "statesDescription").value().split(', ')
        except Exception:
            #logger.logWarning('No statesDescription found in the CDB')
            raise AttributeError

        enumDict = {}
        i = 0
        for item in enumValues:
            string = str(i)
            enumDict[string] = item.strip()
            i += 1
        if len(enumDict) < 2:
            #logger.logWarning(
            #    'Less than 2 states found, no sense on using a string rep.')
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

        The 'hack' tries to get_sync the value of the property.
        When it fails, we can know that the property is not in a correct state
        '''
        try:
            acs_property.get_sync()
        except Exception:
            return False
        else:
            return True

    @staticmethod
    def is_archive_delta_enabled(archive_delta):
        '''
        To determine when archive delta is indeed disabled
        (Can be done in different ways)

        attributes - property attributes for"archive_delta"
                     or "archive_delta_percent"
        '''
        if (archive_delta is None
                or archive_delta is False
                or archive_delta == "0"
                or archive_delta == "0.0"
                or archive_delta == 0
                or archive_delta == 0.0):

            return False
        else:
            return True


class ComponentUtil(object):
    '''
    Used to determine if a component is characteristic,
    and if it is Python.

    Encapsulates some "hacking" which could be optimized later
    '''

    @staticmethod
    def is_characteristic_component(component):
        '''
        Checks is we can get the characteristics.

        Returns True is it is a characteristic component
        '''
        try:
            component.find_characteristic("*")
        except AttributeError:
            return False
        else:
            return True

    @staticmethod
    def is_python_char_component(component):
        '''
        Check if the component is a Python characteristic
        component.

        @return:  true if it is a python characteristic component,
        false if it a c++ or Java characteristic component
        @rtype: boolean
        @raise AttributeError: if it is not a characteristic component
        '''
        return (len(component.find_characteristic("*")) == 0)

    @staticmethod
    def is_a_property_recorder_component(component):
        return (component._NP_RepositoryId == constants.RECORDER_NP_REP_ID)

    @staticmethod
    def is_component_state_ok(comp_reference, component_id):
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

    @staticmethod
    def get_objectified_cdb(component):
        '''
        Obtains the list of properties from the CDB as objects
    
        This needs to be used for python characteristic components,
        as the property attributes are empty for those components.
        Would work for any component but the performance woulf be affected,
        and it is only recommended for Python components

        @returns: element list
        @rtype: xml.dom.minicompat.NodeList
        '''
        cdb = CDBAccess.cdb()
        componentCDBXML = cdb.get_DAO('alma/%s' % (component.name))
        cdb_entry = XmlObjectifier.XmlObject(componentCDBXML)
        return cdb_entry.getElementsByTagName("*")


class AttributeDecoder(object):
    '''
    Allows to decode the entries in the CDB doing the necessary parsing
    '''
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
        try:
            return ast.literal_eval(value)
        except SyntaxError:
            return None

    @staticmethod
    def _decode_ast_literal_hybrid(value):
        '''
        This is used with variables can be strings or numbers
        '''
        try:
            return AttributeDecoder._decode_ast_literal(value)
        # If exception then it is a string
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
        @raises ValueError:
        @raises TypeError
        '''
        if decode_method is DECODE_METHOD.NONE:
            return AttributeDecoder._decode_none(value)
        elif decode_method is DECODE_METHOD.AST_LITERAL:
            return AttributeDecoder._decode_ast_literal(value)
        elif decode_method is DECODE_METHOD.AST_LITERAL_HYBRID:
            return AttributeDecoder._decode_ast_literal_hybrid(value)
        elif decode_method is DECODE_METHOD.UTF8:
            return AttributeDecoder._decode_utf8(value)
        else:
            raise ValueError("decode_method is not supported")

    @staticmethod
    def decode_boolean(value):
        '''
        Returns a boolean when a cdb boolean attrib is provided,
        otherwise None
        '''
        try:
            decoded = AttributeDecoder._decode_ast_literal(value.title())
        except Exception:
            raise ValueError("could not decode value")
        if type(decoded) is not bool:
            raise TypeError("decoded value is not boolean")
        return decoded


class EnumUtil(object):
    '''
    This class allows to convert enums from and to strings
    '''
    @staticmethod
    def from_string(enum_type, name):
        '''
        To obtain the enum object from a string rep.

        Raises ValueError if type/value not recognized
        '''
        return enum_type._values[enum_type._keys.index(name)]

    @staticmethod
    def to_string(enum_value):
        '''
        Converts the enum into a string
        '''
        return enum_value.key
