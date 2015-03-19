__version__ = "$Id: property_type.py 602 2013-09-25 00:40:12Z tschmidt $"


'''
The property type describes what data is stored in a backend.

Some backends may work schemaless but others may need to know type information.
In any way, the property type information will be useful to analyze data sufficiently.

@note: Some backends may define additional/alternative types
to describe the property type. However, these should only be used internally
or within the backend's data representation.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: property_type.py 602 2013-09-25 00:40:12Z tschmidt $
@change: $LastChangedDate: 2013-09-25 02:40:12 +0200 (Wed, 25 Sep 2013) $
@change: $LastChangedBy: tschmidt $
@requires: Enum
'''


from enum import Enum


PropertyType = Enum('FLOAT', 'DOUBLE', 'LONG', 'LONG_LONG',
                    'STRING', 'BIT_FIELD', 'ENUMERATION', 'BOOL',
                    'FLOAT_SEQ', 'DOUBLE_SEQ', 'LONG_SEQ', 'LONG_LONG_SEQ',
                    'STRING_SEQ', 'BIT_FIELD_SEQ', 'ENUMERATION_SEQ', 'BOOL_SEQ',
                    'OBJECT')
