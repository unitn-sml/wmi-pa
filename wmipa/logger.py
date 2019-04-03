
__version__ = '0.999'
__author__ = 'Paolo Morettin'


import logging
from sys import stdout

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create handler
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter
handler.setFormatter(formatter)

# add handler
logger.addHandler(handler)   
