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

import math
import os
import pymongo
import Queue
import sys
import threading
import time

from copy import copy
from datetime import datetime, timedelta
from optparse import Option, OptionParser, OptionValueError
from pymongo import MongoClient
from random import seed as randseed
from random import uniform
from random import random


__all__ = []
__version__ = \
    "$Revision$".split()[1]
__date__ = "2014-01-06"
__updated__ = \
    "$LastChangedDate$" \
    .split()[1]


HOST = "localhost"
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
    def __init__(self, pid, period, min, max, nxt_bin=None, lst_end=None):
        self.pid = pid
        self.period = period
        self.min = min
        self.max = max
        self.nxt_bin = nxt_bin
        self.lst_end = lst_end


class Statistics(object):
    def __init__(self,
                 bin=None, nxt_bin=None, begin=None, end=None,
                 systems=[], n_props=0,
                 n_bins=0, n_chunks=0, n_data_points=0,
                 realtime=False):
        self.bin = bin
        self.nxt_bin = nxt_bin
        self.begin = begin
        self.end = end
        self.systems = systems
        self.n_props = n_props
        self.n_bins = n_bins
        self.n_chunks = n_chunks
        self.n_data_points = n_data_points
        self.realtime = realtime


def get_total_seconds(td):
    return ((td.microseconds + (td.seconds + td.days * 24L * 3600L) * 10**6L) /
            (10**6L * 1.))


def get_floor(tm, td):
    tmp = tm - datetime.min
    tmp = timedelta(seconds=((get_total_seconds(tmp) //
                              get_total_seconds(td)) *
                             get_total_seconds(td)))
    return datetime.min + tmp


class DBScheduler(threading.Thread):
    def __init__(self,
                 queue_out, queue_in, chunk_size):
        super(DBScheduler, self).__init__()
        self._queue_out = queue_out
        self._queue_in = queue_in
        self._chunk_size = chunk_size
        self._do_flush = threading.Event()
        self._do_flush.clear()
        self.daemon = True
        self.start()

    def flush(self):
        self._do_flush.set()

    def _flush(self, n):
        if n:
            self._queue_out.join()
            for i in range(n):
                self._queue_in.task_done()

    def run(self):
        lst_bin = None
        n_chunks = 0
        nxt_tm = None
        while True:
            while True:
                try:
                    bin, chunk, n_dp = self._queue_in.get(block=True,
                                                          timeout=10)
                    break
                except Queue.Empty:
                    if self._do_flush.is_set():
                        self._flush(n_chunks)
                        n_chunks = 0
                        self._do_flush.clear()
            if lst_bin != bin:
                if nxt_tm is None:
                    now = datetime.now()
                    nxt_tm = get_floor(now, self._chunk_size)
                    if now > nxt_tm:
                        nxt_tm += self._chunk_size
                else:
                    self._flush(n_chunks)
                    n_chunks = 0
                    now = datetime.now()
                if now < nxt_tm:
                    time.sleep(get_total_seconds(nxt_tm - now))
                nxt_tm += self._chunk_size
                lst_bin = bin
            self._queue_out.put((bin, chunk, n_dp), block=True)
            n_chunks += 1


class DBInserter(threading.Thread):
    def __init__(self,
                 stats_col, chunks_col,
                 stats, queue_in):
        super(DBInserter, self).__init__()
        self._stats_col = stats_col
        self._chunks_col = chunks_col
        self._stats = stats
        self._stats.n_bins = 0
        self._stats.n_chunks = 0
        self._stats.n_data_points = 0
        self._queue_in = queue_in
        self._chunks = []
        self._n_bins = -1
        self._n_data_points = 0
        self._force = False
        self.daemon = True
        self.start()

    def _send_stats(self):
        stats = {
            "bin": self._stats.bin,
            "begin": self._stats.begin,
            "end": self._stats.end,
            "delta_t": get_total_seconds(self._stats.end - self._stats.begin),
            "systems": self._stats.systems,
            "n_props": self._stats.n_props,
            "n_bins": self._stats.n_bins,
            "n_chunks": self._stats.n_chunks,
            "n_data_points": self._stats.n_data_points,
            "realtime": self._stats.realtime, }
        self._stats_col.insert(stats)
        self._stats.n_bins = 0
        self._stats.n_chunks = 0
        self._stats.n_data_points = 0

    def _send_chunks(self):
        self._chunks_col.insert(self._chunks)
        for i in range(len(self._chunks)):
            self._queue_in.task_done()
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
                bin, chunk, n_dp = self._queue_in.get(block=not self._chunks)
                if lst_bin != bin:
                    self._n_bins += 1
                    if bin == bin.replace(minute=0, second=0, microsecond=0):
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


