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
import logging

from .cfs import components
from .cfs.options import options

LOGGER = logging.getLogger(__name__)


class Component(object):
    """Holds the data, including state, for a single component"""

    def __init__(self, data, retain_desired_state=False):
        self.id = data['id']
        self.error_count = data['error_count']
        self.tags = data.get('tags', {})
        self.config_name = data['desired_config']
        # config_limit - Comma-delimited string listing the layers that still need to be configured
        self.config_limit = ','.join([str(i) for i, layer in enumerate(data.get('desired_state', []))
                                     if layer.get('status', '').lower() == 'pending'])
        # latest_status/timestamp - Identifies if the most recent config attempt was failed/incomplete
        #   and when the most recent state was recorded
        self.latest_status = ''
        self.latest_timestamp = ''
        state = data.get('state', [])
        if len(state):
            recent_state = state[-1]
            self.latest_status = recent_state['status']
            self.latest_timestamp = recent_state['last_updated']
        # desired_state_hash is to determine if the desired_state has changed without needing to store the whole
        #   desired state data in memory.
        self.desired_state_hash = hash(':'.join(
            [f"{layer['commit']}{layer['playbook']}" for layer in data.get('desired_state', [])]))
        # Only retain desired state when it's actually going to be used
        # This should be reserved for iterating through components and not used for components stored in memory for an
        #   extended period of time to reduce memory consumption
        self.desired_state = []
        if retain_desired_state:
            self.desired_state = data.get('desired_state', [])
        # batch_key - Used to determine like components that can be configured together
        #   latest_status is used to separate batches for components that failed, and components that were incomplete
        self.batch_key = self.config_name + ':' + self.config_limit + ':' + self.latest_status

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
        for layer in self.desired_state:
            if layer.get('status', '').lower() == 'pending':
                new_state = {
                    'commit': layer.get('commit'),
                    'playbook': layer.get('playbook', options.default_playbook),
                    'clone_url': layer.get('clone_url'),
                    'status': status,
                    'session_name': session_name
                }
                patch = {'state_append': new_state}
                if error_count is not None:
                    patch['error_count'] = error_count
                components.patch_component(self.id, patch)
                if not all_layers:
                    return

    def increment_error_count(self, session_name=None):
        error_count = self.error_count + 1
        self.set_status('failed', session_name=session_name, error_count=error_count,
                        all_layers=False)
