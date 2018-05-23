"""
This module includes the implementations of Python ACS callback
classes for use in the PropertyRecorder component. The purpose
of these callbacks is to store the data into the different backends
of the property recorders

BaseArchCB is a base class containing the base functionality
ArchCBXXX deals for the XXX type ACS property.
ArchCBpatternStringRep allows to insert the string representation of a Enum.


@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: Acspy.Common.Log or logging
"""
from Acspy.Common.Log import getLogger
import ACS__POA   # Import the Python CORBA stubs for BACI
from omniORB.CORBA import TRUE  # @UnresolvedImport
from ctamonitoring.property_recorder import constants
from ctamonitoring.property_recorder.frontend_exceptions import (
    UnsupporterPropertyTypeError
    )
from ctamonitoring.property_recorder.backend.exceptions import (
    InterruptedException
    )

__version__ = "$Id$"


class BaseArchCB:
    """
    This class contains the implementation of the
    callback basic operations, with a common for all the used callbacks.

    Method working() and done() are invoked by the
    monitor created by the recorder.

    When monitor is done a flush() order is issued to the buffer

    @ivar status: Status of the Callback,
                following acs required states:
                INIT; WORKING, DONE
    @type status: string
    @ivar backend_buffer: with the data
    @type backend_buffer:
        ctamonitoring.property_recorder.backend.dummy.registry.Buffer
    @ivar property_name: Name of the ACS property
    @type property_name: string
    """

    def __init__(self, property_name, backend_buffer, logger=None):
        """
        Constructor.

        @param property_name: Propoerty name for the callback
        @type property_name: string
        @param backend_buffer: buffer from the backend registry
        @type backend_buffer:
            ctamonitoring.property_recorder.backend.dummy.registry.Buffer

        @raise ValueError: if no name is given to the property
            or no buffer is specified
        """

        # If there is no name then we do not want to store anything
        if property_name is not None:
            self.property_name = property_name
        else:
            raise ValueError("no name was given to the property")

        # collection where the data should be stored. Expected:
        # deque type. If none is provided, the only local storage is performed
        if backend_buffer is None:
            raise ValueError("no archive buffer was provided")
        else:
            self.backend_buffer = backend_buffer

        if logger is None:
            logger = getLogger('ctamonitoring.property_recorder.callbacks')

        self._logger = logger

        # Flag for the application to check if the action is still going on
        # and if the callback has arrived.
        self.status = 'INIT'

    def working(self, value, completion, desc):
        """
        Method invoked by the monitor according to the
        configuration (at a certain rate of value change)
        It sends the requested values and completion of the property
        as read to the backend

        Parameters:
        @param value: value of the monitored item
        @type value: depends on the property type
        @param completion: CORBA completion structure
        @type completion: ACSErr.Completion
        @param desc: callback struct description
        @type desc: ACS.CBDescOut

        """
        is_done = False
        self.save_if_ok(value, completion, desc, is_done)

    def done(self, value, completion, desc):
        """
        Invoked asynchronously when the DO has finished. Normally this is
        invoked just before a monitor is destroyed or when an asynchronous
        method has finished.

        Parameters:
        @param value: value of the monitored item
        @type value: depends on the property type
        @param completion: CORBA completion structure
        @type completion: ACSErr.Completion
        @param desc: callback struct description
        @type desc: ACS.CBDescOut
        """

        is_done = True
        self.save_if_ok(value, completion, desc, is_done)
        try:
            self.backend_buffer.flush()
        except InterruptedException:
            self._logger.logDebug("last monitoring value might be lost")
        self.backend_buffer = None

    def save_if_ok(self, value, completion, desc, is_done):
        # to make pychecker happy
        desc = None  # @UnusedVariable

        working_str = 'DONE' if is_done else 'WORKING'

        self._logger.logDebug(
            'Monitor of ' + self.property_name + ' ' + working_str +
            ', value read is: ' +
            str(value) + '  time: ' +
            str(completion.timeStamp) +
            ' type: ' + str(completion.type) +
            ' code: ' + str(completion.code))

        if is_completion_ok(completion):
            self.backend_buffer.add(completion.timeStamp, value)
        else:
            self._logger.logWarning(
                'Property: ' + self.property_name +
                ' completion type: ' +
                ' type: ' + str(completion.type) +
                ' code: ' +
                str(completion.code) +
                ', data is not stored')

        self.status = working_str

    def negotiate(self, time_to_transmit, desc):
        """
        Implementation of negotiate. For simplicity's sake,
        we always return true. In case that we need to implement
        the method, the BACI specs should be investigated

        Parameters: See the BACI specs.

        Returns: TRUE
        """
        # to make pychecker happy
        time_to_transmit = None  # @UnusedVariable
        desc = None  # @UnusedVariable
        return TRUE

    def last(self):
        """
        Return the last value received by the DO.

        Returns: last archived value
        """
        raise NotImplementedError("History cannot be obtained from buffer")


class ArchCBlong(BaseArchCB, ACS__POA.CBlong):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBlong

    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBlongSeq(BaseArchCB, ACS__POA.CBlongSeq):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBlongSeq
    """
    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBuLong(BaseArchCB, ACS__POA.CBuLong):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBuLong
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBuLongSeq(BaseArchCB, ACS__POA.CBuLongSeq):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBuLongSeq
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBlongLong(BaseArchCB, ACS__POA.CBlongLong):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBlongLong
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBuLongLong(
        BaseArchCB, ACS__POA.CBuLongLong):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBuLongLong
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBdouble(BaseArchCB, ACS__POA.CBdouble):  # @UndefinedVariable
    """
    Extension of the BaseArchCB base class for CBdouble
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBdoubleSeq(
        BaseArchCB, ACS__POA.CBdoubleSeq):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBdoubleSeq
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBstring(BaseArchCB, ACS__POA.CBstring):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBstring
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBstringSeq(
        BaseArchCB, ACS__POA.CBstringSeq):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBstringSeq
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBpatternValueRep(
        BaseArchCB, ACS__POA.CBpattern):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBpattern,
    using the integer representation of it
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.

        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBfloat(
        BaseArchCB,
        ACS__POA.CBfloat):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBfloat
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBfloatSeq(
        BaseArchCB,
        ACS__POA.CBfloatSeq):  # @UndefinedVariable

    """
        Extension of the BaseArchCB base class for CBfloatSeq
        """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBbool(
        BaseArchCB,
        ACS__POA.CBboolean):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBbool
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBboolSeq(
        BaseArchCB,
        ACS__POA.CBbooleanSeq):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBboolSeq
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.

        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class ArchCBonOffSwitch(
        BaseArchCB,
        ACS__POA.CBOnOffSwitch):  # @UndefinedVariable

    """
    Extension of the BaseArchCB base class for CBonOffSwitch
    """

    def __init__(self, name=None, backend_buffer=None,
                 logger=None):
        """
        Constructor.
        """
        BaseArchCB.__init__(self, name, backend_buffer, logger)


class CBFactory():

    """
     Provides the adequate callback object according to the property type
     The type of property is found according to its NP_RepositoryId,
     which is stored in the 'constants module'

     All the methods and members are static, and the callback object
     is obtained via a factory method

    """
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
    __cbMap[constants.ROWRONGBOOL_NP_REP_ID] = None
    __cbMap[constants.RWWRONGBOOL_NP_REP_ID] = None
    __cbMap[constants.ROONOFFSWITCH_NP_REP_ID] = None
    __cbMap[constants.RWONOFFSWITCH_NP_REP_ID] = None

    @staticmethod
    def get_callback(prop, prop_name, monitor_buffer, logger=None):
        """
        Static factory method that returns the callback adequate to
        the property

        @param prop: ACS property to monitor
        @type prop: ACS._objref_<property_type>
        @param monitor_buffer: buffer object from the backends types
        @type: ctamonitoring.property_recorder.backend.dummy.registry.Buffer
        @raise UnsupporterPropertyTypeError: If the property type
                                             is not supported
        @param logger ACS logger
        @type Acspy.Common.Log.Logger
        """
        if logger is None:
            logger = getLogger('ctamonitoring.property_recorder.callbacks')
        try:
            if CBFactory.__cbMap[prop._NP_RepositoryId] is None:
                raise UnsupporterPropertyTypeError(prop._NP_RepositoryId)
            else:
                return (
                    CBFactory.__cbMap[prop._NP_RepositoryId](
                        prop_name, monitor_buffer, logger)
                )
        # If key error, then it is probably an enum
        except KeyError:
            logger.debug(
                "no NP_RepositoryID, "
                "property type candidate: enum")
            return (
                ArchCBpatternValueRep(
                    prop_name,
                    monitor_buffer, logger)
            )


def is_completion_ok(completion):
    """ Checks if completion from the property read is OK

    TODO: In previous version, completion was always 0 (ACS 12),
    now it is always 1 (ACS 2014_6). Is this an issue?
    It can be reproduced by the Objex monitors, so has nothing
    to do with Python. Values seems to be OK.
    I assume here that completion 0 or 1 is OK
    If in the future we want to take care of completions types and code:
    self.buffer.add(completion.timeStamp,  value, completion.type
    completion.code)
    """
    return int(completion.type) < 2
