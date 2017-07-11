__version__ = "$Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $"


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
@version: $Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $
@change: $LastChangedDate: 2013-08-09 01:28:32 +0200 (Fr, 09 Aug 2013) $
@change: $LastChangedBy: tschmidt $
"""