def acquire_systems(sys_col, sys_locks, systems, props_col, n_props):
    lock_tm = datetime.now()
    if(systems):
        for system in systems:
            print "locking %s" % (system,)
            s = sys_col.find_and_modify(
                {
                    "system_name": system,
                    "$or": [
                        {"lock": {"$exists": False}},
                        {"lock": None}
                    ]
                },
                {
                    "$set": {"lock": lock_tm}
                },
                sort=[("random", pymongo.ASCENDING)]
            )
            if not s:
                raise RuntimeError("%s is not available" % (system,))
            sys_locks.append({"name": system, "tm": lock_tm})
    elif n_props:
        n_total = 0
        while n_total < n_props:
            print "locking system..."
            s = sys_col.find_and_modify(
                {
                    "$or": [
                        {"lock": {"$exists": False}},
                        {"lock": None}
                    ]
                },
                {
                    "$set": {"lock": lock_tm}
                },
                sort=[("random", pymongo.ASCENDING)])
            if not s and not sys_locks:
                raise RuntimeError("no system available")
            if not s:
                break
            if "system_name" in s and s["system_name"] is not None:
                sys_locks.append({"name": s["system_name"], "tm": lock_tm})
                n = props_col.find(
                    {
                        "system_name": s["system_name"]
                    }
                ).count()
                print "%s adds %d properties" % (s["system_name"], n)
            else:
                sys_locks.append({"name": None, "tm": lock_tm})
                n = props_col.find(
                    {
                        "$or": [
                            {"system_name": {"$exists": False}},
                            {"system_name": None}
                        ]
                    }
                ).count()
                print "independent components add %d properties" % (n,)
            n_total += n


