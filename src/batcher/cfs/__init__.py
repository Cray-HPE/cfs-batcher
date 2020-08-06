# Copyright 2020, Cray Inc., A Hewlett Packard Enterprise Company

from batcher import PROTOCOL

API_VERSION = 'v1'
SERVICE_NAME = 'cray-cfs-api'
ENDPOINT = "%s://%s/apis/cfs" % (PROTOCOL, SERVICE_NAME)
