__version__ = "$Id$"


"""
A ring buffer.

@author: tschmidt
@organization: DESY Zeuthen
@copyright: cta-observatory.org
@version: $Id$
@change: $LastChangedDate$
@change: $LastChangedBy$
@requires: collections
@requires: ctamonitoring.property_recorder.backend.exceptions
@requires: threading
"""


from collections import deque
from ctamonitoring.property_recorder.backend.exceptions \
    import InterruptedException
from threading import Condition
from threading import Event


class _DownCounter(object):
    def __init__(self, count):
        self._cond = Condition()
        if count < 0:
            self._count = 0
        else:
            self._count = count
        self._terminated = False

    def dec(self):
        with self._cond:
            if self._count:
                self._count -= 1
                if not self._count:
                    self._cond.notify()
            return self._count

    def terminate(self):
        with self._cond:
            if self._count and not self._terminated:
                self._terminated = True
                self._cond.notify()

    def wait(self, timeout=None):
        with self._cond:
            if self._count and not self._terminated:
                self._cond.wait(timeout)
            if self._terminated:
                raise InterruptedException()
            return self._count


class _Trigger(object):
    def __init__(self, n):
        if n < 0:
            self.n = 0
        else:
            self.n = n
        self.terminated = False
        self.trigger = Event()
        self.trigger.clear()


class RingBuffer(object):
    """
    RingBuffer is a data structure that uses a single, fixed-size buffer
    as if it were connected end-to-end.

    When the buffer is filled, new data is written
    starting at the beginning of the buffer and overwriting the old.

    RingBuffer is typically used in a producer/consumer scheme.
    """

    def __init__(self, maxsize=0):
        """
        ctor.

        @param maxsize: Sets the upperbound limit on the number of items
        that can be placed in the buffer before overwriting old items.
        If maxsize is less than or equal to zero, the buffer size is infinite.
        Optional, default is 0.
        @type maxsize: int
        """
        if maxsize > 0:
            self._maxsize = maxsize
        else:
            self._maxsize = None
        self._cond = Condition()
        self._buf = deque()
        self._flushers = []
        self._getters = []
        self._flush = False
        self._flush_all = False
        self._terminating = False
        self._terminated = False

    def _decrement_flushers(self):
        self._flush = False
        for f in self._flushers:
            self._flush |= bool(f.dec())

    def _trigger(self):
        if (self._getters and
            not self._getters[0].trigger.is_set() and
            (self._flush or
             self._flush_all or
             self._terminating or
             self._getters[0].n <= len(self._buf))):
            self._getters[0].trigger.set()

    def add(self, item):
        """
        Add a new item to the buffer.

        Overwrite the oldest if the buffer is full.
        @param item: The new item.
        """
        with self._cond:
            if self._maxsize and (self._maxsize == len(self._buf)):
                self._buf.popleft()
                self._decrement_flushers()
            self._buf.append(item)
            self._trigger()

    def _test_terminated(self):
        if self._terminated:
                raise InterruptedException()

    def flush(self, current=False):
        """
        Block until all items in the buffer have been removed.

        @param current: Block until all items currently included have been
        removed or overwritten OR until the buffer is empty.
        Optional, default is False.
        @type current: boolean.
        @raise ctamonitoring.property_recorder.backend.exceptions.InterruptedException:
        if flush() is blocking and terminate() is called or
        if get() is called after terminate().
        """
        if current:
            flusher = None
            with self._cond:
                if self._buf:
                    self._test_terminated()
                    flusher = _DownCounter(len(self._buf))
                    self._flushers.append(flusher)
                    self._flush = True
                    self._trigger()
            if flusher is not None:
                try:
                    flusher.wait()
                finally:
                    with self._cond:
                        self._flushers.remove(flusher)
        else:
            with self._cond:
                if self._buf:
                    self._test_terminated()
                    self._flush_all = True
                    self._trigger()
                    self._cond.wait()
                    if self._flush_all:
                        raise InterruptedException()

    def _get_items(self, items, n):
        while len(items) < n and self._buf:
            items.append(self._buf.popleft())
            self._decrement_flushers()
        if not self._buf:
            self._flush_all = False
            self._cond.notify_all()

    def get(self, n=1, timeout=None):
        """
        Remove and return items from the buffer.

        Blocks until n items are available but at most timeout seconds.
        May return before timeout seconds if a flush is requested and items
        are available.
        @param n: Return upto n items. Optional, default is 1.
        @type n: int
        @param timeout: Timeout for the operation in seconds
        (or fractions thereof). Optional, default is None.
        @type timeout: float or none type
        @return: A list of items.
        @rtype: list
        @raise InterruptedException: If get() is blocking and terminate()
        is called or if get() is called after terminate().
        """
        items = []
        if n < 0:
            n = 0
        elif self._maxsize and n > self._maxsize:
            n = self._maxsize
        getter = None
        with self._cond:
            self._test_terminated()
            if not n:
                pass
            elif not self._getters and n <= len(self._buf):
                self._get_items(items, n)
            else:
                getter = _Trigger(n)
                self._getters.append(getter)
        if getter is not None:
            try:
                getter.trigger.wait(timeout)  # shouldn't throw but who knows
            except:
                with self._cond:
                    self._getters.remove(getter)
                    raise
            else:
                with self._cond:
                    first_getter = getter is self._getters[0]
                    self._getters.remove(getter)
                    if (timeout is None or timeout > 0):
                        self._test_terminated()
                    # we could simplify this to just testing terminated and
                    # first_getter since we currently only trigger the
                    # first getter.  however it may change how we trigger
                    # getters so, keep testing if the getter was triggered or
                    # if it is the first one.
                    if (not getter.terminated and
                            (getter.trigger.is_set() or first_getter)):
                        self._get_items(items, n)
                        if (self._terminating and
                                (not self._buf or not self._getters)):
                            self._terminate()
                        else:
                            self._trigger()
        return items

    def terminate(self):
        """Terminate consumers."""
        with self._cond:
            if not self._terminating and not self._terminated:
                if not self._buf or not self._getters:
                    self._terminate()
                else:
                    self._terminating = True
                    self._trigger()

    def _terminate(self):
        for g in self._getters:
            if not g.trigger.is_set():
                g.terminated = True
                g.trigger.set()
        for f in self._flushers:
            f.terminate()
        self._cond.notify_all()
        self._terminated = True
        self._terminating = False
