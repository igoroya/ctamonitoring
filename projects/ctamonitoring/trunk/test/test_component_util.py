"""
Unit test module for util.component_util

This test mocks ACS components and properties.
See test_acs_integration for tests that use real ACS
components

@requires: testacsproperties
@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: unittest
@requires: ctamonitoring.property_recorder.util
@requires: logging
@requires: ctamonitoring.property_recorder.backend
@requires: ctamonitoring.property_recorder.constants
"""
import unittest
from mock import Mock
import CORBA
from ctamonitoring.property_recorder.util import component_util
from ctamonitoring.property_recorder.frontend_exceptions import (
    UnsupporterPropertyTypeError, ComponentNotFoundError,
    WrongComponentStateError)
from ctamonitoring.property_recorder.backend import property_type

__version__ = "$Id$"

PROPERTY_TYPE = property_type.PropertyType


class PropertyTypeUtilTest(unittest.TestCase):

    '''
    Tests operations related to the property type
    '''

    def test_get_enum_prop_dict(self):
        my_enum_prop = get_mock_enum_prop()
        decoded = component_util.get_enum_prop_dict(my_enum_prop)
        expected_value = {'0': 'STATE1', '1': 'STATE2', '2': 'STATE3'}
        self.assertEqual(expected_value, decoded)

        attrs = {'get_characteristic_by_name.side_effect': Exception}
        mock_prop = Mock()
        mock_prop.configure_mock(**attrs)

        self.assertRaises(
            AttributeError,
            component_util.get_enum_prop_dict,
            mock_prop
        )

        chars = CORBA.Any(CORBA.TC_string, 'STATE1')
        attrs = {'get_characteristic_by_name.return_value': chars}
        mock_prop = Mock()
        mock_prop.configure_mock(**attrs)

        self.assertRaises(
            ValueError,
            component_util.get_enum_prop_dict,
            mock_prop
        )

    def test_get_property_type(self):
        # my_component = self._my_acs_client.getComponent(
        #    "TEST_PROPERTIES_COMPONENT",
        #    True)

        my_component = get_mock_acs_component()

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_EnumTestROProp()._NP_RepositoryId),
            PROPERTY_TYPE.OBJECT
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_EnumTestRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.OBJECT
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleROProp()._NP_RepositoryId),
            PROPERTY_TYPE.DOUBLE
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatSeqRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.FLOAT_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longSeqRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_LONG
        )
        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.DOUBLE
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_booleanROProp()._NP_RepositoryId),
            PROPERTY_TYPE.BOOL
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleSeqROProp()._NP_RepositoryId),
            PROPERTY_TYPE.DOUBLE_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longLongROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_patternROProp()._NP_RepositoryId),
            PROPERTY_TYPE.BIT_FIELD
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_booleanRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.BOOL
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_doubleSeqRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.DOUBLE_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longLongRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_patternRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.BIT_FIELD
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongSeqROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_SEQ
        )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            component_util.get_property_type,
            my_component._get_booleanSeqROProp()._NP_RepositoryId
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatROProp()._NP_RepositoryId),
            PROPERTY_TYPE.FLOAT
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_stringROProp()._NP_RepositoryId),
            PROPERTY_TYPE.STRING
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongSeqRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_SEQ
        )

        self.assertRaises(
            UnsupporterPropertyTypeError,
            component_util.get_property_type,
            my_component._get_booleanSeqRWProp()._NP_RepositoryId
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.FLOAT
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_stringRWProp()._NP_RepositoryId),
            PROPERTY_TYPE.STRING
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_floatSeqROProp()._NP_RepositoryId),
            PROPERTY_TYPE.FLOAT_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_longSeqROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_SEQ
        )

        self.assertEqual(
            component_util.get_property_type(
                my_component._get_uLongLongROProp()._NP_RepositoryId),
            PROPERTY_TYPE.LONG_LONG
        )

    def test_is_archive_delta_enabled(self):

        # First test the cases when it should be false
        self.assertFalse(
            component_util.is_archive_delta_enabled(None)
        )
        self.assertFalse(
            component_util.is_archive_delta_enabled(False)
        )
        self.assertFalse(
            component_util.is_archive_delta_enabled("0")
        )
        self.assertFalse(
            component_util.is_archive_delta_enabled("0.0")
        )
        self.assertFalse(
            component_util.is_archive_delta_enabled(0)
        )
        self.assertFalse(
            component_util.is_archive_delta_enabled(0.0)
        )
        self.assertTrue(
            component_util.is_archive_delta_enabled(True)
        )

    def test_is_property_ok(self):

        attrs = {'get_sync.return_value': "_"}
        mock_prop = Mock()
        mock_prop.configure_mock(**attrs)

        self.assertTrue(
            component_util.is_property_ok(mock_prop)
        )

        attrs = {'get_sync.side_effect': Exception}
        mock_prop = Mock()
        mock_prop.configure_mock(**attrs)
        self.assertFalse(
            component_util.is_property_ok(mock_prop)
        )


