'''
Created on 6 Apr 2018

@author: igoroya
'''
import unittest
from enum import Enum
from ctamonitoring.property_recorder.util import (enum_util)

class enum_util_test(unittest.TestCase):

    def test_to_string(self):
        test_enum = Enum('test_enum', 'DUMMY LOG MYSQL MONGODB')
        self.assertEqual(
            'DUMMY',
            enum_util.to_string(test_enum.DUMMY)
            )

    def test_from_string(self):
        test_enum = Enum('test_enum', 'DUMMY LOG MYSQL MONGODB')
        self.assertEqual(
            test_enum.LOG,
            enum_util.from_string(test_enum, 'LOG')
            )

        self.assertRaises(
            KeyError,
            enum_util.from_string,
            test_enum, 'NOPE')

if __name__ == '__main__':
    unittest.main()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(enum_util_test))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests
