#
# MIT License
#
# (C) Copyright 2020-2026 Hewlett Packard Enterprise Development LP
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
from time import sleep
from typing import Optional

from csm_utils.logging import compact_response_text, exc_type_msg
from requests.exceptions import HTTPError, ConnectionError, ReadTimeout
from urllib3.exceptions import MaxRetryError

from batcher.client import requests_retry_session
from . import ENDPOINT as BASE_ENDPOINT


LOGGER = logging.getLogger(__name__)
ENDPOINT = "%s/%s" % (BASE_ENDPOINT, __name__.lower().split('.')[-1])


def get_session(name):
    """Get a configuration (CFS) session"""
    url = ENDPOINT + '/' + name
    session = requests_retry_session()
    LOGGER.debug("GET %s", url)
    try:
        response = session.get(url)
        response.raise_for_status()
        data = json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: %s", exc_type_msg(e))
        return {}
    except HTTPError as e:
        # If the session is deleted, we need different handling than other errors
        if e.response.status_code == 404:
            raise e
        LOGGER.error("Unexpected response from CFS: %s", exc_type_msg(e))
        return {}
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: %s", exc_type_msg(e))
        return {}
    LOGGER.debug("GET %s response=%s", url, compact_response_text(response.text))
    return data


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
    if not parameters:
        parameters = {}
    LOGGER.debug("GET %s (params=%s)", ENDPOINT, parameters)
    try:
        response = session.get(ENDPOINT, params=parameters)
        response.raise_for_status()
        data = json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: %s", exc_type_msg(e))
        raise e
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: %s", exc_type_msg(e))
        raise e
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: %s", exc_type_msg(e))
        raise e
    LOGGER.debug(
        "GET %s (params=%s) response=%s",
        ENDPOINT,
        parameters,
        compact_response_text(response.text),
    )
    return data


def create_session(
    session_name: str,
    config: str,
    config_limit: str = '',
    components: list[str] = [],
    tags: Optional[str] = None,
) -> bool:
    """
    Create a configuration (CFS) session
    Return True if successful OR if the session already exists
    Return False otherwise

    Batcher uses UUIDs for session names, and the number of possible UUIDs
    is so vast that we can safely ignore the possibility that an existing
    session was not created by us.
    """
    ansible_limit = ','.join(components)
    data = {'name': session_name,
            'configuration_name': config,
            'configuration_limit': config_limit,
            'ansible_limit': ansible_limit,
            'target': {'definition': 'dynamic'}}
    if tags:
        data['tags'] = tags
    LOGGER.debug("Submitting a session to CFS: %s", data)
    session = requests_retry_session()
    try:
        response = session.post(ENDPOINT, json=data)
        LOGGER.debug("New session response=%s", compact_response_text(response.text))
        response.raise_for_status()
        return True
    except (ConnectionError, MaxRetryError, ReadTimeout) as err:
        LOGGER.error("Unable to connect to CFS: %s", exc_type_msg(err))
    except HTTPError as err:
        if err.response.status_code == 409:
            # This means we succeeded in creating the session previously, but
            # failed to record that fact. This can be the case when the
            # request times out. In this case, we just report success.
            LOGGER.debug(exc_type_msg(err))
            LOGGER.info("CFS session '%s' already exists", session_name)
            return True
        LOGGER.error("Unexpected response from CFS: %s", exc_type_msg(err))
    return False


def delete_session(name):
    """Create a configuration (CFS) session"""
    url = ENDPOINT + '/' + name
    session = requests_retry_session()
    LOGGER.debug("DELETE %s", url)
    try:
        response = session.delete(url)
        response.raise_for_status()
        LOGGER.debug("DELETE %s succeeded", url)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: %s", exc_type_msg(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: %s", exc_type_msg(e))


def get_session_status(name):
    """Get the status for configuration (CFS) session"""
    data = get_session(name)
    session = data.get('status', {}).get('session', {})
    status = session.get('status', 'unknown')
    succeeded = session.get('succeeded', '')
    return status, succeeded
