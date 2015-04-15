'''
Unit test module for config

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''
import unittest
from ctamonitoring.property_recorder.config import RecorderConfig
from ctamonitoring.property_recorder.config import BackendType

__version__ = '$Id$'


class Defaults:

    default_timer_trigger = 60.0
    max_comps = 100
    max_props = 1000
    checking_period = 10  # seconds
    backend_type = BackendType.LOG
    components = set()
    backend_config = None
    is_include_mode = False


class RecorderConfigTest(unittest.TestCase):

    a_long = 150L
    a_float = 0.8
    a_neg_long = -1L
    a_string = 'a'
    a_string_set = set(['a', 'b'])
    a_hybrid_set = set(['a', 1])
    a_backend_type = BackendType.MONGODB

    def setUp(self):
        self.recoder_config = RecorderConfig()

    def test_default_timer_trigger(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.default_timer_trigger,
            Defaults.default_timer_trigger)

        self.recoder_config.default_timer_trigger = self.a_float
        self.assertEqual(
            self.recoder_config.default_timer_trigger,
            self.a_float)

        self.assertRaises(
            ValueError, setattr,
            self.recoder_config,
            'default_timer_trigger',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'default_timer_trigger',
            self.a_string)

    def test_max_comps(self):
        # check the default value
        self.assertEqual(self.recoder_config.max_comps, Defaults.max_comps)

        self.recoder_config.max_comps = self.a_long
        self.assertEqual(self.recoder_config.max_comps, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_comps',
            self.a_string)

    def test_max_props(self):
        # check the default value
        self.assertEqual(self.recoder_config.max_props, Defaults.max_props)

        self.recoder_config.max_props = self.a_long
        self.assertEqual(self.recoder_config.max_props, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_neg_long)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'max_props',
            self.a_string)

    def test_checking_period(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.checking_period,
            Defaults.checking_period)

        self.recoder_config.checking_period = self.a_long
        self.assertEqual(self.recoder_config.checking_period, self.a_long)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'checking_period',
            self.a_neg_long)
        self.assertRaises(
            ValueError, setattr,
            self.recoder_config,
            'checking_period',
            self.a_float)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'checking_period',
            self.a_string)

    def test_backend_type(self):
        # check the default value
        self.assertEqual(
            self.recoder_config.backend_type,
            Defaults.backend_type)

        self.recoder_config.backend_type = self.a_backend_type
        self.assertEqual(self.recoder_config.backend_type, self.a_backend_type)

        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'backend_type',
            self.a_string)
        self.assertRaises(
            ValueError,
            setattr,
            self.recoder_config,
            'backend_type',
            self.a_long)

    def test_is_include_mode(self):
        self.recoder_config.is_include_mode = True
        self.assertTrue(self.recoder_config.is_include_mode)

        self.recoder_config.is_include_mode = False
        self.assertFalse(self.recoder_config.is_include_mode)
        # should raise an exception for other data types
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_long)
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_float)
        self.assertRaises(
            TypeError,
            setattr,
            self.recoder_config,
            'is_include_mode',
            self.a_string)

    def test_components(self):

        self.assertRaises(
            NotImplementedError,
            setattr,
            self.recoder_config,
            'components',
            self.a_string_set)

        self.recoder_config.set_components(self.a_string_set)
        self.assertEquals(self.recoder_config.components, self.a_string_set)

        self.assertRaises(
            TypeError,
            self.recoder_config.set_components,
            self.a_float)

        self.assertRaises(
            TypeError,
            self.recoder_config.set_components,
            self.a_hybrid_set)


if __name__ == '__main__':
    unittest.main()

# suite = unittest.TestLoader().loadTestsFromTestCase(RecorderConfigTest)
# unittest.TextTestRunner(verbosity=2).run(suite)
