""" Implements logging functionalities for ICHOR to time how long jobs took, as well as to log important information a user should know (e.g. integration errors
for points)."""

import logging

from ichor.log.concurrent_log_handler import ConcurrentRotatingFileHandler

LOG_LEVEL = logging.DEBUG


def setup_logger(
    name,
    log_file,
    level=LOG_LEVEL,
    formatter=logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%d-%m-%Y %H:%M:%S"
    ),
):
    handler = ConcurrentRotatingFileHandler(
        log_file
    )  # <= Has broken ICHOR before when submitted, use with caution
    # handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logger("ICHOR", "ichor.log")
timing_logger = setup_logger("TIMING", "ichor.timing")


def log_time(*args):
    timing_logger.info(" | ".join(map(str, args)))
