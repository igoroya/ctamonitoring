__version__ = "$Id$"


"""
The typed fork forwards any backend operation to its childs.

It creates second level backends so called childs - there will be
a default child that will receive all 'untyped' data and possibly
additional childs that may receive corresponding 'typed' data.
An example: You want to record all float data in Akumuli, but data
of different type in MongoDB. Your choice for the default child is
the MongoDB backend and the choice for the 'float backend' is the
Akumuli backend.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
"""
