# Copyright 2020 Hewlett Packard Enterprise Development LP

from collections import defaultdict, deque
import logging
from requests.exceptions import HTTPError
import time

from .cfs.options import options
from .cfs import sessions
from .cfs import components
from .component import Component

LOGGER = logging.getLogger(__name__)

RECENT_SESSIONS_SIZE = 20
MIN_BACKOFF = 60
MAX_BACKOFF = 60 * 60 * 6  # 24 hours

"""
The combination of batch manager and batch ensure that a desired
configuration for a component is not added and run multiple times.

To avoid unecessary configuration, a batch tracks the associated CFS
session.  This ensures that components are not queued for configuration if
they are already queued, or are currently being configured.  On completion
of the session, there are additional checks to ensure the component's
state was updated, either with a failure or success.  If not the component
will be updated with a failure status if the session failed, or a skipped
status if the session succeeded to avoid reconfiguration in cases where the
desired configuration does not affect the component (e.g. a playbook for
Application nodes set as the desired state for a Compute node)
"""


class BatchManager(object):
    """Manages multiple Batch objects"""

    def __init__(self):
        # self.batches is a dict where the key is a desired configuration, and
        # the value is a list of Batch objects
        self.batches = defaultdict(list)
        # self.components is a set of all components currently in batches,
        # either waiting on configuration, or being configured
        self.components = set()
        # The following are used to track failures and provide backoffs
        self.recent_sessions = deque([True] * RECENT_SESSIONS_SIZE, RECENT_SESSIONS_SIZE)
        self.current_backoff = 0
        self.backoff_start = 0
        # If there are batcher is restarted, state will need to be rebuilt.
        self._rebuild_state()

    def check_status(self):
        """Remove batches for which the sessions have been completed"""
        LOGGER.debug('Checking batch session status')
        finished_keys = []
        n_complete = 0
        for key, batches in self.batches.items():
            remaining_batches = []
            for batch in batches:
                complete, success = batch.check_complete()
                if complete:
                    self.recent_sessions.append(success)
                    self.components = self.components.difference(
                        batch.components)
                    n_complete += 1
                else:
                    remaining_batches.append(batch)
            # Remove completed batches, and remove the key
            # if that configuration key no longer has batches associated
            if not remaining_batches:
                finished_keys.append(key)
            else:
                self.batches[key] = remaining_batches
        for key in finished_keys:
            del self.batches[key]
        if n_complete:
            LOGGER.info('{} batches/sessions have completed'.format(
                n_complete))
            self.update_backoff()

    def update_batches(self):
        LOGGER.debug('Checking components for new configuration states')
        i = 0
        data = components.get_components(enabled=True, status='pending')
        for component_data in data:
            component = Component(component_data)
            self.add(component)
            i += 1
        if i:
            LOGGER.debug('Found {} components that need updates'.format(i))

    def add(self, component):
        """Adds a component to the appropriate batch"""
        if component in self.components:
            return
        for batch in self.batches[component.config_key]:
            if batch.try_add(component):
                break
        else:
            new_batch = Batch(component)
            self.batches[component.config_key].append(new_batch)

    def send_batches(self):
        """Sends any batches that are ready"""
        LOGGER.debug('Sending completed batches')
        if self.backoff():
            return
        n_complete = 0
        for key, batches in self.batches.items():

            for batch in batches:
                if batch.try_send():
                    n_complete += 1
        if n_complete:
            msg = 'Successfully submited {} batches for configuration'
            LOGGER.info(msg.format(n_complete))

    """
    Backoff functions
    This is intended to help avoid runaway configuration attempts in cases where configuration
    will never succeed, such as invalid desired configuration with an unlimited number of
    retires.
    """

    def update_backoff(self):
        if any(self.recent_sessions):  # At least one session succeeded
            if self.current_backoff != 0:
                self.current_backoff = 0
                LOGGER.info('A session has succeeded.  Resuming normal operations')
            return

        if time.time() - self.backoff_start >= self.current_backoff:  # The previous backoff expired
            if self.current_backoff == 0:
                self.current_backoff = MIN_BACKOFF
            else:
                self.current_backoff = min(MAX_BACKOFF, self.current_backoff * 2)
            LOGGER.warning('The {} most recent configuration sessions have failed. Halting session '
                           'creation for {} seconds'.format(RECENT_SESSIONS_SIZE,
                                                            self.current_backoff))
            self.backoff_start = time.time()

    def backoff(self):
        if time.time() - self.backoff_start < self.current_backoff:
            return True
        return False

    def _rebuild_state(self):
        sessions_data = sessions.get_sessions()
        while sessions_data is None:
            LOGGER.info('Waiting for CFS to become available')
            sessions_data = sessions.get_sessions()
            time.sleep(1)
        n = 0
        for session in sessions_data:
            status = session.get('status', {}).get('session', {}).get('status', '')
            if 'batcher' in session.get('name', '') and status != 'complete':
                batch = Batch._rebuild_from_session(session)
                if batch.components:
                    config_key = next(iter(batch.components)).config_key
                    self.batches[config_key].append(batch)
                    n += 1
        if n:
            LOGGER.info('Rebuilt previous state.  Found {} incomplete sessions/batches.'.format(n))


