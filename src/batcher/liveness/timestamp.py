#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
'''
A set of routines for creating or reading from an existing timestamp file.
Created on Mar 26, 2020

@author: jsl
'''
import logging
from datetime import datetime, timedelta

from batcher.liveness import TIMESTAMP_PATH
from batcher.cfs.options import Options

LOGGER = logging.getLogger(__name__)


class Timestamp(object):
    def __init__(self, path=TIMESTAMP_PATH, when=None):
        '''
        Creates a new timestamp representation to <path>; on initialization,
        this timestamp is written to disk in a persistent fashion.

        Newly initialized timestamps with a path reference to an existing file
        overwrites the file in question.
        '''
        self.path = path
        with open(self.path, 'w') as timestamp_file:
            if not when:
                # how?
                timestamp_file.write(str(datetime.now().timestamp()))
            else:
                timestamp_file.write(str(when.timestamp()))

    def __str__(self):
        return 'Timestamp from %s; age: %s' % (self.value.strftime("%m/%d/%Y, %H:%M:%S"), self.age)

    @classmethod
    def byref(cls, path):
        """
        Creates a new instance of a Timestamp without initializing it to disk.
        This is useful if you simply want to check the existence of a timestamp
        without altering it.
        """
        self = super().__new__(cls)
        self.path = path
        return self

    @property
    def value(self):
        """
        The timestamp value, as stored on disk. This property does not cache
        the value; instead it reads it each time the property is accessed.
        """
        try:
            with open(self.path, 'r') as timestamp_file:
                return datetime.fromtimestamp(float(timestamp_file.read().strip()))
        except FileNotFoundError:
            LOGGER.warning("Timestamp never initialized to '%s'" % (self.path))
            return datetime.fromtimestamp(0)

    @property
    def age(self):
        """
        How old this timestamp is, implemented as a timedelta object.
        """
        return datetime.now() - self.value

    @property
    def options(self):
        """
        A reference to an options object, which is instantiated upon first use.
        """
        try:
            return self._options
        except AttributeError:
            self._options = Options()
            return self._options

    @property
    def max_age(self):
        """
        The maximum amount of time that can elapse before we consider the timestamp
        as invalid. This is defined as a period of time that normally is required for
        a cycle of batches to complete, plus the period of time that is specified as
        user configuration through the CFS API.

        This value is returned as a timedelta object.
        """
        api_option = timedelta(seconds=int(self.options.batcher_check_interval))
        computation_time = timedelta(seconds=30)
        return api_option + computation_time

    @property
    def alive(self):
        """
        Returns a true or false, depending on if this service is considered alive/viable.
        True if the service has a new enough timestamp; false otherwise.
        """
        return self.age < self.max_age
