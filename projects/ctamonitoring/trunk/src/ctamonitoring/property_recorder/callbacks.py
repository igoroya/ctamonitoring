'''
This module includes the implementations of Python ACS callback
classes for use in the PropertyRecorder component. The purpose
of these callbacks is to store the data into the different backends
of the property recorders

BaseArchCB is a base class containing the base functionality
ArchCBXXX deals for the XXX type ACS property.
ArchCBpatternStringRep allows to insert the string representation of a Enum.


@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$, $LastChangedBy$
'''

#-------------------------------------------------
import ACS__POA   # Import the Python CORBA stubs for BACI
from omniORB.CORBA import TRUE
from ctamonitoring.property_recorder import constants
import logging
#---------------------------------------------------

# Create our own enum type


def enum(**enums):
    return type('Enum', (), enums)


class BaseArchCB:

    '''
    This class contains the implementation of the
    callback basic operations, with a common for all the used callbacks.

    Method working() and done() are invoked by the
    monitor created by the recorder.

    When monitor is done a flush() order is issued to the buffer

    Keyword arguments:
        name         -- of this callback instance
        buffer       -- buffer from the backend registry
        logger       -- logger to be used

    Attributes:
        - status -- Status of the Callback,
                    following acs required states:
                    INIT; WORKING, DONE
        - buffer -- with the data
        - name   -- Name of the property

    Raises:
        ValueError -- if no name is given to the property

    '''
    #--------------------------------------------------

    def __init__(self, name, buffer, logger):
        '''
        Constructor.

        What happens if the completion is not null?
        Should we store something (-1) or have a tag OK in all positions?

        logger -- default value is a console logger with level DEBUG
        '''

        # If there is no name then we do not want to store anything
        if name is not None:
            self.name = name
        else:
            raise ValueError("no name was given to the property")

        # collection where the data should be stored. Expected:
        # deque type. If none is provided, the only local storage is performed
        if buffer is None:
            raise ValueError("no archive buffer was provided")
        else:
            self.buffer = buffer

        # If there no logger is provided, then by default I will log into the
        # console
        if logger is None:
            self._logger = logging.getLogger()
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            self._logger.addHandler(ch)
        else:
            self._logger = logger
        # Flag for the application to check if the action is still going on
        # and if the callback has arrived.
        self.status = 'INIT'

    #------------------------------------------------
    def working(self, value, completion, desc):
        '''
        Method invoked by the monitor according to the
        configuration (at a certain rate of value change)
        It sends the requested values and completion of the property
        as read to the backend

        Parameters:
        - value is the value we are interested in
        - completion is a CORBA completion structure
        - desc is callback struct description

        Returns:
            Nothing

        Raises:
            Nothing
        '''

        self._logger.logDebug('Monitor of ' 
                              + self.name + ', WORKING, value read is: ' 
                              + str(value) + '  time: ' 
                              + str(completion.timeStamp) 
                              + ' type: ' + str(completion.type) + ' code: '
                              + str(completion.code))      
        
        #Do not write the value if an exception happened, but notify
        if completion.type != 0:
            self._logger.logWarning('Property: '+ self.name + ' completion type: ' 
                                    + ' type: ' + str(completion.type)
                                    + ' code: '
                                    + str(completion.code)
                                    +', data is not stored')           
           
        else:     
            self.buffer.add(completion.timeStamp, value)

        
        # If in the future we want to take care of completions types and code then:
        # self.buffer.add(completion.timeStamp,  value, completion.type
        # completion.code)

        # test the dir of the read types, to see if can do better with the enum
        #readValue = [self.name, value, timestamp, completion]
        # Check that the buffer is not full?
        # len(queue)
        # Save the value for later use
        completion = None
        # to make pychecker happy
        desc = None

        # Set flag.
        self.status = 'WORKING'
    #---------------------------------------------

    def done(self, value, completion, desc):
        '''
        Invoked asynchronously when the DO has finished. Normally this is
        invoked just before a monitor is destroyed or when an asynchronous
        method has finished.

        Parameters:
        - value is the value we are interested in
        - completion is a CORBA completion structure
        - desc is callback struct description

        Returns:
            Nothing
        Raises:
            Nothing
        '''
        # to make pychecker happy
        desc = None

        self._logger.logDebug('Monitor of ' + self.name +
                             ' DONE, value read is: '
                             + str(value) + '  time: '
                             + str(completion.timeStamp)
                             + ' type: ' + str(completion.type)
                             + ' code: ' + str(completion.code))
        
        if completion.type != 0:
          self._logger.logWarning('Property: '+ self.name + ' completion type: ' 
                                    + ' type: ' + str(completion.type)
                                    + ' code: '
                                    + str(completion.code)
                                    +', data is not stored')   
        else:     
            self.buffer.add(completion.timeStamp, value)
      
        # If in the future we want to take care of completions types and code then:
        # self.buffer.add(completion.timeStamp,  value, completion.type
        # completion.code)

        self.completion = completion

      
        self.buffer.flush()  # Done with the monitor so flush the data
      
        self.buffer = None  #TODO: with the = Non then there is no need to call flush --> Check
        # Set flags.
        self.status = 'DONE'
    #---------------------------------------------------

    def negotiate(self, time_to_transmit, desc):
        '''
        Implementation of negotiate. For simplicity's sake,
        we always return true. In case that we need to implement
        the method, the BACI specs should be investigated

        Parameters: See the BACI specs.

        Returns: TRUE

        Raises: Nothing
        '''
        # to make pychecker happy
        time_to_transmit = None
        desc = None
        return TRUE
    #------------------------------------------------

    def last(self):
        '''
        Return the last value received by the DO.

        Parameters: None.

        Returns: last archived value

        Raises: Nothing
        '''
        return self.buffer[-1]
     #-------------------------------------------------


