# Copyright 2020 Hewlett Packard Enterprise Development LP

import json
import logging
from requests.exceptions import HTTPError, ConnectionError
from urllib3.exceptions import MaxRetryError
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


def get_sessions():
    """Get a configuration (CFS) session"""
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
    return None


def create_session(config, config_limit='', components=[], tags=None):
    """Create a configuration (CFS) session"""
    success = False
    name = 'batcher-' + str(uuid.uuid4())
    ansible_limit = ','.join(components)
    data = {'name': name,
            'configurationName': config,
            'configurationLimit': config_limit,
            'ansibleLimit': ansible_limit,
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


def get_session_status(name):
    """Get the status for configuration (CFS) session"""
    data = get_session(name)
    session = data.get('status', {}).get('session', {})
    status = session.get('status', 'unknown')
    succeeded = session.get('succeeded', '')
    return status, succeeded
