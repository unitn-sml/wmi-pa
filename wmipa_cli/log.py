import logging

logger = logging.getLogger(__package__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)