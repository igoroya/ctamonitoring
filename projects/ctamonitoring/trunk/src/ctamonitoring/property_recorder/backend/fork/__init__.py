__version__ = "$Id$"


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
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