class ComponentUtilTest(unittest.TestCase):

    '''
    Test operations at component level
    '''

    def test_is_char_comp(self):

        attrs = {'find_characteristic.return_value': '_'}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertTrue(
            component_util.is_characteristic_component(mock_component)
        )

        attrs = {'find_characteristic.side_effect': AttributeError}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertFalse(
            component_util.is_characteristic_component(mock_component)
        )

    def test_is_python_char_component(self):

        attrs = {'find_characteristic.return_value': []}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertTrue(
            component_util.is_python_char_component(mock_component)
        )

        attrs = {'find_characteristic.side_effect': AttributeError}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertRaises(
            Exception,
            component_util.is_python_char_component,
            mock_component
        )

        attrs = {'find_characteristic.return_value': ["_", "_"]}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertFalse(
            component_util.is_python_char_component(mock_component)
        )

    def test_is_a_prop_rec_comp(self):
        attrs = {'_NP_RepositoryId': 'IDL:cta/actl/PropertyRecorder:1.0'}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertTrue(
            component_util.is_a_property_recorder_component(mock_component)
        )

        attrs = {'_NP_RepositoryId': '_'}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertFalse(
            component_util.is_a_property_recorder_component(mock_component)
        )

    def test_is_component_state_ok(self):

        attrs = {'_get_componentState.return_value': "COMPSTATE_OPERATIONAL",
                 'name': "MOCK_COMPONENT"
                }
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertTrue(
            component_util.is_component_state_ok(
                mock_component)
        )

        attrs = {'_get_componentState.side_effect': Exception,
                 'name': "MOCK_COMPONENT"}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertRaises(
            ComponentNotFoundError,
            component_util.is_component_state_ok,
            mock_component
        )

        attrs = {'_get_componentState.return_value': "OTHER",
                 'name': "MOCK_COMPONENT"}
        mock_component = Mock()
        mock_component.configure_mock(**attrs)
        self.assertRaises(
            WrongComponentStateError,
            component_util.is_component_state_ok,
            mock_component
        )


def get_mock_property(repo_id):
    '''
    Mocks ACS properties, excluding enum properties
    '''
    attrs = {'_NP_RepositoryId': repo_id}
    mock_prop = Mock()
    mock_prop.configure_mock(**attrs)
    return mock_prop


def get_mock_enum_prop():
    '''
    Mocks enum ACS properties
    '''
    chars = CORBA.Any(CORBA.TC_string, 'STATE1, STATE2, STATE3')
    attrs = {'get_characteristic_by_name.return_value': chars}
    mock_prop = Mock()
    mock_prop.configure_mock(**attrs)
    return mock_prop
    # get_characteristic_by_name('statesDescription')


