"""
Tools to convert enums from and to strings

@author: igoroya
@organization: DESY
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""


def from_string(enum_type, name):
    """
    To obtain the enum object from a string rep.

    Raises KeyError if type/value not recognized
    """
    return enum_type[name]


def to_string(enum_value):
    """
    Converts the enum into a string
    """
    return str(enum_value.name)
