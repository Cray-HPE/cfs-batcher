# Copyright 2020-2021 Hewlett Packard Enterprise Development LP
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
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# (MIT License)

import logging

from .cfs import components
from .cfs.options import options

LOGGER = logging.getLogger(__name__)
CONFIG_KEY_FIELDS = ['cloneUrl', 'playbook', 'commit']


class Component(object):
    """Holds the data, including state, for a single component"""

    def __init__(self, data):
        self.data = data
        self.id = data['id']
        self.error_count = data['errorCount']
        self.tags = data.get('tags', {})
        self.config_name = data['desiredConfig']
        config_limit = []
        desiredState = data.get('desiredState', {})
        for i, layer in enumerate(desiredState):
            if layer.get('status', '').lower() == 'pending':
                config_limit.append(str(i))
        if len(config_limit) == len(desiredState):
            self.config_limit = ''
        else:
            self.config_limit = ','.join(config_limit)
        self.config_key = self.config_name + ':' + self.config_limit

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Component):
            return self.id == other.id
        return False

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def set_status(self, status, session_name=None, error_count=None, all_layers=True):
        desiredState = self.data.get('desiredState', {})
        for layer in desiredState:
            if layer.get('status', '').lower() == 'pending':
                new_state = {
                    'commit': layer.get('commit') + status,
                    'playbook': layer.get('playbook', options.default_playbook),
                    'cloneUrl': layer.get('cloneUrl'),
                    'sessionName': session_name
                }
                patch = {'stateAppend': new_state}
                if error_count is not None:
                    patch['errorCount'] = error_count
                components.patch_component(self.id, patch)
                if not all_layers:
                    return

    def increment_error_count(self, session_name=None):
        error_count = self.error_count + 1
        self.set_status('_failed', session_name=session_name, error_count=error_count,
                        all_layers=False)
