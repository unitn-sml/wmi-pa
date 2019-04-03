from antlr4 import *
from pysmt.shortcuts import *
import io

from .antlr.smtlibLexer import smtlibLexer
from .antlr.smtlibParser import smtlibParser
from .visitor import Visitor
from .smtlibErrorListener import SmtlibErrorListener

class SmtlibParser():

    @staticmethod
    def parse(path, mode, domA=None, domX=None):
        if domA is None:
            domA = []
        if domX is None:
            domX = []
    
        # init lexer and parser
        smt_file = FileStream(path)
        lexer = smtlibLexer(smt_file)
        stream = CommonTokenStream(lexer)
        parser = smtlibParser(stream)
        
        # add custom error listener
        parser.removeErrorListeners()
        errorListener = SmtlibErrorListener()
        parser.addErrorListener(errorListener)
        
        # compute parsing
        tree = parser.start()
        
        # visit the tree
        visitor = Visitor(mode, domA, domX)
        return visitor.visit(tree)
        

    @staticmethod
    def parseAll(path):
        return SmtlibParser.parse(path, Visitor.MODEL_QUERY)
        
        
    @staticmethod
    def parseModel(path):
        return SmtlibParser.parse(path, Visitor.MODEL)
        
        
    @staticmethod
    def parseQuery(path, domA, domX):
        return SmtlibParser.parse(path, Visitor.QUERY, domA, domX)
