__version__ = "$Id: recorder_exceptions.py 594 2013-09-15 15:27:57Z igoroya $"



'''
Contains exceptions that could be raised by the front-end module

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id: recorder_exceptions.py 566 2013-08-26 16:30:31Z igoroya $
@change: $LastChangedDate: 2013-08-26 18:30:31 +0200 (Mon, 26 Aug 2013) $, $LastChangedBy: igoroya $
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
        retVal = "component, " + str(self.component_id) + "not found"
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


