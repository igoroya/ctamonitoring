__version__ = "$Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $"


'''
This package is the home of most backends for the property recorder.

However, its certainly possible to use externally defined backends,
if these provide all needed functionality
(cf. module ctamonitoring.property_recorder.backend.dummy.registry).

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id: __init__.py 532 2013-08-08 23:28:32Z tschmidt $
@change: $LastChangedDate: 2013-08-09 01:28:32 +0200 (Fri, 09 Aug 2013) $
@change: $LastChangedBy: tschmidt $
'''


import types


def get_registry_class(class_or_backend_name):
    '''
    Return the backend registry class that matches the given
    fully qualified class name or corresponds to the given backend name.
    
    @param class_or_backend_name: Fully qualified class name or backend name.
    @type class_or_backend_name: string
    @return: Backend registry class.
    @rtype: ClassType or TypeType
    @raise TypeError: If class_or_backend_name doesn't address a class.
    '''
    mod_and_cls = class_or_backend_name.rsplit('.', 1)
    # assume backend name in case length of mod_and_cls is one
    # create fully qualified using backend name...
    if len(mod_and_cls) == 1:
        mod_and_cls = ['.'.join([__name__, class_or_backend_name, 'registry']),
                       "Registry"]
    # get backend registry class
    cls = getattr(__import__(mod_and_cls[0], globals(), locals(), mod_and_cls[-1]),
                      mod_and_cls[-1])
    if not isinstance(cls, (types.ClassType, types.TypeType)):
        TypeError("%s is not a class." % '.'.join(mod_and_cls))
    return cls
