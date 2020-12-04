# Copyright 2020 Hewlett Packard Enterprise Development LP

import json
import logging
from requests.exceptions import HTTPError, ConnectionError
from urllib3.exceptions import MaxRetryError

from batcher.client import requests_retry_session
from . import ENDPOINT as BASE_ENDPOINT


LOGGER = logging.getLogger(__name__)
ENDPOINT = "%s/%s" % (BASE_ENDPOINT, __name__.lower().split('.')[-1])


def get_components(**kwargs):
    """Get components and state information stored in CFS"""
    components = []
    kwargs['configDetails'] = True
    session = requests_retry_session()
    try:
        response = session.get(ENDPOINT, params=kwargs)
        response.raise_for_status()
        components = json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: {}".format(e))
    LOGGER.debug('Received data for {} components'.format(len(components)))
    return components


def get_component(id, **kwargs):
    """Get state information for a single component stored in CFS"""
    url = ENDPOINT + '/' + id
    component = {}
    kwargs['configDetails'] = True
    session = requests_retry_session()
    try:
        response = session.get(url, params=kwargs)
        response.raise_for_status()
        component = json.loads(response.text)
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: {}".format(e))
    return component


def patch_component(id, patch):
    """Update the state information for a single Component"""
    success = False
    url = ENDPOINT + '/' + id
    session = requests_retry_session()
    try:
        response = session.patch(url, json=patch)
        response.raise_for_status()
        success = True
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    return success
