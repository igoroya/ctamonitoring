"""
Unit test module for util.attribute_decoder

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: unittest
@requires: ctamonitoring.property_recorder.util.attribute_decoder
@requires: ctamonitoring.property_recorder.constants
"""
import unittest
from ctamonitoring.property_recorder.util import attribute_decoder
from ctamonitoring.property_recorder.constants import DECODE_METHOD

__version__ = "$Id$"


class AttributeDecoderTest(unittest.TestCase):

    def test_decode_boolean(self):
        cdb_boolean = 'true'
        self.assertTrue(attribute_decoder.decode_boolean(cdb_boolean))

        cdb_boolean = 'false'
        self.assertFalse(attribute_decoder.decode_boolean(cdb_boolean))

        self.assertRaises(
            ValueError,
            attribute_decoder.decode_boolean,
            'wrong'
        )

        self.assertRaises(
            TypeError,
            attribute_decoder.decode_boolean,
            '1'
        )

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
            None,
            attribute_decoder.decode_attribute(
                '1+',
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

        self.assertRaises(
            ValueError,
            attribute_decoder.decode_attribute,
            a_utf_8,
            "WRONG"
        )

        self.assertEqual(
            None,
            attribute_decoder.decode_attribute(
                '\xd0',
                DECODE_METHOD.UTF8
            )
        )


if __name__ == '__main__':
    unittest.main()


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(AttributeDecoderTest))

if __name__ == "__main__":
    unittest.main(defaultTest='suite')
