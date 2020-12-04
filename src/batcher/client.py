# Copyright 2020, Cray Inc., A Hewlett Packard Enterprise Company

from . import PROTOCOL

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def requests_retry_session(retries=10, connect=10, backoff_factor=0.5,
                           status_forcelist=(500, 502, 503, 504),
                           session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount(PROTOCOL, adapter)
    return session
