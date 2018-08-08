"""This module implements the exceptions used throughout the code.

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

class WMIException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)

class WMIParsingError(WMIException):

    def __init__(self, message, expression=None):
        super(WMIParsingError,self).__init__(message)
        self.expression = expression

class WMIRuntimeException(WMIException):

    def __init__(self, message):
        super(WMIRuntimeException,self).__init__(message)


class WMITimeoutException(WMIException):
    def __init__(self):
        msg = "Timeout occurred"
        super(WMITimeoutException, self).__init__(msg)
