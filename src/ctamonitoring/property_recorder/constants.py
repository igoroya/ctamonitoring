'''
Contains the constants used by the property recorder
In particular, those values required to identify the
property type from the NP_RepositoryId and the list
of the possible attributes of a propery

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate: 2015-04-14 19:13:23 +0200 (Tue, 14 Apr 2015)
@change: $LastChangedBy$

'''
from enum import Enum
from collections import namedtuple

__version__ = "$Id$"

RECORDER_NP_REP_ID = 'IDL:cta/actl/PropertyRecorder:1.0'
RODOUBLE_NP_REP_ID = 'IDL:alma/ACS/ROdouble:1.0'
RWDOUBLE_NP_REP_ID = 'IDL:alma/ACS/RWdouble:1.0'
RODOUBLESEQ_NP_REP_ID = 'IDL:alma/ACS/ROdoubleSeq:1.0'
RWDOUBLESEQ_NP_REP_ID = 'IDL:alma/ACS/RWdoubleSeq:1.0'
ROFLOAT_NP_REP_ID = 'IDL:alma/ACS/ROfloat:1.0'
RWFLOAT_NP_REP_ID = 'IDL:alma/ACS/RWfloat:1.0'
ROFLOATSEQ_NP_REP_ID = 'IDL:alma/ACS/ROfloatSeq:1.0'
RWFLOATSEQ_NP_REP_ID = 'IDL:alma/ACS/RWfloatSeq:1.0'
ROLONG_NP_REP_ID = 'IDL:alma/ACS/ROlong:1.0'
RWLONG_NP_REP_ID = 'IDL:alma/ACS/RWlong:1.0'
ROLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/ROlongSeq:1.0'
RWLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/RWlongSeq:1.0'
ROULONG_NP_REP_ID = 'IDL:alma/ACS/ROuLong:1.0'
RWULONG_NP_REP_ID = 'IDL:alma/ACS/RWuLong:1.0'
ROULONGSEQ_NP_REP_ID = 'IDL:alma/ACS/ROuLongSeq:1.0'
RWULONGSEQ_NP_REP_ID = 'IDL:alma/ACS/RWuLongSeq:1.0'
# NOTE: longLongSeq seems to be unsupported in ACS
ROLONGLONG_NP_REP_ID = 'IDL:alma/ACS/ROlongLong:1.0'
RWLONGLONG_NP_REP_ID = 'IDL:alma/ACS/RWlongLong:1.0'
ROLONGLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/ROlongLongSeq:1.0'
RWLONGLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/RWlongLongSeq:1.0'
ROULONGLONG_NP_REP_ID = 'IDL:alma/ACS/ROuLongLong:1.0'
RWULONGLONG_NP_REP_ID = 'IDL:alma/ACS/RWuLongLong:1.0'
ROULONGLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/ROuLogLongSeq:1.0'
RWULONGLONGSEQ_NP_REP_ID = 'IDL:alma/ACS/RWuLongLongSeq:1.0'
ROBOOLEAN_NP_REP_ID = 'IDL:alma/ACS/ROboolean:1.0'
RWBOOLEAN_NP_REP_ID = 'IDL:alma/ACS/RWboolean:1.0'
ROBOOLEANSEQ_NP_REP_ID = 'IDL:alma/ACS/RObooleanSeq:1.0'
RWBOOLEANSEQ_NP_REP_ID = 'IDL:alma/ACS/RWbooleanSeq:1.0'
# patternSeq not supported
ROPATTERN_NP_REP_ID = 'IDL:alma/ACS/ROpattern:1.0'
RWPATTERN_NP_REP_ID = 'IDL:alma/ACS/RWpattern:1.0'
ROPATTERNSEQ_NP_REP_ID = 'IDL:alma/ACS/ROpatternSeq:1.0'
RWPATTERNSEQ_NP_REP_ID = 'IDL:alma/ACS/RWpatternSeq:1.0'
ROSTRING_NP_REP_ID = 'IDL:alma/ACS/ROstring:1.0'
RWSTRING_NP_REP_ID = 'IDL:alma/ACS/RWstring:1.0'
ROSTRINGSEQ_NP_REP_ID = 'IDL:alma/ACS/ROstringSeq:1.0'
RWSTRINGSEQ_NP_REP_ID = 'IDL:alma/ACS/RWstringSeq:1.0'
# The next two bools exist but are actually wrong types that cannot be used
ROWRONGBOOL_NP_REP_ID = 'IDL:alma/ACS/ROBool:1.0'
RWWRONGBOOL_NP_REP_ID = 'IDL:alma/ACS/RWBool:1.0'
ROONOFFSWITCH_NP_REP_ID = 'IDL:alma/ACS/ROOnOffSwitch:1.0'
RWONOFFSWITCH_NP_REP_ID = 'IDL:alma/ACS/RWOnOffSwitch:1.0'


DecodeMethod = Enum('NONE', 'AST_LITERAL', 'AST_LITERAL_HYBRID', 'UTF8')

AttributeInfo = namedtuple('name', 'name, decoding, isPositive, yes_synonyms')


PROPERTY_ATTRIBUTES = [AttributeInfo(
                            'archive_priority', DecodeMethod.AST_LITERAL,
                            False, None),
                       AttributeInfo(
                            'name', DecodeMethod.NONE,
                            False, None),
                       AttributeInfo(
                            'archive_min_int', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'archive_max_int', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'archive_mechanism', DecodeMethod.NONE,
                            False, None),
                       AttributeInfo(
                            'archive_delta', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'archive_delta_percent', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'default_timer_trig', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'default_value', DecodeMethod.AST_LITERAL_HYBRID,
                            False, None),
                       AttributeInfo(
                            'description', DecodeMethod.NONE, False, None),
                       AttributeInfo('format', DecodeMethod.NONE, False, None),
                       AttributeInfo(
                            'graph_max', DecodeMethod.AST_LITERAL,
                            False, None),
                       AttributeInfo(
                            'graph_min', DecodeMethod.AST_LITERAL,
                            False, None),
                       AttributeInfo(
                            'min_delta_trig', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'min_step', DecodeMethod.AST_LITERAL, True, None),
                       AttributeInfo(
                            'min_timer_trig', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo(
                            'resolution', DecodeMethod.AST_LITERAL,
                            True, None),
                       AttributeInfo('units', DecodeMethod.UTF8, False, None),
                       AttributeInfo(
                            'condition', DecodeMethod.NONE, False, None),
                       AttributeInfo(
                            'bitDescription', DecodeMethod.NONE, False, None),
                       AttributeInfo(
                            'statesDescription', DecodeMethod.NONE,
                            False, None),
                       AttributeInfo(
                            'whenCleared', DecodeMethod.NONE, False, None),
                       AttributeInfo(
                            'whenSet', DecodeMethod.NONE, False, None),
                       AttributeInfo(
                            'archive_suppress', DecodeMethod.NONE, False,
                            ['yes', 'true']),
                       ]
'''
These are the attributes that a property can potentially have associated with
it, together with the way we are decoding it for the property recorder
'''