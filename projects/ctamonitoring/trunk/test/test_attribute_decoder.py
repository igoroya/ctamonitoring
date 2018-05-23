#!/usr/bin/env python
__version__ = "$Id: test_util.py 1654 2015-12-22 11:07:42Z igoroya $"
'''
Unit test module for util

This test requires a proper ACS component to run. For that,
the module testacsproperties is used.

@requires: testacsproperties

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: test_attribute_decoder.py 1168 2015-04-13 18:42:27Z igoroya $
@change: $LastChangedDate: 2015-04-13 20:42:27 +0200 (Mon, 13 Apr 2015) $
@change: $LastChangedBy: igoroya $
@requires: unittest
@requires: ctamonitoring.property_recorder.util
@requires: logging
@requires: ctamonitoring.property_recorder.backend
@requires: enum
@requires: ctamonitoring.property_recorder.constants
'''

import unittest
from ctamonitoring.property_recorder.util import attribute_decoder
from ctamonitoring.property_recorder.constants import DECODE_METHOD

class AttributeDecoderTest(unittest.TestCase):

    def test_decode_boolean(self):
        cdb_boolean = 'true'
        self.assertTrue(attribute_decoder.decode_boolean(cdb_boolean))
        cdb_boolean = 'false'
        self.assertFalse(attribute_decoder.decode_boolean(cdb_boolean))

    def test_decode_attribute(self):
        a_num = '1'
        a_no_decode = 'hello'
        a_utf_8 = "my_text".encode('utf-8')

        self.assertEqual(
            1,
            attribute_decoder.decode_attribute(
                a_num,
                DECODE_METHOD.AST_LITERAL
                )
            )

        self.assertEqual(
            1,
            attribute_decoder.decode_attribute(
                a_num,
                DECODE_METHOD.AST_LITERAL_HYBRID
                )
            )

        self.assertEqual(
            'hello',
            attribute_decoder.decode_attribute(
                a_no_decode,
                DECODE_METHOD.NONE
                )
            )

        self.assertEqual(
            'hello',
            attribute_decoder.decode_attribute(
                a_no_decode,
                DECODE_METHOD.AST_LITERAL_HYBRID
                )
            )

        self.assertEqual(
            'my_text',
            attribute_decoder.decode_attribute(
                a_utf_8,
                DECODE_METHOD.UTF8
                )
            )

if __name__ == '__main__':
    unittest.main()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AttributeDecoderTest))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='suite')  # run all tests