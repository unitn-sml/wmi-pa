from antlr4 import *
from pysmt.shortcuts import *
import io

from .antlr.minizincLexer import minizincLexer
from .antlr.minizincParser import minizincParser
from .visitor import Visitor
from .minizincErrorListener import MinizincErrorListener

class MinizincParser():

    @staticmethod
    def parse(path, mode, domA=None, domX=None):
        if domA is None:
            domA = []
        if domX is None:
            domX = []
        
        # init lexer and parser
        mzn_file = FileStream(path)
        lexer = minizincLexer(mzn_file)
        stream = CommonTokenStream(lexer)
        parser = minizincParser(stream)
        
        # add custom error listener
        parser.removeErrorListeners()
        errorListener = MinizincErrorListener()
        parser.addErrorListener(errorListener)
        
        # compute parsing
        tree = parser.minizinc()
        
        # visit the tree
        visitor = Visitor(mode, domA, domX)
        return visitor.visit(tree)
        

    @staticmethod
    def parseAll(path):
        return MinizincParser.parse(path, Visitor.MODEL_QUERY)
        
        
    @staticmethod
    def parseModel(path):
        return MinizincParser.parse(path, Visitor.MODEL)
        
        
    @staticmethod
    def parseQuery(path, domA, domX):
        return MinizincParser.parse(path, Visitor.QUERY, domA, domX)
