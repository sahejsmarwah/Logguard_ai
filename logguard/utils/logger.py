import logging
import sys

def setup_logger():
    logger = logging.getLogger("logguard")
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.handlers = []
    logger.addHandler(handler)

    return logger
