#
# MIT License
#
# (C) Copyright 2020-2023 Hewlett Packard Enterprise Development LP
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

from batcher.client import requests_retry_session
from . import ENDPOINT as BASE_ENDPOINT


LOGGER = logging.getLogger(__name__)
ENDPOINT = "%s/%s" % (BASE_ENDPOINT, __name__.lower().split('.')[-1])


def iter_components(**kwargs):
    """Get information for all CFS sessions"""
    kwargs['config_details'] = True
    kwargs['state_details'] = True
    next_parameters = kwargs
    while True:
        data = get_components(parameters=next_parameters)
        for component in data["components"]:
            yield component
        next_parameters = data["next"]
        if not next_parameters:
            break


def get_components(parameters=None):
    """Get components and state information stored in CFS"""
    if not parameters:
        parameters = {}
    session = requests_retry_session()
    try:
        response = session.get(ENDPOINT, params=parameters)
        response.raise_for_status()
        components_data = json.loads(response.text)
        LOGGER.debug('Received data for {} components'.format(len(components_data["components"])))
        return components_data
    except (ConnectionError, MaxRetryError) as e:
        LOGGER.error("Unable to connect to CFS: {}".format(e))
    except HTTPError as e:
        LOGGER.error("Unexpected response from CFS: {}".format(e))
    except json.JSONDecodeError as e:
        LOGGER.error("Non-JSON response from CFS: {}".format(e))
    return None


def get_component(id, **kwargs):
    """Get state information for a single component stored in CFS"""
    url = ENDPOINT + '/' + id
    component = {}
    kwargs['config_details'] = True
    kwargs['state_details'] = True
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
