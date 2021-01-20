# Copyright 2020 Hewlett Packard Enterprise Development LP

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
    'defaultBatcherRetryPolicy': 1
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


options = Options()