# © Copyright 2020-2021 Hewlett Packard Enterprise Development LP
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
import os
import threading
from time import sleep

from .batch import BatchManager
from .liveness.timestamp import Timestamp

from .cfs.options import options


DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = logging.getLogger(__name__)


def monotonic_liveliness_heartbeat():
    """
    Periodically add a timestamp to disk; this allows for reporting of basic
    health at a minimum rate. This prevents the pod being marked as dead if
    a period of no events have been monitored from k8s for an extended
    period of time.
    """
    while True:
        Timestamp()
        sleep(10)


def setup_logging():
    log_format = "%(asctime)-15s - %(levelname)-7s - %(name)s - %(message)s"
    requested_log_level = os.environ.get('CFS_LOG_LEVEL', DEFAULT_LOG_LEVEL)
    log_level = logging.getLevelName(requested_log_level)
    logging.basicConfig(level=log_level, format=log_format)


def main():
    # Create a liveness thread to indicate overall health of the pod
    heartbeat = threading.Thread(target=monotonic_liveliness_heartbeat, args=())
    heartbeat.start()

    manager = BatchManager()
    while True:
        try:
            sleep(options.batcher_check_interval)
            options.update()
            manager.check_status()
            manager.update_batches()
            manager.send_batches()
        except Exception as e:
            LOGGER.error('Unexpected error occurred: {}'.format(e))
            sleep(5)  # Arbitrary sleep to prevent recurring errors from hammering other services.


if __name__ == '__main__':
    setup_logging()
    main()