def acquire_properties(sys_locks, props_col, begin, chunks_col, chunk_size):
    properties = []
    first_bin = None
    for system in sys_locks:
        if system["name"] is not None:
            query = {"system_name": system["name"]}
        else:
            query = {
                "$or": [
                    {"system_name": {"$exists": False}},
                    {"system_name": None}
                ]
            }
        for prop in props_col.find(query):
            pid = prop["_id"]
            period = prop["meta"]["period"]
            graph_min = prop["meta"]["graph_min"]
            graph_max = prop["meta"]["graph_max"]
            lst_end = (begin -
                       timedelta(seconds=uniform(0, period)))
            chunks = chunks_col.find({"pid": pid}) \
                               .sort("bin", pymongo.DESCENDING) \
                               .limit(1)
            if chunks.count():
                chunk = chunks.next()
                nxt_bin = chunk["bin"] + chunk_size
                if nxt_bin >= begin:
                    p = Property(pid,
                                 timedelta(seconds=period),
                                 graph_min,
                                 graph_max,
                                 nxt_bin,
                                 chunk["end"])
                    if first_bin is None or nxt_bin < first_bin:
                        first_bin = nxt_bin
                else:
                    p = Property(pid,
                                 timedelta(seconds=period),
                                 graph_min,
                                 graph_max,
                                 begin,
                                 lst_end)
                    first_bin = begin
            else:
                p = Property(pid,
                             timedelta(seconds=period),
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
            s = sys_col.find_and_modify(
                {
                    "system_name": sys_lock["name"],
                    "$and": [
                        {"lock": {"$exists": True}},
                        {"lock": sys_lock["tm"]}
                    ]
                },
                {
                    "$set": {"lock": None, "random": random()}
                }
            )
        else:
            print "releasing independent components"
            s = sys_col.find_and_modify(
                {
                    "$or": [
                        {"system_name": {"$exists": False}},
                        {"system_name": None}
                    ],
                    "$and": [
                        {"lock": {"$exists": True}},
                        {"lock": sys_lock["tm"]}
                    ]
                },
                {
                    "$set": {"lock": None, "random": random()}
                }
            )
        if not s:
            sys_not_locked.append(sys_lock["name"])
    if sys_not_locked:
        if len(sys_not_locked) > 1:
            raise RuntimeError("oups, %s weren't locked anymore" %
                               ((", ").join(str(sys_not_locked)),))
        else:
            raise RuntimeError("oups, %s wasn't locked anymore" %
                               (str(sys_not_locked[0]),))


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
                              description=program_desc,
                              option_class=DatetimeOption)
        parser.add_option("--host", dest="host",
                          help="hostname or IP address of the MongoDB server "
                          "[default: %default]")
        parser.add_option("-p", "--port", dest="port", type="int",
                          help="port number on which to connect "
                          "[default: %default]")
        parser.add_option("-s", "--system", dest="systems", action="append",
                          help="system(s) to create data for [default: none]",
                          metavar="NAME")
        parser.add_option("-n", "--nprops", dest="n_props", type="int",
                          help="approx. integral number of properties to "
                          "create data for [default: %default] if, "
                          "no system is specified")
        parser.add_option("-b", "--begin", dest="begin", type="datetime",
                          help="start date to create data from "
                          "[default: %default]",
                          metavar="DATE")
        parser.add_option("-d", "--days", dest="days", type="int",
                          help="days that are added to 'begin' "
                          "to determine the stop date [default: %default]")
        parser.add_option("--chunksize", dest="chunk_size", type="int",
                          help="chunk size in seconds [default: %default]",
                          metavar="SECONDS")
        parser.add_option("--realtime", dest="realtime", action="store_true",
                          help="run data generation in realtime")

        # set defaults
        parser.set_defaults(host=HOST, port=27017,
                            n_props=15000,
                            begin="2013-10-01", days=1,
                            chunk_size=60,
                            realtime=False)

        # process options
        (opts, args) = parser.parse_args(argv)
        end = opts.begin + timedelta(days=opts.days)
        chunk_size = timedelta(seconds=opts.chunk_size)

        print "-" * 40
        print "host = %s" % (opts.host,)
        print "port = %d" % (opts.port,)
        if opts.systems:
            print "systems = %s" % (", ".join(opts.systems),)
        else:
            print "nprops = %d" % (opts.n_props,)
        print "begin = %s" % (str(opts.begin),)
        print "end = %s" % (str(end),)
        print "chunksize = %s" % (str(chunk_size),)
        if opts.realtime:
            print "realtime generation"

        # connect to db server, db and collections
        client = MongoClient(opts.host, opts.port)
        db = client.ctamonitoringtest
        chunks_collection = db.chunks
        properties_collection = db.properties
        statistics_collection = db.statistics
        systems_collection = db.systems

        system_locks = []
        try:
            # prepare data creation
            print "-" * 40
            acquire_systems(systems_collection, system_locks,
                            opts.systems, properties_collection, opts.n_props)
            properties, first_bin = acquire_properties(system_locks,
                                                       properties_collection,
                                                       opts.begin,
                                                       chunks_collection,
                                                       chunk_size)
            if properties:
                print "-" * 40
                print "nprops = %d" % (len(properties),)
                print "firstbin = %s" % (str(first_bin),)
                bin = first_bin
                statistics = Statistics()
                statistics.systems = [s["name"] for s in system_locks]
                statistics.n_props = len(properties)
                statistics.realtime = opts.realtime
                queue = Queue.Queue(3 * len(properties))
                wait = 10
                if not opts.realtime:
                    db_inserter = DBInserter(statistics_collection,
                                             chunks_collection,
                                             statistics, queue)
                else:
                    queue_out = Queue.Queue(math.ceil(1.1 * len(properties)))
                    db_scheduler = DBScheduler(queue_out, queue, chunk_size)
                    db_inserter = DBInserter(statistics_collection,
                                             chunks_collection,
                                             statistics, queue_out)
                    wait = max(wait, math.ceil(1.1 *
                                               get_total_seconds(chunk_size)))
                while bin < end:
                    for prop in properties:
                        if prop.nxt_bin > bin:
                            continue
                        prop.nxt_bin = bin + chunk_size
                        values = []
                        t = prop.lst_end
                        while True:
                            t += prop.period
                            if t >= prop.nxt_bin:
                                break
                            val = uniform(prop.min, prop.max)
                            values.append({"t": t, "val": val})
                        if not values:
                            continue
                        prop.lst_end = values[-1]["t"]
                        chunk = {
                            "begin": values[0]["t"],
                            "end": prop.lst_end,
                            "values": values,
                            "bin": bin,
                            "pid": prop.pid
                        }
                        while True:
                            try:
                                queue.put((bin, chunk, len(values)),
                                          block=True, timeout=wait)
                                break
                            except Queue.Full:
                                if (opts.realtime and
                                        not db_scheduler.is_alive()):
                                    raise
                                if not db_inserter.is_alive():
                                    raise
                    bin += chunk_size
                print "-" * 40
                print "flushing..."
                if opts.realtime:
                    db_scheduler.flush()
                queue.join()
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