class ArchCBlong(BaseArchCB, ACS__POA.CBlong):

    '''
    Extension of the BaseArchCB base class for CBlong

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #----------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#--------------------------------------------------


class ArchCBlongSeq(BaseArchCB, ACS__POA.CBlongSeq):

    '''
    Extension of the BaseArchCB base class for CBlongSeq

    Keyword arguments:
    name         -- of this callback instance
    buffer -- is assumed a list-type object with enum-type
                    entries with: Property name (Component_Property)
                    |  value   |   timestamp   |
                    completion (value of the completion? OK or BAD enum)
    logger       -- logger to be use
    '''  # ----------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.

        Parameters: name of this callback instance

        Raises: Nothing
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#--------------------------------------------------------


class ArchCBuLong(BaseArchCB, ACS__POA.CBuLong):

    '''
    Extension of the BaseArchCB base class for CBuLong

    Keyword arguments:
    name         -- of this callback instance
    buffer -- is assumed a list-type object with enum-type
                    entries with: Property name (Component_Property)
                    |  value   |   timestamp   |
                    completion (value of the completion? OK or BAD enum)
    logger       -- logger to be use
    '''  # ----------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#--------------------------------------------------------


class ArchCBuLongSeq(BaseArchCB, ACS__POA.CBuLongSeq):

    '''
    Extension of the BaseArchCB base class for CBuLongSeq

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#-----------------------------------------------------------------------------


