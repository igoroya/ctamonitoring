__version__ = "$Id$"



'''
Contains exceptions that could be raised by the front-end module

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$, $LastChangedBy$
'''


class ComponenNotFoundError(Exception):
    '''
    When a component entry is not found when is was indeed expected
    '''
    def __init__(self, component_id, msg = ""):
        '''
        ctor.
    
        @param component_id: The id of the component
        @type component_id: string
        @param msg: Additional information. Optional("").
        @param msg: string
        '''
        self.component_id = component_id
        self.msg = msg
    
    def __str__(self):
        retVal = "component, " + str(self.component_id) + " not found"
        if self.msg:
            retVal += ": " + self.msg
        return retVal


class WrongComponenStateError(Exception):
    '''
    When a component entry is existing but with a wrong state
    '''
    def __init__(self, component_id, comp_state, msg = ""):
        '''
        ctor.
    
        @param component_id: The id of the component
        @type property_type: string
        @param comp_state: The id of the component
        @type comp_state: string
        @param msg: Additional information. Optional("").
        @param msg: string
        '''
        self.component_id = component_id
        self.comp_state = comp_state
        self.msg = msg
    
    def __str__(self):
        retVal = ("component, " + 
                  str(self.component_id) + 
                " found in wrong state: "+ 
                str(self.comp_state)
        )            
        if self.msg:
            retVal += ": " + self.msg
        return retVal

class UnsupporterPropertyTypeError(Exception):
    '''
    When property type is not recognized or supported
    '''
    def __init__(self, property_rep_id, msg = ""):
        '''
        ctor.
    
        @param property_rep_id: The property repository id
        @type property_rep_id: string
        @param msg: Additional information. Optional("").
        @param msg: string
        '''
        self.property_rep_id = property_rep_id
        self.msg = msg
    
    def __str__(self):
        retVal = ("Property type: " + 
                  str(self.property_rep_id) + 
                " is not supported "
        )            
        if self.msg:
            retVal += ": " + self.msg
        return retVal
    
class BadCdbRecorderConfig(Exception):
    '''
    When the config of the recorder stored in the CDB is not correct
    
    TODO: Not used! Should be removed?
    '''
    def __init__(self, cdb_entry_id, msg = ""):
        '''
        ctor.
    
        @param cdb_entry_id: The entry in the Cdb which was wrong
        @type cdb_entry_id: string
        @param msg: Additional information. Optional("").
        @param msg: string
        '''
        self.cdb_entry_id = cdb_entry_id
        self.msg = msg
    
    def __str__(self):
        retVal = ("The entry fot: " + 
                  str(self.cdb_entry_id) + 
                " is not correct in the component CDB "
        )            
        if self.msg:
            retVal += ": " + self.msg
        return retVal
