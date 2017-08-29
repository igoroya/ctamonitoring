__version__ = "$Id$"


"""
Little helpers that a backend might find useful...

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: datetime
@requires: Acspy.Common.TimeHelper eventually
@requires: ctamonitoring.property_recorder.backend.property_type
"""


from datetime import datetime
from datetime import timedelta
from ctamonitoring.property_recorder.backend.property_type import PropertyType
try:
    from Acspy.Common.TimeHelper import TimeUtil

    def to_posixtime(tm):
        """
        Convert an ACS epoch to a POSIX timestamp...

        ...such as is returned by time.time().

        @param tm: A time in 100 nanoseconds that have passed since
        October 15, 1582.
        @type tm: acstime.Epoch
        @return: The POSIX timestamp.
        @rtype: float
        """
        return TimeUtil().epoch2py(tm)

    def to_datetime(tm):
        """
        Convert an ACS epoch to a date + time.

        @param tm: A time in 100 nanoseconds that have passed since
        October 15, 1582.
        @type tm: acstime.Epoch
        @return: Date + time.
        @rtype: datetime.datetime
        """
        return datetime.utcfromtimestamp(to_posixtime(tm))
except ImportError:
    # assume time information is a POSIX timestamp, such as is returned
    # by time.time(), or a datetime.datetime if this doesn't run in an
    # ACS system
    def to_posixtime(tm):
        """
        Convert a date + time to a POSIX timestamp...

        ...or keep it a POSIX timestamp eventually.

        @param tm: A time in seconds that have passed since January 1, 1970.
        @type tm: integer or floating point number or datetime.datetime
        @return: Date + time.
        @rtype: datetime.datetime
        """
        if isinstance(tm, datetime):
            return get_total_seconds(tm - datetime.utcfromtimestamp(0), False)
        return tm

    def to_datetime(tm):
        """
        Convert a POSIX timestamp to a date + time...

        ...or keep it a date + time eventually.

        @param tm: A time in seconds that have passed since January 1, 1970.
        @type tm: integer or floating point number or datetime.datetime
        @return: Date + time.
        @rtype: datetime.datetime
        """
        if not isinstance(tm, datetime):
            return datetime.utcfromtimestamp(tm)
        return tm


def get_total_seconds(td, ignore_fractions_of_seconds=False):
    """
    Get the total number of seconds contained in a time duration.

    @param td: The time duration.
    @type td: datetime.timedelta
    @param ignore_fractions_of_seconds: Return the number of seconds
    without its fractions or not. Optional, default is False.
    @type ignore_fractions_of_seconds: boolean
    @return: The number of seconds in td.
    @rtype: long or float
    @note: For very large time durations this method may loose accuracy.
    """
    try:
        if ignore_fractions_of_seconds:
            return long(td.total_seconds())
        else:
            return td.total_seconds()
    except AttributeError:
        pass

    if ignore_fractions_of_seconds:
        microseconds = td.microseconds
    else:
        microseconds = float(td.microseconds)
    return (microseconds + (td.seconds +
                            td.days*24L*3600L) * 10**6L) / 10**6L


def get_floor(tm, td, ignore_fractions_of_seconds=True):
    """
    Get the floor is computed and the remainder (if any) is thrown away.

    @param tm: A date + time.
    @type tm: datetime.datetime
    @param td: A time duration that defines the time grid.
    @type td: datetime.timedelta
    @param ignore_fractions_of_seconds: Ignore fractions of seconds or not.
    Optional, default is True.
    @type ignore_fractions_of_seconds: boolean
    @return: The floor of tm.
    @rtype: datetime.datetime
    """
    flag = ignore_fractions_of_seconds
    duration = get_total_seconds(td, flag)
    tmp = tm - datetime.min
    tmp = timedelta(seconds=(get_total_seconds(tmp, flag) //
                             duration) * duration)
    return datetime.min + tmp


def to_string(dt, property_type, property_type_desc=None):
    """
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
    """
    if property_type is PropertyType.ENUMERATION:
        return property_type_desc[dt]
    elif property_type is PropertyType.BIT_FIELD:
        return bin(dt)
    return str(dt)


def get_enum_desc_key_type(property_type_desc):
    """
    Get the key type of an enum's property type description.

    @param property_type_desc: The property type description.
    @type property_type_desc: dict
    @return: basestring or int
    """
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
    """
    Get an enum's inverted property type description.

    The property type description usually is a dictionary that maps
    enum tags to enum integer value. The inverted one maps integers to tags.

    @param property_type_desc: The property type description.
    @type property_type_desc: dict
    @return: The inverted property type description.
    @rtype: dict
    """
    if get_enum_desc_key_type(property_type_desc) is basestring:
        retVal = dict((v, k) for k, v in property_type_desc.iteritems())
        if len(retVal) != len(property_type_desc):
            raise ValueError("duplicated enum values")
        return retVal
    return property_type_desc
