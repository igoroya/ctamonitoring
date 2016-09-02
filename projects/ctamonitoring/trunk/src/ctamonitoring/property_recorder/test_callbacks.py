'''
Unit test module for callbacks

Here we test the base class for all these callbacks and
also the CBFactory to get them

@author: igoroya
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
'''
import unittest
from ctamonitoring.property_recorder.backend.dummy.registry import Buffer
from ctamonitoring.property_recorder import callbacks
from ctamonitoring.property_recorder.frontend_exceptions import (
    UnsupporterPropertyTypeError
    )
from ctamonitoring.property_recorder.callbacks import CBFactory, BaseArchCB

from ACS import CBDescOut  # @UnresolvedImport
from ACSErr import Completion  # @UnresolvedImport
from ACS import (
    _objref_ROBool,  # @UnresolvedImport
    _objref_RObooleanSeq,   # @UnresolvedImport
    _objref_ROfloat,       # @UnresolvedImport
    _objref_ROlongLong,    # @UnresolvedImport
    _objref_ROstring,      # @UnresolvedImport
    _objref_ROuLongLong,    # @UnresolvedImport
    _objref_ROOnOffSwitch,  # @UnresolvedImport
    _objref_ROdouble,       # @UnresolvedImport
    _objref_ROfloatSeq,  # @UnresolvedImport
    _objref_ROlongSeq,      # @UnresolvedImport
    _objref_ROstringSeq,    # @UnresolvedImport
    _objref_ROuLongSeq,     # @UnresolvedImport
    _objref_ROboolean,      # @UnresolvedImport
    _objref_ROdoubleSeq,    # @UnresolvedImport
    _objref_ROlong,         # @UnresolvedImport
    _objref_ROpattern,     # @UnresolvedImport
    _objref_ROuLong,    # @UnresolvedImport
    _objref_RWBool,         # @UnresolvedImport
    _objref_RWbooleanSeq,   # @UnresolvedImport
    _objref_RWfloat,        # @UnresolvedImport
    _objref_RWlongLong,     # @UnresolvedImport
    _objref_RWstring,       # @UnresolvedImport
    _objref_RWuLongSeq,     # @UnresolvedImport
    _objref_RWOnOffSwitch,  # @UnresolvedImport
    _objref_RWdouble,       # @UnresolvedImport
    _objref_RWfloatSeq,     # @UnresolvedImport
    _objref_RWlongSeq,      # @UnresolvedImport
    _objref_RWuLong,        # @UnresolvedImport
    _objref_RWboolean,      # @UnresolvedImport
    _objref_RWdoubleSeq,    # @UnresolvedImport
    _objref_RWlong,         # @UnresolvedImport
    _objref_RWpattern,      # @UnresolvedImport
    _objref_RWuLongLong    # @UnresolvedImport
    )
from mock import (create_autospec, MagicMock)
from Acspy.Common.Log import logging

__version__ = "$Id$"


class BaseArchCBTest(unittest.TestCase):

    def setUp(self):

        self.my_property = 'prop'
        self.backend_buffer = Buffer()

        logging.basicConfig()
        """
        Note that we need to mock the ACS logger if we want to run the test
        with ACS down. This is because (i) the ACS logger and the Python Logger
        are not compatible; (ii) the ACS logger, if created, blocks the main
        process if ACS is not up!
        """
        self.dummy_logger = create_autospec(logging.Logger)("TestLogger")
        self.dummy_logger.logDebug = MagicMock()

    def test_init(self):

        cb = BaseArchCB(self.my_property, self.backend_buffer,
                        self.dummy_logger)
        cb._logger = self.dummy_logger
        self.assertEqual('INIT', cb.status)

    def test_working(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer,
                        self.dummy_logger)
        cb._logger = self.dummy_logger
        value = 1
        completion = Completion(1, 0, 0, [])
        desc = CBDescOut(1, "e")
        cb.working(value, completion, desc)
        self.assertEqual('WORKING', cb.status)

    def test_done(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer,
                        self.dummy_logger)
        cb._logger = self.dummy_logger
        value = 1
        completion = Completion(1, 0, 0, [])
        desc = CBDescOut(1, "e")
        cb.done(value, completion, desc)
        self.assertEqual('DONE', cb.status)

    def test_last(self):
        cb = BaseArchCB(self.my_property, self.backend_buffer,
                        self.dummy_logger)
        cb._logger = self.dummy_logger
        self.assertRaises(NotImplementedError, cb.last)


class CBFactoryTest(unittest.TestCase):

    def setUp(self):

        self.backend_buffer = Buffer()

        logging.basicConfig()
        self.dummy_logger = logging.Logger("test_logger")
        self.dummy_logger.setLevel(logging.WARNING)

    def test_get_callback(self):
        # RObool seems to be an ACS mistake, ROboolean should be used instead
        prop = _objref_ROBool(None)
        self.assertRaises(
            UnsupporterPropertyTypeError,
            CBFactory.get_callback, prop, "",
            self.backend_buffer, self.dummy_logger)

        # RObool seems to be an ACS mistake
        prop = _objref_ROboolean(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))

        prop = _objref_RObooleanSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBboolSeq))

        prop = _objref_ROfloat(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloat))

        prop = _objref_ROlongLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongLong))

        prop = _objref_ROstring(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstring))

        prop = _objref_ROuLongLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongLong))

        prop = _objref_ROOnOffSwitch(None)
        self.assertRaises(
            UnsupporterPropertyTypeError,
            CBFactory.get_callback,
            prop, "", self.backend_buffer, self.dummy_logger)

        prop = _objref_ROdouble(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdouble))

        prop = _objref_ROfloatSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloatSeq))

        prop = _objref_ROlongSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongSeq))

        prop = _objref_ROstringSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstringSeq))

        prop = _objref_ROuLongSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongSeq))

        prop = _objref_ROboolean(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))

        prop = _objref_ROdoubleSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdoubleSeq))

        prop = _objref_ROlong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlong))

        prop = _objref_ROpattern(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBpatternValueRep))

        prop = _objref_ROuLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLong))

        prop = _objref_RWBool(None)
        self.assertRaises(
            UnsupporterPropertyTypeError,
            CBFactory.get_callback,
            prop, "",
            self.backend_buffer, self.dummy_logger)

        prop = _objref_RWbooleanSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBboolSeq))

        prop = _objref_RWfloat(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloat))

        prop = _objref_RWlongLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongLong))

        prop = _objref_RWstring(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBstring))

        prop = _objref_RWuLongSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongSeq))

        prop = _objref_RWOnOffSwitch(None)
        self.assertRaises(
            UnsupporterPropertyTypeError,
            CBFactory.get_callback, prop, "",
            self.backend_buffer, self.dummy_logger)

        prop = _objref_RWdouble(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdouble))

        prop = _objref_RWfloatSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBfloatSeq))

        prop = _objref_RWlongSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlongSeq))

        prop = _objref_RWuLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLong))

        prop = _objref_RWboolean(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBbool))

        prop = _objref_RWdoubleSeq(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBdoubleSeq))

        prop = _objref_RWlong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBlong))

        prop = _objref_RWpattern(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBpatternValueRep))

        prop = _objref_RWuLongLong(None)
        cb = CBFactory.get_callback(prop, "", self.backend_buffer,
                                    self.dummy_logger)
        self.assertTrue(isinstance(cb, callbacks.ArchCBuLongLong))


if __name__ == '__main__':
    unittest.main()
