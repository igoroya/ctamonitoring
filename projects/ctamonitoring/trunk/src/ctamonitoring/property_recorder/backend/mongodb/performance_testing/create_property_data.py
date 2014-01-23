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
@requires: os
@requires: pymongo
@requires: sys
@requires: copy
@requires: datetime
@requires: optparse
@requires: Queue
@requires: random
@requires: threading
@requires: time
'''

import os
import pymongo
import Queue
import sys

from copy import copy
from datetime import datetime, timedelta
from optparse import Option, OptionParser, OptionValueError
from pymongo import MongoClient
from random import seed as randseed
from random import uniform
from threading import Thread
from time import sleep


__all__ = []
__version__ = "$Revision$".split()[1]
__date__ = "2014-01-06"
__updated__ = "$LastChangedDate$".split()[1]

SEED = None
DEBUG = 0


def check_datetime(option, opt, value):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except:
        raise OptionValueError("option %s: invalid date type: %r (2013-01-01)"
                               % (opt, value))


class DatetimeOption(Option):
    TYPES = Option.TYPES + ("datetime",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["datetime"] = check_datetime


class Property(object):
    def __init__(self, pid, period, min, max, nxt_bin = None, lst_end = None):
        self.pid = pid
        self.period = period
        self.min = min
        self.max = max
        self.nxt_bin = nxt_bin
        self.lst_end = lst_end


class Statistics(object):
    def __init__(self,
                 bin = None, nxt_bin = None, begin = None, end = None,
                 systems = [], n_params = 0,
                 n_bins = 0, n_chunks = 0, n_data_points = 0):
        self.bin = bin
        self.nxt_bin = nxt_bin
        self.begin = begin
        self.end = end
        self.systems = systems
        self.n_params = n_params
        self.n_bins = n_bins
        self.n_chunks = n_chunks
        self.n_data_points = n_data_points


class DBInserter(Thread):
    def __init__(self,
                 stats_col, chunks_col,
                 stats, queue):
        super(DBInserter, self).__init__()
        self._stats_col = stats_col
        self._chunks_col = chunks_col
        self._stats = stats
        self._stats.n_bins = 0
        self._stats.n_chunks = 0
        self._stats.n_data_points = 0
        self._queue = queue
        self._chunks = []
        self._n_bins = -1
        self._n_data_points = 0
        self._force = False
        self.daemon = True
        self.start()
    
    def _send_stats(self):
        td = self._stats.end - self._stats.begin
        td = ((td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) /
              (10**6 * 1.))
        stats = {
                 "bin" : self._stats.bin,
                 "begin" : self._stats.begin,
                 "end" : self._stats.end,
                 "delta_t" : td,
                 "systems" : self._stats.systems,
                 "n_params" : self._stats.n_params,
                 "n_bins" : self._stats.n_bins,
                 "n_chunks" : self._stats.n_chunks,
                 "n_data_points" : self._stats.n_data_points,
                 "realtime" : False
              }
        #print stats
        self._stats_col.insert(stats)
        self._stats.n_bins = 0
        self._stats.n_chunks = 0
        self._stats.n_data_points = 0
    
    def _send_chunks(self):
        self._chunks_col.insert(self._chunks)
        for i in range(len(self._chunks)):
            self._queue.task_done()
        self._stats.n_bins += self._n_bins
        self._n_bins = 0
        self._stats.n_chunks += len(self._chunks)
        self._chunks = []
        self._stats.n_data_points += self._n_data_points
        self._n_data_points = 0
        self._force = False
    
    def run(self):
        lst_bin = None
        while True:
            try:
                bin, chunk, n_dp = self._queue.get(block = not self._chunks)
                if lst_bin != bin:
                    self._n_bins += 1
                    if bin == bin.replace(minute = 0, second = 0, microsecond = 0):
                        self._stats.bin = self._stats.nxt_bin
                        self._stats.nxt_bin = bin
                        self._stats.begin = self._stats.end
                        self._stats.end = datetime.utcnow()
                        if self._stats.bin is not None:
                            if self._chunks:
                                self._send_chunks()
                            self._send_stats()
                    lst_bin = bin
                self._chunks.append(chunk)
                self._n_data_points += n_dp
            except Queue.Empty:
                self._force = True
            if self._force or len(self._chunks) >= 100:
                self._send_chunks()


def acquire_systems(sys_col, sys_locks, systems, props_col, n_params):
    lock_tm = datetime.now()
    if(systems):
        for system in systems:
            print "locking %s" % (system,)
            s = sys_col.find_and_modify({"system name" : system,
                                         "$or" : [{"lock" : {"$exists" : False}},
                                                  {"lock" : None}]},
                                        {"$set" : {"lock" : lock_tm}})
            if not s:
                raise RuntimeError("%s is not available" % (system,))
            sys_locks.append({"name" : system, "tm" : lock_tm})
    elif n_params:
        n_total = 0
        while n_total < n_params:
            print "locking system..."
            s = sys_col.find_and_modify({"$or" : [{"lock" : {"$exists" : False}},
                                                  {"lock" : None}]},
                                        {"$set" : {"lock" : lock_tm}})
            if not s and not sys_locks:
                raise RuntimeError("no system available")
            if not s:
                break
            if s.has_key("system name") and s["system name"] is not None:
                sys_locks.append({"name" : s["system name"],
                                  "tm" : lock_tm})
                n = props_col.find({"system name" : s["system name"]}).count()
                print "%s adds %d properties" % (s["system name"], n)
            else:
                sys_locks.append({"name" : None, "tm" : lock_tm})
                n = props_col.find({"$or" : [{"system name" : {"$exists" : False}},
                                             {"system name" : None}]}).count()
                print "independent components add %d properties" % (n,)
            n_total += n


def acquire_properties(sys_locks, props_col, begin, chunks_col, bin_size):
    properties = []
    first_bin = None
    for system in sys_locks:
        if system["name"] is not None:
            query = {"system name" : system["name"]}
        else:
            query = {"$or" : [{"system name" : {"$exists" : False}},
                              {"system name" : None}]}
        for property in props_col.find(query):
            pid = property["_id"]
            period = property["meta"]["period"]
            graph_min = property["meta"]["graph_min"]
            graph_max = property["meta"]["graph_max"]
            lst_end = (begin -
                       timedelta(seconds = uniform(0, period)))
            chunks = chunks_col.find({"pid" : pid}) \
                               .sort("begin", pymongo.DESCENDING) \
                               .limit(1)
            if chunks.count():
                chunk = chunks.next()
                nxt_bin = chunk["bin"] + bin_size
                if nxt_bin >= begin:
                    p = Property(pid,
                                 timedelta(seconds = period),
                                 graph_min,
                                 graph_max,
                                 nxt_bin,
                                 chunk["end"])
                    if first_bin is None or nxt_bin < first_bin:
                        first_bin = nxt_bin
                else:
                    p = Property(pid,
                                 timedelta(seconds = period),
                                 graph_min,
                                 graph_max,
                                 begin,
                                 lst_end)
                    first_bin = begin
            else:
                p = Property(pid,
                             timedelta(seconds = period),
                             graph_min,
                             graph_max,
                             begin,
                             lst_end)
                first_bin = begin
            properties.append(p)
    return properties, first_bin


def release_systems(sys_col, sys_locks):
    sys_not_locked = []
    for sys_lock in sys_locks:
        if sys_lock["name"] is not None:
            print "releasing %s" % (sys_lock["name"],)
            s = sys_col.find_and_modify({"system name" : sys_lock["name"],
                                         "$and" : [{"lock" : {"$exists" : True}},
                                                   {"lock" : sys_lock["tm"]}]},
                                        {"$set" : {"lock" : None}})
        else:
            print "releasing independent components"
            s = sys_col.find_and_modify({"$or" : [{"system name" : {"$exists" : False}},
                                                  {"system name" : None}],
                                         "$and" : [{"lock" : {"$exists" : True}},
                                                   {"lock" : sys_lock["tm"]}]},
                                        {"$set" : {"lock" : None}})
        if not s: sys_not_locked.append(sys_lock["name"])
    if sys_not_locked:
        if len(sys_not_locked) > 1:
            raise RuntimeError("oups, %s weren't locked anymore"
                               % ((", ").join(str(sys_not_locked)),))
        else:
            raise RuntimeError("oups, %s wasn't locked anymore"
                               % (str(sys_not_locked[0]),))

def main(argv = None):
    randseed(SEED)
    
    program_name = os.path.basename(sys.argv[0])
    program_version = "%s" % __version__
    program_build_date = "%s" % __updated__
    program_version_string = "%%prog %s (%s)" % (program_version,
                                                 program_build_date)
    program_longdesc = '''''' # optional - give further explanation about what the program does
    program_desc = '''''' # optional - give further explanation about what the program does
    
    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version = program_version_string,
                              epilog = program_longdesc,
                              description = program_desc,
                              option_class = DatetimeOption)
        parser.add_option("--host", dest = "host",
                          help = "hostname or IP address of the MongoDB server "
                          "[default: %default]")
        parser.add_option("-p", "--port", dest = "port", type = "int",
                          help = "port number on which to connect "
                          "[default: %default]")
        parser.add_option("-s", "--system", dest = "systems", action = "append",
                          help="system(s) to create data for [default: none]",
                          metavar = "NAME")
        parser.add_option("-n", "--nparams", dest = "n_params", type = "int",
                          help="approx. integral number of parameters to "
                          "create data for [default: %default] if, "
                          "no system is specified")
        parser.add_option("-b", "--begin", dest = "begin", type ="datetime",
                          help = "start date to create data from "
                          "[default: %default]",
                          metavar = "DATE")
        parser.add_option("-d", "--days", dest = "days", type = "int",
                          help = "days that are added to 'begin' "
                          "to determine the stop date [default: %default]")
        parser.add_option("--binsize", dest = "bin_size", type = "int",
                          help = "bin size in seconds [default: %default]",
                          metavar = "SECONDS")
        
        # set defaults
        parser.set_defaults(host = "zoja", port = 27017,
                            n_params = 15000,
                            begin = "2013-10-01", days = 1,
                            bin_size = 60)
        
        # process options
        (opts, args) = parser.parse_args(argv)
        end = opts.begin + timedelta(days = opts.days)
        bin_size = timedelta(seconds = opts.bin_size)
        
        print "-" * 40
        print "host = %s" % (opts.host,)
        print "port = %d" % (opts.port,)
        if opts.systems:
            print "systems = %s" % (", ".join(opts.systems),)
        else:
            print "nparams = %d" % (opts.n_params,)
        print "begin = %s" % (str(opts.begin),)
        print "end = %s" % (str(end),)
        print "binsize = %s" % (str(bin_size),)
        
        # connect to db server, db and collections
        client = MongoClient(opts.host, opts.port)
        db = client.monitest
        chunks_collection = db.chunks
        properties_collection = db.properties
        statistics_collection = db.statistics
        systems_collection = db.systems
        
        system_locks = []
        try:
            # prepare data creation
            print "-" * 40
            acquire_systems(systems_collection, system_locks,
                            opts.systems, properties_collection, opts.n_params)
            properties, first_bin = acquire_properties(system_locks,
                                                       properties_collection,
                                                       opts.begin,
                                                       chunks_collection,
                                                       bin_size)
            if properties:
                print "-" * 40
                print "nparams = %d" % (len(properties),)
                print "firstbin = %s" % (str(first_bin),)
                bin = first_bin
                #end = opts.begin + timedelta(hours = 3)
                statistics = Statistics()
                statistics.systems = [s["name"] for s in system_locks]
                statistics.n_params = len(properties)
                queue = Queue.Queue(3 * len(properties))
                db_inserter = DBInserter(statistics_collection,
                                         chunks_collection,
                                         statistics, queue)
                while bin < end:
                    #print str(bin)
                    for property in properties:
                        if property.nxt_bin > bin:
                            print "oups"
                            continue
                        property.nxt_bin = bin + bin_size
                        values = []
                        t = property.lst_end
                        while True:
                            t += property.period
                            if t >= property.nxt_bin:
                                break
                            val = uniform(property.min, property.max)
                            values.append({"t" : t, "val" : val})
                        if not values:
                            print "oups"
                            continue
                        property.lst_end = values[-1]["t"]
                        chunk = {
                                 "begin" : values[0]["t"],
                                 "end" : property.lst_end,
                                 "values" : values,
                                 "bin" : bin,
                                 "pid" : property.pid
                                }
                        while True:
                            try:
                                queue.put((bin, chunk, len(values)),
                                          block = True)
                                break
                            except Queue.Full:
                                if not db_inserter.is_alive():
                                    raise
                    bin += bin_size
        finally:
            print "-" * 40
            release_systems(systems_collection, system_locks)
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    sys.exit(main())
