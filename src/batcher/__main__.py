#
# MIT License
#
# (C) Copyright 2020-2026 Hewlett Packard Enterprise Development LP
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
import os
import threading
import time

from csm_utils.logging import exc_type_msg
from csm_utils.wait_interval import IntervalTimer, get_max_sleep_seconds

from .batch import BatchManager
from .cfs.options import options
from .liveness.timestamp import Timestamp


DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = logging.getLogger(__name__)
MAIN_THREAD = threading.current_thread()


def monotonic_liveliness_heartbeat():
    """
    Periodically add a timestamp to disk; this allows for reporting of basic
    health at a minimum rate. This prevents the pod being marked as dead if
    a period of no events have been monitored from k8s for an extended
    period of time.
    """
    while True:
        if not MAIN_THREAD.is_alive():
            # All hope abandon ye who enter here
            return
        Timestamp()
        time.sleep(10)


def setup_logging():
    log_format = "%(asctime)-15s - %(process)d - %(thread)d - %(levelname)-7s - %(name)s - %(message)s"
    requested_log_level = os.environ.get("STARTING_CFS_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    log_level = logging.getLevelName(requested_log_level)
    logging.basicConfig(level=log_level, format=log_format)


def _update_options_and_log_level() -> None:
    """
    Gets the latest CFS options values, then updates the current logging level
    based on the value in the options database
    """
    orig_check_interval = options.batcher_check_interval
    try:
        options.update()
    except Exception as e:
        LOGGER.error("Error getting latest CFS option values: %s", exc_type_msg(e))
        return
    if (new_check_interval := options.batcher_check_interval) != orig_check_interval:
        LOGGER.info(
            "Batcher check interval updated from '%d' to '%d'",
            orig_check_interval,
            new_check_interval
        )
    try:
        if not options.logging_level:
            return
        new_level = logging.getLevelName(options.logging_level.upper())
        current_level = LOGGER.getEffectiveLevel()
        if current_level != new_level:
            LOGGER.log(
                current_level,
                "Changing logging level from {} to {}".format(
                    logging.getLevelName(current_level), logging.getLevelName(new_level)
                ),
            )
            logger = logging.getLogger()
            logger.setLevel(new_level)
            LOGGER.log(
                new_level,
                "Logging level changed from {} to {}".format(
                    logging.getLevelName(current_level), logging.getLevelName(new_level)
                ),
            )
    except Exception as e:
        LOGGER.error("Error updating logging level: %s", exc_type_msg(e))


def _update_options_and_log_level_and_return_check_interval() -> int:
    """
    For use with the IntervalTimer class. This will be called periodically
    during the sleep interval between batches. It calls the
    _update_options_and_log_level() function, then returns the current
    batcher_check_interval value. In this way, the sleep interval can be
    cut short if the batcher_check_interval option is reduced.
    """
    _update_options_and_log_level()
    return options.batcher_check_interval


def main():
    # Create a liveness thread to indicate overall health of the pod
    heartbeat = threading.Thread(target=monotonic_liveliness_heartbeat, args=())
    heartbeat.start()
    max_sleep_seconds = get_max_sleep_seconds(max_sleep_seconds_env_var_name="MAX_SLEEP_SECONDS")
    interval_timer = IntervalTimer(
        get_interval_duration=_update_options_and_log_level_and_return_check_interval,
        max_sleep_seconds=max_sleep_seconds,
    )
    manager = BatchManager()
    while True:
        try:
            interval_timer.wait_for_interval()
            LOGGER.debug("Checking status of batches")
            manager.check_status()
            if not options.batcher_disable:
                manager.update_batches()
                manager.send_batches()
        except Exception as e:
            LOGGER.error("Unexpected error occurred: %s", exc_type_msg(e))
            time.sleep(5)  # Sleep to prevent recurring errors from hammering other services.


if __name__ == "__main__":
    setup_logging()
    main()
