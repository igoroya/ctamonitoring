__version__ = "$Id$"


"""
The simple fork forwards any backend operation to its childs.

It creaties second level backends so called childs.
It registers a given property at these childs (Registry) and adds
property data to their buffers. Simple fork doesn't do any parallel
processing though. All operations are executed sequentially - so,
a potential "add" at the simple fork will cause an "add" at the first
backend, then at the second etc.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