class ArchCBlongLong(BaseArchCB, ACS__POA.CBlongLong):

    '''
    Extension of the BaseArchCB base class for CBlongLong

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBuLongLong(BaseArchCB, ACS__POA.CBuLongLong):

    '''
    Extension of the BaseArchCB base class for CBuLongLong

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        Parameters: name of this callback instance
        Raises: Nothing
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBdouble(BaseArchCB, ACS__POA.CBdouble):

    '''
    Extension of the BaseArchCB base class for CBdouble

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBdoubleSeq(BaseArchCB, ACS__POA.CBdoubleSeq):

    '''
    Extension of the BaseArchCB base class for CBdoubleSeq

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBstring(BaseArchCB, ACS__POA.CBstring):

    '''
    Extension of the BaseArchCB base class for CBstring

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBstringSeq(BaseArchCB, ACS__POA.CBstringSeq):

    '''
    Extension of the BaseArchCB base class for CBstringSeq

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBpatternValueRep(BaseArchCB, ACS__POA.CBpattern):

    '''
    Extension of the BaseArchCB base class for CBpattern,
    using the integer representation of it

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.

        Parameters: name of this callback instance

        Raises: Nothing
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBpatternStringRep(BaseArchCB, ACS__POA.CBpattern):

    '''
    Extension of the BaseArchCB base class for CBlongPattern,
    used normally with enumerations, using the string representation of it.
    Currently not used in the property recorder

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None, enumStates=None):
        '''
        Constructor.
        '''
        if(enumStates is not None):
            self._enumStates = enumStates
        else:
            self._enumStates = None

        BaseArchCB.__init__(self, name, buffer,
                            logger)

    def working(self, value, completion, desc):
        '''
        Method invoked by the monitor according to the
        configuration (at a certain rate of value change)
        It sends the requested values and completion of the property
        as read to the backend.
        Overrides the superclass, to allow the string representation
        of enums


        Parameters:
        - value is the value we are interested in
        - completion is a CORBA completion structure
        - desc is callback struct description

        Returns:
            Nothing

        Raises:
            Nothing
        '''

        if self._enumStates is not None:
            self._logger.logDebug('Monitor of ' + self.name
                               + ', WORKING, state read is: '
                               + self._enumStates[value]
                               + '  time: ' + str(completion.timeStamp)
                               + ' type: ' + str(completion.type)
                               + ' code: ' + str(completion.code))
            #self.buffer.add(completion.timeStamp, value)
            # TODO: I think that the backend can do the conversion from enums to sting rep
            # so might be needed to change

            if completion.type != 0:
                self._logger.logWarning('Property: '+ self.name + ' completion type: ' 
                                        + ' type: ' + str(completion.type)
                                        + ' code: '
                                        + str(completion.code)
                                        +', data is not stored')     
             
            else:     
                self.buffer.add(completion.timeStamp, self._enumStates[value])

        else:
            BaseArchCB.working(self, value, completion, desc)


        completion = None
        # to make pychecker happy
        desc = None

        # Set flag.
        self.status = 'WORKING'

    def done(self, value, completion, desc):
        '''
        Invoked asynchronously when the DO has finished. Normally this is
        invoked just before a monitor is destroyed or when an asynchronous
        method has finished.
        Overrides the superclass, to allow the string representation
        of enums


        Parameters:
        - value is the value we are interested in
        - completion is a CORBA completion structure
        - desc is callback struct description

        Returns: Nothing
        Raises: Nothing
        '''
        # to make pychecker happy
        desc = None

        if self._enumStates is not None:
            self._logger.logDebug('Monitor of ' + self.name
                                  + ', DONE, state read is: '
                                  + self._enumStates[value]
                                  + '  time: ' + str(completion.timeStamp)
                                  + ' type: ' + str(completion.type)
                                  + ' code: ' + str(completion.code))
            #self.buffer.add(completion.timeStamp, value)
            # TODO: I think that the backend can do the conversion from enums to sting rep
            # so might be needed to change

            if completion.type != 0:
                self._logger.logWarning('Property: '+ self.name + ' completion type: ' 
                                        + ' type: ' + str(completion.type)
                                        + ' code: '
                                        + str(completion.code)
                                        +', data is not stored')   
             
            else:     
                self.buffer.add(completion.timeStamp, self._enumStates[value])

        else:
            BaseArchCB.working(self, value, completion, desc)

       # Save completion to be able to fetch the error code.
        self.completion = completion

        self.buffer.flush()  # Done with the monitor so flush the data
        
        self.buffer = None # TODO: see above comment
        
        # Set flags.
        self.status = 'DONE'
#------------------------------------------------------------------------------


class ArchCBfloat(BaseArchCB, ACS__POA.CBfloat):

    '''
    Extension of the BaseArchCB base class for CBfloat

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBfloatSeq(BaseArchCB, ACS__POA.CBfloatSeq):

    '''
        Extension of the BaseArchCB base class for CBfloatSeq

        Keyword arguments:
        name         -- of this callback instance
        buffer       -- buffer from the backend registry
        logger       -- logger to be use
        '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBbool(BaseArchCB, ACS__POA.CBboolean):

    '''
    Extension of the BaseArchCB base class for CBbool

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBboolSeq(BaseArchCB, ACS__POA.CBbooleanSeq):

    '''
    Extension of the BaseArchCB base class for CBboolSeq

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.

        Parameters: name of this callback instance

        Raises: Nothing
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class ArchCBonOffSwitch(BaseArchCB, ACS__POA.CBOnOffSwitch):

    '''
    Extension of the BaseArchCB base class for CBonOffSwitch

    Keyword arguments:
    name         -- of this callback instance
    buffer       -- buffer from the backend registry
    logger       -- logger to be use
    '''
    #--------------------------------------------------------------------------

    def __init__(self, name=None, buffer=None,
                 logger=None):
        '''
        Constructor.
        '''
        BaseArchCB.__init__(self, name, buffer, logger)
#------------------------------------------------------------------------------


