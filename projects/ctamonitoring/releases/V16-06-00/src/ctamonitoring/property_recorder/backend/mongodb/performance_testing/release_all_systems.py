#!/usr/bin/env python
# encoding: utf-8
'''
monitest.release_all_systems -- shortdesc

monitest.release_all_systems is a description

It defines classes_and_methods

@author: tschmidt
@organization: DESY Zeuthen
@copyright: 2014, cta-observatory.org. All rights reserved.
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: math
@requires: os
@requires: pymongo
@requires: sys
@requires: threading
@requires: time
@requires: copy
@requires: datetime
@requires: optparse
@requires: Queue
@requires: random
'''

import os
import sys

from optparse import OptionParser
from pymongo import MongoClient
from random import seed as randseed
from random import random


__all__ = []
__version__ = \
    "$Revision$".split()[1]
__date__ = "2015-05-22"
__updated__ = \
    "$LastChangedDate$" \
    .split()[1]


HOST = "localhost"
SEED = None
DEBUG = 0


def main(argv=None):
    randseed(SEED)

    program_name = os.path.basename(sys.argv[0])
    program_version = "%s" % __version__
    program_build_date = "%s" % __updated__
    program_version_string = "%%prog %s (%s)" % (program_version,
                                                 program_build_date)
    # optional - give further explanation about what the program does
    program_longdesc = ''''''
    # optional - give further explanation about what the program does
    program_desc = ''''''
    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string,
                              epilog=program_longdesc,
                              description=program_desc)
        parser.add_option("--host", dest="host",
                          help="hostname or IP address of the MongoDB server "
                          "[default: %default]")
        parser.add_option("-p", "--port", dest="port", type="int",
                          help="port number on which to connect "
                          "[default: %default]")

        # set defaults
        parser.set_defaults(host=HOST, port=27017)

        # process options
        (opts, args) = parser.parse_args(argv)

        print "-" * 40
        print "host = %s" % (opts.host,)
        print "port = %d" % (opts.port,)

        # connect to db server, db and collections
        client = MongoClient(opts.host, opts.port)
        db = client.ctamonitoringtest
        systems_collection = db.systems
        systems_collection.update_many(
            {
                "$and": [
                    {"lock": {"$exists": True}},
                    {"lock": {"$ne": None}}
                ]
            },
            {
                "$set": {"lock": None, "random": random()}
            }
        )
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    sys.exit(main())
