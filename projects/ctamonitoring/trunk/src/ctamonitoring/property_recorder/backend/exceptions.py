__version__ = "$Id$"


'''
Errors that could be raised by backends.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: ctamonitoring.property_recorder.backend.property_type
'''


class UnsupportedPropertyTypeError(Exception):
    '''
    Raised during registration if a backend doesn't support a given property type.
    
    This is quiet possible with "complex" property types such as sequences or objects.
    '''
    def __init__(self, property_type, msg = ""):
        '''
        ctor.
    
        @param property_type: The property type.
        @type property_type: ctamonitoring.property_recorder.backend.property_type.PropertyType
        @param msg: Additional information. Optional("").
        @param msg: string
        '''
        self.property_type = property_type
        self.msg = msg
    
    def __str__(self):
        retVal = "unsupported property type, " + str(self.property_type)
        if self.msg:
            retVal += ": " + self.msg
        return retVal


class InterruptedException(Exception):
    '''
    Raised during the call to a blocking method if the event it is waiting for
    never occurs. It is often useful for long-running non-blocking methods to
    raise an InterruptedException too.
    '''
    pass

