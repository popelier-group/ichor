""" Implements logging functionalities for ICHOR to time how long jobs took,
as well as to log important information a user should know (e.g. integration errors
for points)."""

import logging

from ichor.hpc.log.concurrent_log_handler import ConcurrentRotatingFileHandler


def setup_logger(
    name,
    log_file,
    level=logging.DEBUG,
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


logger = setup_logger("ichor_logger", "ichor.log")
timing_log = setup_logger("timing_logger", "ichor.timing")


def log_time(*args):
    global timing_log
    timing_log.info(" | ".join(map(str, args)))
