__version__ = "$Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $"


"""
The fork forwards any backend operation to its childs.

It creaties second level backends so called childs.
It registers a given property at these childs (Registry) and adds
property data to their buffers. Fork adds data to these buffers
in (a) separated thread(s). The input thread and these workers
are decoupled by a ring buffer - so, data is lost if the input rate
is higher then the output rate.
All other operations are executed sequentially at all childs.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $
@change: $LastChangedDate: 2013-08-09 01:28:32 +0200 (Fr, 09 Aug 2013) $
@change: $LastChangedBy: tschmidt $
"""
