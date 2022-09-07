#
# MIT License
#
# (C) Copyright 2020-2022 Hewlett Packard Enterprise Development LP
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
import logging
import json
from requests.exceptions import HTTPError, ConnectionError
from urllib3.exceptions import MaxRetryError

from batcher.client import requests_retry_session
from . import ENDPOINT as BASE_ENDPOINT

LOGGER = logging.getLogger(__name__)
ENDPOINT = "%s/%s" % (BASE_ENDPOINT, __name__.lower().split('.')[-1])

DEFAULTS = {
    'batcherCheckInterval': 10,
    'batchSize': 25,
    'batchWindow': 60,
    'defaultBatcherRetryPolicy': 3,
    'batcherMaxBackoff': 60 * 60,  # 1 hour
    'batcherDisable': False,
    'batcherPendingTimeout': 300,
}


class Options():
    """
    Handler for reading configuration options from the CFS api

    This caches the options so that frequent use of these options do not all
    result in network calls.
    """
    def __init__(self):
        self.options = DEFAULTS

    def update(self):
        """Refreshes the cached options data"""
        options = self._read_options()
        if options:
            self.options.update(options)
            patch = {}
            for key, value in DEFAULTS.items():
                if key not in options:
                    LOGGER.info("Setting option {} to {}.".format(key, str(value)))
                    patch[key] = value
            self._patch_options(patch)

    def _read_options(self):
        """Retrieves the current options from the CFS api"""
        session = requests_retry_session()
        try:
            response = session.get(ENDPOINT)
            response.raise_for_status()
            return json.loads(response.text)
        except (ConnectionError, MaxRetryError) as e:
            LOGGER.error("Unable to connect to CFS: {}".format(e))
        except HTTPError as e:
            LOGGER.error("Unexpected response from CFS: {}".format(e))
        except json.JSONDecodeError as e:
            LOGGER.error("Non-JSON response from CFS: {}".format(e))
        return {}

    def _patch_options(self, obj):
        """Add missing options to the CFS api"""
        session = requests_retry_session()
        try:
            response = session.patch(ENDPOINT, json=obj)
            response.raise_for_status()
        except (ConnectionError, MaxRetryError) as e:
            LOGGER.error("Unable to connect to CFS: {}".format(e))
        except HTTPError as e:
            LOGGER.error("Unexpected response from CFS: {}".format(e))

    def get_option(self, key, type):
        return type(self.options[key])

    @property
    def batcher_check_interval(self):
        return self.get_option('batcherCheckInterval', int)

    @property
    def batch_size(self):
        return self.get_option('batchSize', int)

    @property
    def batch_window(self):
        return self.get_option('batchWindow', int)

    @property
    def default_batcher_retry_policy(self):
        return self.get_option('defaultBatcherRetryPolicy', int)

    @property
    def default_playbook(self):
        return self.get_option('defaultPlaybook', str)

    @property
    def max_backoff(self):
        return self.get_option('batcherMaxBackoff', int)

    @property
    def disable(self):
        return self.get_option('batcherDisable', bool)

    @property
    def pending_timeout(self):
        return self.get_option('batcherPendingTimeout', int)


options = Options()
