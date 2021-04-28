# © Copyright 2020-2021 Hewlett Packard Enterprise Development LP

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
        sleep(options.batcher_check_interval)
        options.update()
        manager.check_status()
        manager.update_batches()
        manager.send_batches()


if __name__ == '__main__':
    setup_logging()
    main()
