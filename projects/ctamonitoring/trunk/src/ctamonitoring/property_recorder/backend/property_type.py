__version__ = "$Id$"


"""
The property type describes what data is stored in a backend.

Some backends may work schemaless but others may need to know type information.
In any way, the property type information will be useful to analyze
data sufficiently.

@note: Some backends may define additional/alternative types
to describe the property type. However, these should only be used internally
or within the backend's data representation.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: Enum
"""


from enum import Enum


PropertyType = Enum('PropertyType', 'FLOAT DOUBLE LONG LONG_LONG '
                    'STRING BIT_FIELD ENUMERATION BOOL '
                    'FLOAT_SEQ DOUBLE_SEQ LONG_SEQ LONG_LONG_SEQ '
                    'STRING_SEQ BIT_FIELD_SEQ ENUMERATION_SEQ BOOL_SEQ '
                    'OBJECT')
