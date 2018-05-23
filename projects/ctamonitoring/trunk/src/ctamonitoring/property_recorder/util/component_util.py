'''
Contains some helper functions to be of used in the module

Most of the "hacks" that are needed to make the property
recorder to work are included here

@author: igoroya
@organization: DESY
@copyright: cta-observatory.org
@version: $Id: util.py 2091 2018-04-06 14:25:24Z igoroya $
@change: $LastChangedDate: 2018-04-06 16:25:24 +0200 (Fri, 06 Apr 2018) $
@change: $LastChangedBy: igoroya $
'''
from ctamonitoring.property_recorder.backend import property_type
from ctamonitoring.property_recorder import constants

from ctamonitoring.property_recorder.frontend_exceptions import (
    ComponentNotFoundError,
    WrongComponentStateError,
    UnsupporterPropertyTypeError
    )
from Acspy.Common.Log import getLogger

from Acspy.Common import CDBAccess  # these are necessary for python components
from Acspy.Util import XmlObjectifier  # as before

__version__ = "$Id: componnent_util.py 2091 2018-04-06 14:25:24Z igoroya $"


PropertyType = property_type.PropertyType


property_primitives = {}
property_primitives[constants.RODOUBLE_NP_REP_ID] = PropertyType.DOUBLE
property_primitives[constants.RWDOUBLE_NP_REP_ID] = PropertyType.DOUBLE
property_primitives[constants.RODOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
property_primitives[constants.RWDOUBLESEQ_NP_REP_ID] = PropertyType.DOUBLE_SEQ
property_primitives[constants.ROFLOAT_NP_REP_ID] = PropertyType.FLOAT
property_primitives[constants.RWFLOAT_NP_REP_ID] = PropertyType.FLOAT
property_primitives[constants.ROFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
property_primitives[constants.RWFLOATSEQ_NP_REP_ID] = PropertyType.FLOAT_SEQ
property_primitives[constants.ROLONG_NP_REP_ID] = PropertyType.LONG
property_primitives[constants.RWLONG_NP_REP_ID] = PropertyType.LONG
property_primitives[constants.ROLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
property_primitives[constants.RWLONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
property_primitives[constants.ROULONG_NP_REP_ID] = PropertyType.LONG
property_primitives[constants.RWULONG_NP_REP_ID] = PropertyType.LONG
property_primitives[constants.ROULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
property_primitives[constants.RWULONGSEQ_NP_REP_ID] = PropertyType.LONG_SEQ
property_primitives[constants.ROLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
property_primitives[constants.RWLONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
# longLongSeq unsupported in ACS
property_primitives[constants.ROLONGLONGSEQ_NP_REP_ID] = None
property_primitives[constants.RWLONGLONGSEQ_NP_REP_ID] = None
property_primitives[constants.ROULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
property_primitives[constants.RWULONGLONG_NP_REP_ID] = PropertyType.LONG_LONG
property_primitives[constants.ROULONGLONGSEQ_NP_REP_ID] = None
property_primitives[constants.RWULONGLONGSEQ_NP_REP_ID] = None
property_primitives[constants.ROBOOLEAN_NP_REP_ID] = PropertyType.BOOL
property_primitives[constants.RWBOOLEAN_NP_REP_ID] = PropertyType.BOOL
# TODO: we should have PropertyType.BOOL_SEQ in the backend, but we don't
# , so I remove support from them
property_primitives[constants.ROBOOLEANSEQ_NP_REP_ID] = None
property_primitives[constants.RWBOOLEANSEQ_NP_REP_ID] = None
property_primitives[constants.ROPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
property_primitives[constants.RWPATTERN_NP_REP_ID] = PropertyType.BIT_FIELD
# patternSeq not supported
property_primitives[constants.ROPATTERNSEQ_NP_REP_ID] = None
property_primitives[constants.RWPATTERNSEQ_NP_REP_ID] = None
property_primitives[constants.ROSTRING_NP_REP_ID] = PropertyType.STRING
property_primitives[constants.RWSTRING_NP_REP_ID] = PropertyType.STRING
property_primitives[constants.ROSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ
property_primitives[constants.RWSTRINGSEQ_NP_REP_ID] = PropertyType.STRING_SEQ


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
            if property_primitives[rep_id] is None:
                raise UnsupporterPropertyTypeError(rep_id)
            else:
                return (
                    property_primitives[rep_id]
                )

        # If key error, then it is probably an enum, represented as OBJECT type
        except KeyError:
            return PropertyType.OBJECT


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
        try:
            enumValues = prop.get_characteristic_by_name(
                "statesDescription").value().split(', ')
        except Exception:
            raise AttributeError

        enumDict = {}
        i = 0
        for item in enumValues:
            string = str(i)
            enumDict[string] = item.strip()
            i += 1
        if len(enumDict) < 2:
            # if less than 2 states found, no sense on using a string rep
            raise ValueError

        return enumDict


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


def is_a_property_recorder_component(component):
        return (component._NP_RepositoryId == constants.RECORDER_NP_REP_ID)


def is_component_state_ok(comp_reference):
        '''
        Check if the component is still operational

        component -- the reference to an ACS component

        returns True is OK

        Raises:
        ComponentNotFoundError -- component is not present
        WrongComponentStateError -- component is present, but in wrong state
        '''

        state = None

        try:
            state = str(comp_reference._get_componentState())
        except Exception:
            raise ComponentNotFoundError(comp_reference.name)

        if (state != "COMPSTATE_OPERATIONAL"):
            raise WrongComponentStateError(comp_reference.name, state)

        return True


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