class CBFactory():

    '''
     Provides the adequate callback object according to the property type
     The type of property is found according to its NP_RepositoryId,
     which is stored in the 'constants module'

     All the methods and members are static, and the callback object
     is obtained via a factory method

    '''
    __cbMap = {}
    __cbMap[constants.RODOUBLE_NP_REP_ID] = ArchCBdouble
    __cbMap[constants.RWDOUBLE_NP_REP_ID] = ArchCBdouble
    __cbMap[constants.RODOUBLESEQ_NP_REP_ID] = ArchCBdoubleSeq
    __cbMap[constants.RWDOUBLESEQ_NP_REP_ID] = ArchCBdoubleSeq
    __cbMap[constants.ROFLOAT_NP_REP_ID] = ArchCBfloat
    __cbMap[constants.RWFLOAT_NP_REP_ID] = ArchCBfloat
    __cbMap[constants.ROFLOATSEQ_NP_REP_ID] = ArchCBfloatSeq
    __cbMap[constants.RWFLOATSEQ_NP_REP_ID] = ArchCBfloatSeq
    __cbMap[constants.ROLONG_NP_REP_ID] = ArchCBlong
    __cbMap[constants.RWLONG_NP_REP_ID] = ArchCBlong
    __cbMap[constants.ROLONGSEQ_NP_REP_ID] = ArchCBlongSeq
    __cbMap[constants.RWLONGSEQ_NP_REP_ID] = ArchCBlongSeq
    __cbMap[constants.ROULONG_NP_REP_ID] = ArchCBuLong
    __cbMap[constants.RWULONG_NP_REP_ID] = ArchCBuLong
    __cbMap[constants.ROULONGSEQ_NP_REP_ID] = ArchCBuLongSeq
    __cbMap[constants.RWULONGSEQ_NP_REP_ID] = ArchCBuLongSeq
    __cbMap[constants.ROLONGLONG_NP_REP_ID] = ArchCBlongLong
    __cbMap[constants.RWLONGLONG_NP_REP_ID] = ArchCBlongLong
    # longLongSeq unsupported in ACS
    __cbMap[constants.ROLONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.RWLONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.ROULONGLONG_NP_REP_ID] = ArchCBuLongLong
    __cbMap[constants.RWULONGLONG_NP_REP_ID] = ArchCBuLongLong
    __cbMap[constants.ROULONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.RWULONGLONGSEQ_NP_REP_ID] = None
    __cbMap[constants.ROBOOLEAN_NP_REP_ID] = ArchCBbool
    __cbMap[constants.RWBOOLEAN_NP_REP_ID] = ArchCBbool
    __cbMap[constants.ROBOOLEANSEQ_NP_REP_ID] = ArchCBboolSeq
    __cbMap[constants.RWBOOLEANSEQ_NP_REP_ID] = ArchCBboolSeq
    __cbMap[constants.ROPATTERN_NP_REP_ID] = ArchCBpatternValueRep
    __cbMap[constants.RWPATTERN_NP_REP_ID] = ArchCBpatternValueRep
    # patternSeq not supported
    __cbMap[constants.ROPATTERNSEQ_NP_REP_ID] = None
    __cbMap[constants.RWPATTERNSEQ_NP_REP_ID] = None
    __cbMap[constants.ROSTRING_NP_REP_ID] = ArchCBstring
    __cbMap[constants.RWSTRING_NP_REP_ID] = ArchCBstring
    __cbMap[constants.ROSTRINGSEQ_NP_REP_ID] = ArchCBstringSeq
    __cbMap[constants.RWSTRINGSEQ_NP_REP_ID] = ArchCBstringSeq

    @staticmethod
    def getCallback(prop, monitorBuffer, logger):
        '''
        Static factory method that returns the callback adequate to
        the property

        Keyword arguments:
        prop         -- ACS property to monitor
        monitorBuffer -- buffer object from the backends types
        logger       -- logger to be used
                     (if None, default console at DEBUG level is used)

        Returns:
        the Callback object for the monitor
        '''
        try:
            if CBFactory.__cbMap[prop._NP_RepositoryId] is None:
                raise Exception
                # throw an unsuported exception
            else:
                return (
                    CBFactory.__cbMap[prop._NP_RepositoryId](
                        prop._get_name(), monitorBuffer, logger)
                )

        # If key error, then it is probably an enum
        except KeyError:
            logger.debug("no NP_RepositoryID, property type candidate: enum")
# Next lines commented, used to use the string representation from here
#             try:
#                 enumStates = CBFactory._getEnumPropDict(prop, logger)
#                 return (
#                     ArchCBpatternStringRep(
#                         prop._get_name(),
#                         monitorBuffer,
#                         logger,
#                         enumStates)
#                 )
#
#             except Exception:
#             logger.debug(
#                     "num states cannot be read, use the int representation")
            return (
                ArchCBpatternValueRep(
                    prop._get_name(),
                    monitorBuffer,
                    logger)
            )
