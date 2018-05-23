"""
Utilities to decode the entries in the CDB doing the require parsing

@author: igoroya
@organization: DESY
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
import ast
from ctamonitoring.property_recorder.constants import DECODE_METHOD

__version__ = "$Id$"


def decode_attribute(value, decode_method):
    """
    Picks the correct decoding method
    Raises an exception when the decoding method is not supported
    @raises ValueError:
    @raises TypeError
    """
    if decode_method is DECODE_METHOD.NONE:
        return _decode_none(value)
    elif decode_method is DECODE_METHOD.AST_LITERAL:
        return _decode_ast_literal(value)
    elif decode_method is DECODE_METHOD.AST_LITERAL_HYBRID:
        return _decode_ast_literal_hybrid(value)
    elif decode_method is DECODE_METHOD.UTF8:
        return _decode_utf8(value)
    else:
        raise ValueError("decode_method is not supported")


def _decode_none(value):
    """
    This is used with strings that do not need any decoding
    """
    return value


def _decode_ast_literal(value):
    """
    This is used with variables that are no strings, that need
    to be decoded
    """
    try:
        return ast.literal_eval(value)
    except SyntaxError:
        return None


def _decode_ast_literal_hybrid(value):
    """
    This is used with variables can be strings or numbers
    """
    try:
        return _decode_ast_literal(value)
    # If exception then it is a string
    except Exception:
        return value


def _decode_utf8(value):
    """
    Returns a Unicode object on success, or None on failure
    """
    try:
        return value.decode('utf-8')
    except UnicodeDecodeError:
        return None


def decode_boolean(value):
    """
    Returns a boolean when a cdb boolean attrib is provided,
    otherwise None
    """
    try:
        decoded = _decode_ast_literal(value.title())
    except Exception:
        raise ValueError("could not decode value")
    if not isinstance(decoded, bool):
        raise TypeError("decoded value is not boolean")
    return decoded
