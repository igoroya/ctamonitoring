__version__ = "$Id: util.py 592 2013-09-12 02:01:43Z tschmidt $"


'''
Little helpers that a backend might find useful...

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: util.py 592 2013-09-12 02:01:43Z tschmidt $
@change: $LastChangedDate: 2013-09-12 04:01:43 +0200 (Thu, 12 Sep 2013) $
@change: $LastChangedBy: tschmidt $
@requires: datetime
@requires: Acspy.Common.TimeHelper eventually
@requires: ctamonitoring.property_recorder.backend.property_type
'''


from datetime import datetime
from datetime import timedelta
try:
    from Acspy.Common.TimeHelper import TimeUtil
    def to_datetime(tm):
        '''
        Convert an ACS epoch to a date + time.
        
        @param tm: A time in 100 nanoseconds that have passed since
        October 15, 1582.
        @type tm: long or acstime.Epoch
        @return: Date + time.
        @rtype: datetime.datetime
        '''
        return datetime.utcfromtimestamp(TimeUtil().epoch2py(tm))
except ImportError:
    # assume time information is a POSIX timestamp, such as is returned
    # by time.time(), or a datetime.datetime if this doesn't run in an ACS system
    def to_datetime(tm):
        '''
        Convert POSIX timestamp to a date + time or keep it a date + time eventually.
        
        @param tm: A time in seconds that have passed since January 1, 1970.
        @type tm: integer or floating point number or datetime.datetime
        @return: Date + time.
        @rtype: datetime.datetime
        '''
        if not isinstance(tm, datetime):
            return datetime.utcfromtimestamp(tm)
        return tm


def get_total_seconds(td):
    '''
    Get the total number of seconds contained in a time duration.
    
    @param td: The time duration.
    @type td: datetime.timedelta
    @return: The number seconds in td.
    @rtype: long
    @note: For very large time durations this method may loose accuracy.
    '''
    total_seconds = (td.microseconds + (td.seconds +
                                        td.days * 24L * 3600L) * 10**6L) / 10**6L
    return total_seconds


def get_floor(tm, td):
    '''
    Get the floor is computed and the remainder (if any) is thrown away.
    
    @param tm: A date + time.
    @type tm: datetime.datetime
    @param td: A time duration that defines the time grid.
    @type td: datetime.timedelta
    @return: The floor of tm.
    @rtype: datetime.datetime
    '''
    tmp = tm - datetime.min
    tmp = timedelta(seconds=(get_total_seconds(tmp) // get_total_seconds(td)) *
                            get_total_seconds(td))
    return datetime.min + tmp


from ctamonitoring.property_recorder.backend.property_type import PropertyType
def to_string(dt, property_type, property_type_desc = None):
    '''
    Get a printable string representation of a property value.
    
    Most property types can convert to string easily using str(). However,
    PropertyType.ENUMERATION and PropertyType.BIT_FIELD don't since the
    their standard representation is an integer.
    to_string() uses for enumerations the inverted property type description
    to map integer values to their "string representation". Bit fields are
    represented by a binary string (cf. bin()).
    
    @param dt: A property value.
    @param property_type: The property type.
    @type property_type: ctamonitoring.property_recorder.backend.property_type.PropertyType
    @param property_type_desc: The property type description.
    Enums need additional information to convert into a string.
    To relate an enum integer values to a "tag" one should provide a dictionary
    "values -> tags" here (inverted property type description). Optional(None).
    @type property_type_desc: typically dict
    @return: The printable string representation of the property value.
    @rtype: string
    '''
    if property_type is PropertyType.ENUMERATION:
        return property_type_desc[dt]
    elif property_type is PropertyType.BIT_FIELD:
        return bin(dt)
    return str(dt)


def get_enum_desc_key_type(property_type_desc):
    '''
    Get the key type of an enum's property type description.
    
    @param property_type_desc: The property type description.
    @type property_type_desc: dict
    @return: basestring or int
    '''
    retVal = None
    for key in property_type_desc.keys():
        if isinstance(key, basestring):
            if retVal and retVal is not basestring:
                raise TypeError("an enum description shouldn't mix key types")
            retVal = basestring
        elif isinstance(key, (int, long)):
            if retVal and retVal is not int:
                raise TypeError("an enum description shouldn't mix key types")
            retVal = int
        else:
            raise TypeError("an enum description only uses string and integer keys")
    if not len(property_type_desc):
        raise ValueError("enum description has no entries")
    return retVal

def get_enum_inverted_desc(property_type_desc):
    '''
    Get an enum's inverted property type description.
    The property type description usually is a dictionary that maps
    enum tags to enum integer value. The inverted one maps integers to tags.
    
    @param property_type_desc: The property type description.
    @type property_type_desc: dict
    @return: The inverted property type description.
    @rtype: dict
    '''
    if get_enum_desc_key_type(property_type_desc) is basestring:
        retVal = dict((v,k) for k, v in property_type_desc.iteritems())
        if len(retVal) != len (property_type_desc):
            raise ValueError("duplicated enum values")
        return retVal
    return property_type_desc
