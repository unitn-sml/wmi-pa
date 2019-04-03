import sys
from antlr4 import *
from antlr4.error.ErrorListener import *

from .antlr.minizincParser import minizincParser
from .antlr.minizincVisitor import minizincVisitor
 
class MinizincErrorListener(ErrorListener):

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise Exception('Syntax error at line '+str(line)+', column '+str(column)+': '+msg)
