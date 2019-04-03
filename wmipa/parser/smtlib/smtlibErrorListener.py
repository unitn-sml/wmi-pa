import sys
from antlr4 import *
from antlr4.error.ErrorListener import *

from .antlr.smtlibParser import smtlibParser
from .antlr.smtlibVisitor import smtlibVisitor
 
class SmtlibErrorListener(ErrorListener):

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception('Syntax error at line '+str(line)+', column '+str(column)+': '+msg)
