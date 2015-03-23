"""
Contains the constants used by the property recorder
In particular, those values required in the NP REPOSITORY

@author: igoroya
@organization: HU Berlin
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$, $LastChangedBy$

"""

from enum import Enum
from collections import namedtuple


RECORDER_NP_REP_ID = "IDL:cta/actl/PropertyRecorder:1.0"
RODOUBLE_NP_REP_ID = "IDL:alma/ACS/ROdouble:1.0"
RWDOUBLE_NP_REP_ID = "IDL:alma/ACS/RWdouble:1.0"
RODOUBLESEQ_NP_REP_ID = "IDL:alma/ACS/ROdoubleSeq:1.0"
RWDOUBLESEQ_NP_REP_ID = "IDL:alma/ACS/RWdoubleSeq:1.0"
ROFLOAT_NP_REP_ID = "IDL:alma/ACS/ROfloat:1.0"
RWFLOAT_NP_REP_ID = "IDL:alma/ACS/RWfloat:1.0"
ROFLOATSEQ_NP_REP_ID = "IDL:alma/ACS/ROfloatSeq:1.0"
RWFLOATSEQ_NP_REP_ID = "IDL:alma/ACS/RWfloatSeq:1.0"
ROLONG_NP_REP_ID = "IDL:alma/ACS/ROlong:1.0"
RWLONG_NP_REP_ID = "IDL:alma/ACS/RWlong:1.0"
ROLONGSEQ_NP_REP_ID = "IDL:alma/ACS/ROlongSeq:1.0"
RWLONGSEQ_NP_REP_ID = "IDL:alma/ACS/RWlongSeq:1.0"
ROULONG_NP_REP_ID = "IDL:alma/ACS/ROuLong:1.0"
RWULONG_NP_REP_ID = "IDL:alma/ACS/RWuLong:1.0"
ROULONGSEQ_NP_REP_ID = "IDL:alma/ACS/ROuLongSeq:1.0"
RWULONGSEQ_NP_REP_ID = "IDL:alma/ACS/RWuLongSeq:1.0"
# NOTE: longLongSeq seems to be unsupported in ACS
ROLONGLONG_NP_REP_ID = "IDL:alma/ACS/ROlongLong:1.0"
RWLONGLONG_NP_REP_ID = "IDL:alma/ACS/RWlongLong:1.0"
ROLONGLONGSEQ_NP_REP_ID = "IDL:alma/ACS/ROlongLongSeq:1.0"
RWLONGLONGSEQ_NP_REP_ID = "IDL:alma/ACS/RWlongLongSeq:1.0"
ROULONGLONG_NP_REP_ID = "IDL:alma/ACS/ROuLongLong:1.0"
RWULONGLONG_NP_REP_ID = "IDL:alma/ACS/RWuLongLong:1.0"
ROULONGLONGSEQ_NP_REP_ID = "IDL:alma/ACS/ROuLogLongSeq:1.0"
RWULONGLONGSEQ_NP_REP_ID = "IDL:alma/ACS/RWuLongLongSeq:1.0"
ROBOOLEAN_NP_REP_ID = "IDL:alma/ACS/ROboolean:1.0"
RWBOOLEAN_NP_REP_ID = "IDL:alma/ACS/RWboolean:1.0"
ROBOOLEANSEQ_NP_REP_ID = "IDL:alma/ACS/RObooleanSeq:1.0"
RWBOOLEANSEQ_NP_REP_ID = "IDL:alma/ACS/RWbooleanSeq:1.0"
# patternSeq not supported
ROPATTERN_NP_REP_ID = "IDL:alma/ACS/ROpattern:1.0"
RWPATTERN_NP_REP_ID = "IDL:alma/ACS/RWpattern:1.0"
ROPATTERNSEQ_NP_REP_ID = "IDL:alma/ACS/ROpatternSeq:1.0"
RWPATTERNSEQ_NP_REP_ID = "IDL:alma/ACS/RWpatternSeq:1.0"
ROSTRING_NP_REP_ID = "IDL:alma/ACS/ROstring:1.0"
RWSTRING_NP_REP_ID = "IDL:alma/ACS/RWstring:1.0"
ROSTRINGSEQ_NP_REP_ID = "IDL:alma/ACS/ROstringSeq:1.0"
RWSTRINGSEQ_NP_REP_ID = "IDL:alma/ACS/RWstringSeq:1.0"




DecodeMethod = Enum('NONE', 'AST_LITERAL', 'AST_LITERAL_HYBRID', 'UTF8')

AttributeInfo = namedtuple('name', 'name, decoding, isPositive, yes_synonyms')
      


PROPERTY_ATTRIBUTES = [AttributeInfo('archive_priority', DecodeMethod.AST_LITERAL, False),
                            AttributeInfo('archive_min_int', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('archive_max_int', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('archive_suppress', DecodeMethod.AST_LITERAL, False),
                            AttributeInfo('archive_mechanism', DecodeMethod.NONE, False),
                            AttributeInfo('archive_delta', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('archive_delta_percent', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('default_timer_trig', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('default_value', DecodeMethod.AST_LITERAL_HYBRID, False),
                            AttributeInfo('description', DecodeMethod.NONE, False),
                            AttributeInfo('format', DecodeMethod.NONE, False),
                            AttributeInfo('graph_max', DecodeMethod.AST_LITERAL, False),
                            AttributeInfo('graph_min', DecodeMethod.AST_LITERAL, False),
                            AttributeInfo('min_delta_trig', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('min_step', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('min_timer_trig', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('resolution', DecodeMethod.AST_LITERAL, True),
                            AttributeInfo('units', DecodeMethod.UTF8, False),
                            AttributeInfo('type', DecodeMethod.NONE, False),
                            AttributeInfo('condition', DecodeMethod.NONE, False),
                            AttributeInfo('bitDescription', DecodeMethod.NONE, False),
                            AttributeInfo('statesDescription', DecodeMethod.NONE, False),
                            AttributeInfo('whenCleared', DecodeMethod.NONE, False),
                            AttributeInfo('whenSet', DecodeMethod.NONE, False),
                            AttributeInfo('archive_suppress', DecodeMethod.NONE, False, ["yes", "true"]),                
                            ]
