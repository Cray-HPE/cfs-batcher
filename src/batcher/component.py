# © Copyright 2020 Hewlett Packard Enterprise Development LP

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
        desiredState = self.data.get('desiredState', {})
        self.config_key = ':'.join([v for k, v in
                                   desiredState.items()
                                   if k in CONFIG_KEY_FIELDS])

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

    def set_status(self, status, session_name=None, error_count=None):
        desiredState = self.data.get('desiredState', {})
        new_state = desiredState.copy()
        if not new_state.get('cloneUrl'):
            new_state['cloneUrl'] = options.default_clone_url
        if not new_state.get('playbook'):
            new_state['playbook'] = options.default_playbook
        del new_state['lastUpdated']
        commit = desiredState.get('commit', '') + status
        new_state['commit'] = commit
        patch = {'state': new_state}
        if session_name:
            patch['sessionName'] = session_name
        if error_count is not None:
            patch['errorCount'] = error_count
        components.patch_component(self.id, patch)

    def increment_error_count(self, session_name=None):
        error_count = self.error_count + 1
        self.set_status('_failed', session_name=session_name, error_count=error_count)
