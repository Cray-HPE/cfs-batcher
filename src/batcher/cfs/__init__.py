# Copyright 2020 Hewlett Packard Enterprise Development LP

from batcher import PROTOCOL

API_VERSION = 'v2'
SERVICE_NAME = 'cray-cfs-api'
ENDPOINT = "%s://%s/%s" % (PROTOCOL, SERVICE_NAME, API_VERSION)
