
__version__ = '0.999'
__author__ = 'Paolo Morettin'


import logging
from sys import stdout

class Loggable:
    # the following two methods were overwritten to allow the serialization
    # of the class instances (logger contains unserializable data structures).
    # serialization is necessary for multiprocessing.
    
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d
    def __setstate__(self, d):
        self.__dict__.update(d)

    def init_sublogger(self, name):
        self.logger = get_sublogger(name)


DEF_PATH = "log_wmi.log"
ROOT_NAME = "root"

def init_root_logger(path=None, verbose=False):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    logger = logging.getLogger(ROOT_NAME)
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler(stdout)
    sh.setLevel(logging.DEBUG if verbose else logging.INFO)
    sh.setFormatter(formatter)

    path = path or DEF_PATH
    fh = logging.FileHandler(path, "w+")    
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)

def get_sublogger(name):
    return logging.getLogger("{}.{}".format(ROOT_NAME, name))
    
