#!/usr/bin/env python
# encoding: utf-8
'''
monitest.create_property_data -- shortdesc

monitest.create_property_data is a description

It defines classes_and_methods

@author: tschmidt
@organization: DESY Zeuthen
@copyright: 2014, cta-observatory.org. All rights reserved.
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: sys
@requires: os
@requires: optparse
'''

import sys
import os

from optparse import OptionParser


__all__ = []
__version__ = "$Revision$".split()[1]
__date__ = "2014-01-06"
__updated__ = "$LastChangedDate$".split()[1]

DEBUG = 1


def main(argv = None):
    '''Command line options.'''
    
    program_name = os.path.basename(sys.argv[0])
    program_version = "%s" % __version__
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    program_longdesc = '''''' # optional - give further explanation about what the program does
    
    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        parser.add_option("-i", "--in", dest="infile", help="set input path [default: %default]", metavar="FILE")
        parser.add_option("-o", "--out", dest="outfile", help="set output path [default: %default]", metavar="FILE")
        parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")
        
        # set defaults
        parser.set_defaults(outfile="./out.txt", infile="./in.txt")
        
        # process options
        (opts, args) = parser.parse_args(argv)
        
        if opts.verbose > 0:
            print("verbosity level = %d" % opts.verbose)
        if opts.infile:
            print("infile = %s" % opts.infile)
        if opts.outfile:
            print("outfile = %s" % opts.outfile)
            
        # MAIN BODY #
        
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    sys.exit(main())