class Batch(object):
    """Manages a collection of similar components"""

    def __init__(self, component):
        self.components = set()
        if not component:
            return

        self.components.add(component)

        self.config_name = component.config_name
        self.config_limit = component.config_limit

        self.session_name = ''
        self.start = time.time()

    @classmethod
    def _rebuild_from_session(cls, session):
        batch = Batch(None)
        batch.session_name = session.get('name', '')
        config_data = session['configuration']
        batch.config_name = config_data.get('name')
        batch.config_limit = config_data.get('limit')
        ansible_data = session['ansible']
        component_ids = ansible_data.get('limit').split(',')
        for component_id in component_ids:
            batch.components.add(Component(components.get_component(component_id)))

        return batch

    def try_add(self, component):
        """Add a component if possible"""
        if component in self.components:
            return True  # The component is already in this batch
        if len(self.components) < options.batch_size and not self.session_name:
            self.components.add(component)
            return True
        return False

    def try_send(self):
        """Create a config session for the batch if needed and possible"""
        if not self.session_name and (self.full or self.overdue):
            component_ids = [component.id for component in self.components]
            tags = self._get_tags()
            success, session_name = sessions.create_session(
                config=self.config_name,
                config_limit=self.config_limit,
                components=component_ids,
                tags=tags)
            if success:
                self.session_name = session_name
            return success
        return False

    def check_complete(self):
        """Cleanup the batch/session if the CFS session is complete"""
        complete = False
        success = False
        try:
            status = self.get_status()
            if status == 'complete' or status == 'failed':
                incomplete_components = components.get_components(
                    status='pending', ids=[c.id for c in self.components])
                if incomplete_components:
                    self.component_map = {c.id: c for c in self.components}
                    for component_data in incomplete_components:
                        current_component = Component(component_data)
                        self._check_component_complete(current_component, status)
                complete = True
                if status == 'complete':
                    success = True
            elif status == 'deleted':
                LOGGER.info('Session {} no longer exists'.format(self.session_name))
                complete = True
        except Exception as e:
            LOGGER.warning('Unexpected exception checking session status: {}'.format(e))
            complete = False
        return complete, success

    def _check_component_complete(self, current_component, status):
        component = self.component_map[current_component.id]
        if component.config_key == current_component.config_key:
            if status == 'complete':
                # This can occur when the desired configuration does attempt any changes to the
                # component, so Ansible does not report any status for the component
                LOGGER.debug('Component {} appears to have been skipped'.format(component.id))
                component.set_status('_skipped', session_name=self.session_name)
            if status == 'failed' and component.error_count == current_component.error_count:
                # This can occur when the sessions are failing prior to Ansible running, such as
                # an invalid desired configuration.
                LOGGER.debug('Component {} appears to have an incorrect error count'.format(
                    component.id))
                component.increment_error_count(session_name=self.session_name)

    @property
    def full(self):
        """True if the batch is full"""
        if len(self.components) >= options.batch_size:
            return True
        return False

    @property
    def overdue(self):
        """True if the batch has been waiting too long"""
        if (time.time() - self.start) > options.batch_window:
            return True
        return False

    def get_status(self):
        if self.session_name:
            try:
                status, succeeded = sessions.get_session_status(self.session_name)
            except HTTPError as e:
                if e.response.status_code == 404:
                    return 'deleted'
            LOGGER.debug(
                'Session status for {} is status:{} completed:{}'.format(
                    self.session_name, status, succeeded))
            if succeeded == 'false':
                return 'failed'
            return status.lower()
        else:
            return 'new'

    def _get_tags(self):
        """Returns a dictionary of all of tags common to all components in the batch"""
        keys = None
        for component in self.components:
            if keys is None:
                keys = component.tags.keys()
                continue
            keys = keys & component.tags.keys()
        tags = {}
        for key in keys:
            value = next(iter(self.components)).tags[key]
            if all([value == component.tags[key] for component in self.components]):
                tags[key] = value
        return tags

