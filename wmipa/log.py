
__version__ = '0.999'
__author__ = 'Paolo Morettin'


import logging

# create logger
logger = logging.getLogger(__package__)
logger.addHandler(logging.NullHandler())