def get_mock_acs_component():
    '''
    Mocks ACS component with a set of properties
    '''
    attrs = {'_get_' + prop_name + '.return_value':
             get_mock_property(PROPS_REPO_IDS[prop_name])
             for prop_name in PROPS_REPO_IDS}
    mock_component = Mock()
    mock_component.configure_mock(**attrs)
    return mock_component


PROPS_REPO_IDS = {
    'doubleROProp': 'IDL:alma/ACS/ROdouble:1.0',
    'doubleRWProp': 'IDL:alma/ACS/RWdouble:1.0',
    'doubleSeqROProp': 'IDL:alma/ACS/ROdoubleSeq:1.0',
    'doubleSeqRWProp':  'IDL:alma/ACS/RWdoubleSeq:1.0',
    'floatROProp': 'IDL:alma/ACS/ROfloat:1.0',
    'floatRWProp': 'IDL:alma/ACS/RWfloat:1.0',
    'floatSeqROProp': 'IDL:alma/ACS/ROfloatSeq:1.0',
    'floatSeqRWProp': 'IDL:alma/ACS/RWfloatSeq:1.0',
    'longROProp': 'IDL:alma/ACS/ROlong:1.0',
    'longRWProp': 'IDL:alma/ACS/RWlong:1.0',
    'longSeqROProp': 'IDL:alma/ACS/ROlongSeq:1.0',
    'longSeqRWProp': 'IDL:alma/ACS/RWlongSeq:1.0',
    'uLongROProp': 'IDL:alma/ACS/ROuLong:1.0',
    'uLongRWProp': 'IDL:alma/ACS/RWuLong:1.0',
    'uLongSeqROProp': 'IDL:alma/ACS/ROuLongSeq:1.0',
    'uLongSeqRWProp': 'IDL:alma/ACS/RWuLongSeq:1.0',
    'longLongROProp': 'IDL:alma/ACS/ROlongLong:1.0',
    'longLongRWProp': 'IDL:alma/ACS/RWlongLong:1.0',
    'longLongSeqROProp': 'IDL:alma/ACS/ROlongLongSeq:1.0',
    'longLongSeqRWProp': 'IDL:alma/ACS/RWlongLongSeq:1.0',
    'uLongLongROProp': 'IDL:alma/ACS/ROuLongLong:1.0',
    'uLongLongRWProp': 'IDL:alma/ACS/RWuLongLong:1.0',
    'uLongLongSeqROProp': 'IDL:alma/ACS/ROuLogLongSeq:1.0',
    'uLongLongSeqRWProp': 'IDL:alma/ACS/RWuLongLongSeq:1.0',
    'booleanROProp': 'IDL:alma/ACS/ROboolean:1.0',
    'booleanRWProp': 'IDL:alma/ACS/RWboolean:1.0',
    'booleanSeqROProp': 'IDL:alma/ACS/RObooleanSeq:1.0',
    'booleanSeqRWProp': 'IDL:alma/ACS/RWbooleanSeq:1.0',
    'patternROProp': 'IDL:alma/ACS/ROpattern:1.0',
    'patternRWProp': 'IDL:alma/ACS/RWpattern:1.0',
    'patternSeqROProp': 'IDL:alma/ACS/ROpatternSeq:1.0',
    'patternSeqRWProp': 'IDL:alma/ACS/RWpatternSeq:1.0',
    'stringROProp': 'IDL:alma/ACS/ROstring:1.0',
    'stringRWProp': 'IDL:alma/ACS/RWstring:1.0',
    'stringSeqROProp': 'IDL:alma/ACS/ROstringSeq:1.0',
    'stringSeqRWProp': 'IDL:alma/ACS/RWstringSeq:1.0',
    'EnumTestROProp': 'IDL:cta/actl/ROEnumTest:1.0',
    'EnumTestRWProp': 'IDL:cta/actl/RWEnumTest:1.0'
}


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(PropertyTypeUtilTest))
suite.addTest(unittest.makeSuite(ComponentUtilTest))


if __name__ == "__main__":
    unittest.main(defaultTest='suite')
