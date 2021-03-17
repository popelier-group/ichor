import logging

from ichor.logging.concurrent_log_handler import ConcurrentRotatingFileHandler


def setup_logger(
    name,
    log_file,
    level=logging.INFO,
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
