'''
Tools to convert enums from and to strings

@author: igoroya
@organization: DESY
@copyright: cta-observatory.org
@version: $Id: util.py 2091 2018-04-06 14:25:24Z igoroya $
@change: $LastChangedDate: 2018-04-06 16:25:24 +0200 (Fri, 06 Apr 2018) $
@change: $LastChangedBy: igoroya $
'''


def from_string(enum_type, name):
    '''
    To obtain the enum object from a string rep.

    Raises KeyError if type/value not recognized
    '''
    return enum_type[name]

def to_string(enum_value):
    '''
    Converts the enum into a string
    '''
    return str(enum_value.name)
