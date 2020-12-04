# © Copyright 2020 Hewlett Packard Enterprise Development LP

import logging
import os
from time import sleep

from .batch import BatchManager
from .liveness.timestamp import Timestamp

from .cfs.options import options


DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = logging.getLogger(__name__)


def setup_logging():
    log_format = "%(asctime)-15s - %(levelname)-7s - %(name)s - %(message)s"
    requested_log_level = os.environ.get('CFS_LOG_LEVEL', DEFAULT_LOG_LEVEL)
    log_level = logging.getLevelName(requested_log_level)
    logging.basicConfig(level=log_level, format=log_format)


def main():
    Timestamp()
    manager = BatchManager()
    while True:
        Timestamp()
        sleep(options.batcher_check_interval)
        options.update()
        manager.check_status()
        manager.update_batches()
        manager.send_batches()


if __name__ == '__main__':
    setup_logging()
    main()
