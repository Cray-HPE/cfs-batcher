#
# MIT License
#
# (C) Copyright 2020-2024 Hewlett Packard Enterprise Development LP
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
import ujson as json
import logging
from requests.exceptions import HTTPError, ConnectionError
from urllib3.exceptions import MaxRetryError
from time import sleep
import uuid

from batcher.client import requests_retry_session
from . import ENDPOINT as BASE_ENDPOINT


LOGGER = logging.getLogger(__name__)
ENDPOINT = "%s/%s" % (BASE_ENDPOINT, __name__.lower().split('.')[-1])


def get_session(name):
    """Get a configuration (CFS) session"""
    url = ENDPOINT + '/' + name
    session = requests_retry_session()
    try:
        response = session.get(url)
        response.raise_for_status()
        return json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        # If the session is deleted, we need different handling than other errors
        if e.response.status_code == 404:
            raise e
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: {}".format(e))
    return {}


def iter_sessions():
    """Get information for all CFS sessions"""
    next_parameters = None
    while True:
        data = get_sessions(parameters=next_parameters)
        if not data:
            LOGGER.warning("Could not retrieve any session data. Retrying.")
            sleep(1)
            continue
        for session in data["sessions"]:
            yield session
        next_parameters = data["next"]
        if not next_parameters:
            break


def get_sessions(parameters=None):
    """Get a configuration (CFS) session"""
    session = requests_retry_session()
    try:
        if not parameters:
            parameters = {}
        response = session.get(ENDPOINT, params=parameters)
        response.raise_for_status()
        return json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
        raise e
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
        raise e
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: {}".format(e))
        raise e
    return None


def create_session(config, config_limit='', components=[], tags=None):
    """Create a configuration (CFS) session"""
    success = False
    name = 'batcher-' + str(uuid.uuid4())
    ansible_limit = ','.join(components)
    data = {'name': name,
            'configuration_name': config,
            'configuration_limit': config_limit,
            'ansible_limit': ansible_limit,
            'target': {'definition': 'dynamic'}}
    if tags:
        data['tags'] = tags
    LOGGER.debug('Submitting a session to CFS: {}'.format(data))
    session = requests_retry_session()
    try:
        response = session.post(ENDPOINT, json=data)
        response.raise_for_status()
        success = True
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    return success, name


def delete_session(name):
    """Create a configuration (CFS) session"""
    url = ENDPOINT + '/' + name
    session = requests_retry_session()
    try:
        response = session.delete(url)
        response.raise_for_status()
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))


def get_session_status(name):
    """Get the status for configuration (CFS) session"""
    data = get_session(name)
    session = data.get('status', {}).get('session', {})
    status = session.get('status', 'unknown')
    succeeded = session.get('succeeded', '')
    return status, succeeded
