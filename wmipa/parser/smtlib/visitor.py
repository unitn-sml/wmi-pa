import sys
import warnings
from antlr4 import *
from .antlr.smtlibParser import smtlibParser
from .antlr.smtlibVisitor import smtlibVisitor
from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa.wmiexception import WMIParsingFileException, WMIRuntimeException

# This class defines a complete generic visitor for a parse tree produced by smtlibParser.
class Visitor(ParseTreeVisitor):

    MODEL = "model"
    QUERY = "query"
    MODEL_QUERY = "model_query"
    MODES = [MODEL, QUERY, MODEL_QUERY]

    def __init__(self, mode, domA=None, domX=None):
        if mode not in Visitor.MODES:
            err = "{}, use one: {}".format(mode, ", ".join(Visitor.MODES))
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)
        if domA is None:
            domA = []
        if domX is None:
            domX = []
        self.variables = {}
        self.boolean_variables = domA
        self.real_variables = domX
        self.support = []
        self.weight = None
        self.queries = []
        self.model = "model" in mode
        self.query = "query" in mode
        
        for b in domA:
            self.variables[b.symbol_name()] = {"value":b, "type":'bool', "var":True, "obj":"variable"}
        for r in domX:
            self.variables[r.symbol_name()] = {"value":r, "type":'float', "var":True, "obj":"variable"}
            
            
    def _cast(self, e1, e2):
        if e1['type'] != e2['type']:
            if ((e1['type'] == "float" and e2['type'] == "int") or
               (e1['type'] == "int" and e2['type'] == "float")):
                e1['value'] = ToReal(e1['value'])
                e2['value'] = ToReal(e2['value'])
                e1['type'] = "float"
                e2['type'] = "float"
                return True
            else:
                return False
        return True
        
        
    def _err(self, s, ctx):
        token = ctx.start
        line = token.line
        return '{} at line {}'.format(s, line)
        
        
    def _ctx_text(self, ctx):
        children = ctx.getChildCount()
        if children == 0:
            return ctx.getText()
        
        out = []
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            out.append(self._ctx_text(child).strip())
        return ' '.join(out)


    # Visit a parse tree produced by smtlibParser#start.
    def visitStart(self, ctx:smtlibParser.StartContext):
        self.visitChildren(ctx)
        self.support = And(self.support)
        self.support = simplify(self.support)
        
        if self.model:
            if self.weight == None:
                self.weight = Real(1)
            self.weight = simplify(self.weight)
            ret = [self.support, self.weight, set(self.boolean_variables), set(self.real_variables)]
            if self.query:
                ret.append(self.queries)
            return ret
        else:
            return self.queries


    # Visit a parse tree produced by smtlibParser#response.
    def visitResponse(self, ctx:smtlibParser.ResponseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#generalReservedWord.
    def visitGeneralReservedWord(self, ctx:smtlibParser.GeneralReservedWordContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#simpleSymbol.
    def visitSimpleSymbol(self, ctx:smtlibParser.SimpleSymbolContext):
        if ctx.predefSymbol():
            return self.visitPredefSymbol(ctx.predefSymbol())
        elif ctx.UndefinedSymbol():
            return {"value":ctx.getText(), "obj":"symbol"}


    # Visit a parse tree produced by smtlibParser#quotedSymbol.
    def visitQuotedSymbol(self, ctx:smtlibParser.QuotedSymbolContext):
        return ctx.getText()


    # Visit a parse tree produced by smtlibParser#predefSymbol.
    def visitPredefSymbol(self, ctx:smtlibParser.PredefSymbolContext):
        t = ctx.getText()
        if t == 'true':
            return {"value":Bool(True), "type":"bool", "var":False, "obj":"expr"}
        elif t == 'false':
            return {"value":Bool(False), "type":"bool", "var":False, "obj":"expr"}
        elif t == 'not':
            return {"value":"not", "obj":"symbol"}
        elif t == 'Bool':
            return {"value":"Bool", "obj":"symbol"}
        else:
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(t, ctx))


    # Visit a parse tree produced by smtlibParser#predefKeyword.
    def visitPredefKeyword(self, ctx:smtlibParser.PredefKeywordContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#symbol.
    def visitSymbol(self, ctx:smtlibParser.SymbolContext):
        if ctx.simpleSymbol():
            return self.visitSimpleSymbol(ctx.simpleSymbol())
        elif ctx.quotedSymbol():
            return self.visitQuotedSymbol(ctx.quotedSymbol())


    # Visit a parse tree produced by smtlibParser#numeral.
    def visitNumeral(self, ctx:smtlibParser.NumeralContext):
        value = Int(int(ctx.getText()))
        return {"value":value, "type":"int", "var":False, "obj":"expr"}


    # Visit a parse tree produced by smtlibParser#decimal.
    def visitDecimal(self, ctx:smtlibParser.DecimalContext):
        value = Real(float(ctx.getText()))
        return {"value":value, "type":"float", "var":False, "obj":"expr"}


    # Visit a parse tree produced by smtlibParser#hexadecimal.
    def visitHexadecimal(self, ctx:smtlibParser.HexadecimalContext):
        value = Int(int(ctx.getText()[2:], 16))
        return {"value":value, "type":"int", "var":False, "obj":"expr"}


    # Visit a parse tree produced by smtlibParser#binary.
    def visitBinary(self, ctx:smtlibParser.BinaryContext):
        value = Int(int(ctx.getText()[2:], 2))
        return {"value":value, "type":"int", "var":False, "obj":"expr"}


    # Visit a parse tree produced by smtlibParser#string.
    def visitString(self, ctx:smtlibParser.StringContext):
        raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))


    # Visit a parse tree produced by smtlibParser#keyword.
    def visitKeyword(self, ctx:smtlibParser.KeywordContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#spec_constant.
    def visitSpec_constant(self, ctx:smtlibParser.Spec_constantContext):
        if ctx.numeral():
            return self.visitNumeral(ctx.numeral())
        elif ctx.decimal():
            return self.visitDecimal(ctx.decimal())
        elif ctx.hexadecimal():
            return self.visitHexadecimal(ctx.hexadecimal())
        elif ctx.binary():
            return self.visitBinary(ctx.binary())
        elif ctx.string():
             raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))


    # Visit a parse tree produced by smtlibParser#s_expr.
    def visitS_expr(self, ctx:smtlibParser.S_exprContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#index.
    def visitIndex(self, ctx:smtlibParser.IndexContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#identifier.
    def visitIdentifier(self, ctx:smtlibParser.IdentifierContext):
        if ctx.ParOpen():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('_', ctx))
        else:
            return self.visitSymbol(ctx.symbol())


    # Visit a parse tree produced by smtlibParser#attribute_value.
    def visitAttribute_value(self, ctx:smtlibParser.Attribute_valueContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#attribute.
    def visitAttribute(self, ctx:smtlibParser.AttributeContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#sort.
    def visitSort(self, ctx:smtlibParser.SortContext):
        if ctx.ParOpen():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, ctx.getText())
        else:
            return self.visitIdentifier(ctx.identifier())


    # Visit a parse tree produced by smtlibParser#qual_identifer.
    def visitQual_identifer(self, ctx:smtlibParser.Qual_identiferContext):
        if ctx.ParOpen():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('as', ctx))
        else:
            return self.visitIdentifier(ctx.identifier())


    # Visit a parse tree produced by smtlibParser#var_binding.
    def visitVar_binding(self, ctx:smtlibParser.Var_bindingContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#sorted_var.
    def visitSorted_var(self, ctx:smtlibParser.Sorted_varContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#pattern.
    def visitPattern(self, ctx:smtlibParser.PatternContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#match_case.
    def visitMatch_case(self, ctx:smtlibParser.Match_caseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#term.
    def visitTerm(self, ctx:smtlibParser.TermContext):
        if ctx.ParOpen():
            if ctx.qual_identifer():
                qual_id = self.visitQual_identifer(ctx.qual_identifer())
                op = qual_id['value']
                same_type_op = ['=', '>', '>=', '<', '<=', '=>', '+', '-', '*', '/', 'and', 'or']
                
                terms = []
                var = False
                last = None
                type_ = None
                
                for t in ctx.term():
                    term = self.visitTerm(t)
                    if "obj" in term and (term['obj'] == "variable" or term['obj'] == "expr"):
                        if not last:
                            last = term
                        else:
                            if op in same_type_op:
                                if not self._cast(last, term):
                                    err = 'Expected same type, found {} and {}: {}'.format(last['type'], term['type'], self._ctx_text(ctx))
                                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                                last = term
                        if term['var']:
                            var = True
                        terms.append(term)
                    else:
                        err = self._ctx_text(t)
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                        
                terms_value = [t['value'] for t in terms]
                
                if op == '=':
                    if len(terms)==2:
                        value = EqualsOrIff(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '>':
                    if len(terms)==2:
                        value = GT(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '>=':
                    if len(terms)==2:
                        value = GE(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '<':
                    if len(terms)==2:
                        value = LT(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '<=':
                    if len(terms)==2:
                        value = LE(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '=>':
                    if len(terms)==2:
                        value = Implies(terms_value[0], terms_value[1])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '+':
                    value = Plus(terms_value)
                    type_ = terms[0]['type']
                elif op == '-':
                    if len(terms)==2:
                        value = Minus(terms_value[0], terms_value[1])
                        type_ = terms[0]['type']
                    elif len(terms)==1:
                        if terms[0]['type'] == 'int':
                            value = Times(terms_value[0], Int(-1))
                            type_ = 'int'
                        elif terms[0]['type'] == 'float':
                            value = Times(terms_value[0], Real(-1))
                            type_ = 'float'
                        else:
                            err = 'Expected int or float, found {}: \'{}\''.format(terms[0]['type'], self._ctx_text(ctx.term()[0]))
                            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                    else:
                        err = '{} operator takes one or two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == '*':
                    value = Times(terms_value)
                    type_ = terms[0]['type']
                elif op == '/':
                    if len(terms)==2:
                        value = Div(ToReal(terms_value[0]), ToReal(terms_value[1]))
                        type_ = 'float'
                    else:
                        err = '{} operator takes two parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == 'and':
                    value = And(terms_value)
                    type_ = 'bool'
                elif op == 'or':
                    value = Or(terms_value)
                    type_ = 'bool'
                elif op == 'not':
                    if len(terms)==1:
                        value = Not(terms_value[0])
                        type_ = 'bool'
                    else:
                        err = '{} operator takes one parameter but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                elif op == 'ite':
                    if len(terms)==3:
                        cond = terms[0]
                        then = terms[1]
                        else_ = terms[2]
                        
                        if cond['type'] != "bool":
                            err = 'Expected bool, found {}: \'{}\''.format(cond['type'], self._ctx_text(ctx.term()[0]))
                            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                        
                        # check that then and else parts are of the same type
                        if not self._cast(then, else_):
                            err = 'THEN and ELSE parts must be of the same type: {}'.format(self._ctx_text(ctx))
                            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                            
                        value = Ite(cond['value'], then['value'], else_['value'])
                        type_ = then['type']
                    else:
                        err = '{} operator takes three parameters but {} were given'.format(op, len(terms))
                        raise WMIParsingFileException(WMIParsingFileException.SYNTAX_ERROR, self._err(err, ctx))
                else:
                    raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(op, ctx))
                
                return {'value': value, 'type':type_, 'var':var, 'obj':'expr'}
            elif ctx.GRW_Let():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('let', ctx))
            elif ctx.GRW_Forall():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('forall', ctx))
            elif ctx.GRW_Exists():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('exists', ctx))
            elif ctx.GRW_Match():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('match', ctx))
            elif ctx.GRW_Exclamation():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('!', ctx))
        elif ctx.spec_constant():
            return self.visitSpec_constant(ctx.spec_constant())
        elif ctx.qual_identifer():
            symbol = self.visitQual_identifer(ctx.qual_identifer())
            if symbol['obj'] == 'symbol' and symbol['value'] in self.variables:
                return self.variables[symbol['value']]
            else:
                return symbol
            

    # Visit a parse tree produced by smtlibParser#sort_symbol_decl.
    def visitSort_symbol_decl(self, ctx:smtlibParser.Sort_symbol_declContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#meta_spec_constant.
    def visitMeta_spec_constant(self, ctx:smtlibParser.Meta_spec_constantContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#fun_symbol_decl.
    def visitFun_symbol_decl(self, ctx:smtlibParser.Fun_symbol_declContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#par_fun_symbol_decl.
    def visitPar_fun_symbol_decl(self, ctx:smtlibParser.Par_fun_symbol_declContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#theory_attribute.
    def visitTheory_attribute(self, ctx:smtlibParser.Theory_attributeContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#theory_decl.
    def visitTheory_decl(self, ctx:smtlibParser.Theory_declContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#logic_attribue.
    def visitLogic_attribue(self, ctx:smtlibParser.Logic_attribueContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#logic.
    def visitLogic(self, ctx:smtlibParser.LogicContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#sort_dec.
    def visitSort_dec(self, ctx:smtlibParser.Sort_decContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#selector_dec.
    def visitSelector_dec(self, ctx:smtlibParser.Selector_decContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#constructor_dec.
    def visitConstructor_dec(self, ctx:smtlibParser.Constructor_decContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#datatype_dec.
    def visitDatatype_dec(self, ctx:smtlibParser.Datatype_decContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#function_dec.
    def visitFunction_dec(self, ctx:smtlibParser.Function_decContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#function_def.
    def visitFunction_def(self, ctx:smtlibParser.Function_defContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#prop_literal.
    def visitProp_literal(self, ctx:smtlibParser.Prop_literalContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#script.
    def visitScript(self, ctx:smtlibParser.ScriptContext):
        for command in ctx.command():
            self.visitCommand(command)


    # Visit a parse tree produced by smtlibParser#cmd_assert.
    def visitCmd_assert(self, ctx:smtlibParser.Cmd_assertContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_checkSat.
    def visitCmd_checkSat(self, ctx:smtlibParser.Cmd_checkSatContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_checkSatAssuming.
    def visitCmd_checkSatAssuming(self, ctx:smtlibParser.Cmd_checkSatAssumingContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_declareConst.
    def visitCmd_declareConst(self, ctx:smtlibParser.Cmd_declareConstContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_declareDatatype.
    def visitCmd_declareDatatype(self, ctx:smtlibParser.Cmd_declareDatatypeContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_declareDatatypes.
    def visitCmd_declareDatatypes(self, ctx:smtlibParser.Cmd_declareDatatypesContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_declareFun.
    def visitCmd_declareFun(self, ctx:smtlibParser.Cmd_declareFunContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_declareSort.
    def visitCmd_declareSort(self, ctx:smtlibParser.Cmd_declareSortContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_defineFun.
    def visitCmd_defineFun(self, ctx:smtlibParser.Cmd_defineFunContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_defineFunRec.
    def visitCmd_defineFunRec(self, ctx:smtlibParser.Cmd_defineFunRecContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_defineFunsRec.
    def visitCmd_defineFunsRec(self, ctx:smtlibParser.Cmd_defineFunsRecContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_defineSort.
    def visitCmd_defineSort(self, ctx:smtlibParser.Cmd_defineSortContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_echo.
    def visitCmd_echo(self, ctx:smtlibParser.Cmd_echoContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_exit.
    def visitCmd_exit(self, ctx:smtlibParser.Cmd_exitContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getAssertions.
    def visitCmd_getAssertions(self, ctx:smtlibParser.Cmd_getAssertionsContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getAssignment.
    def visitCmd_getAssignment(self, ctx:smtlibParser.Cmd_getAssignmentContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getInfo.
    def visitCmd_getInfo(self, ctx:smtlibParser.Cmd_getInfoContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getModel.
    def visitCmd_getModel(self, ctx:smtlibParser.Cmd_getModelContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getOption.
    def visitCmd_getOption(self, ctx:smtlibParser.Cmd_getOptionContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getProof.
    def visitCmd_getProof(self, ctx:smtlibParser.Cmd_getProofContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getUnsatAssumptions.
    def visitCmd_getUnsatAssumptions(self, ctx:smtlibParser.Cmd_getUnsatAssumptionsContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getUnsatCore.
    def visitCmd_getUnsatCore(self, ctx:smtlibParser.Cmd_getUnsatCoreContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_getValue.
    def visitCmd_getValue(self, ctx:smtlibParser.Cmd_getValueContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_pop.
    def visitCmd_pop(self, ctx:smtlibParser.Cmd_popContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_push.
    def visitCmd_push(self, ctx:smtlibParser.Cmd_pushContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_reset.
    def visitCmd_reset(self, ctx:smtlibParser.Cmd_resetContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_resetAssertions.
    def visitCmd_resetAssertions(self, ctx:smtlibParser.Cmd_resetAssertionsContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_setInfo.
    def visitCmd_setInfo(self, ctx:smtlibParser.Cmd_setInfoContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_setLogic.
    def visitCmd_setLogic(self, ctx:smtlibParser.Cmd_setLogicContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_setOption.
    def visitCmd_setOption(self, ctx:smtlibParser.Cmd_setOptionContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#cmd_weight.
    def visitCmd_weight(self, ctx:smtlibParser.Cmd_weightContext):
        pass # function never called
        
        
    # Visit a parse tree produced by smtlibParser#cmd_query.
    def visitCmd_query(self, ctx:smtlibParser.Cmd_queryContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#command.
    def visitCommand(self, ctx:smtlibParser.CommandContext):
        if not self.model and not ctx.cmd_query():
            warnings.warn("in query file every command except 'query' will be ignored", RuntimeWarning)
            return
        
        if ctx.cmd_assert():
            term = self.visitTerm(ctx.term()[0])
            if term['type'] != "bool":
                err = 'Expected bool, found {}: \'{}\''.format(term['type'], self._ctx_text(ctx.term()[0]))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            self.support.append( term['value'] )
        elif ctx.cmd_checkSat():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('check-sat', ctx))
        elif ctx.cmd_checkSatAssuming():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('check-sat-assuming', ctx))
        elif ctx.cmd_declareConst():
            symbol = self.visitSymbol(ctx.symbol()[0])
            id_ = symbol['value']
            if id_ in self.variables:
                raise WMIParsingFileException(WMIParsingFileException.DOUBLE_DECLARATION, self._err(id_, ctx))
                
            type_ = self.visitSort(ctx.sort()[0])
            if type_['value'] == 'Int':
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('int', ctx))
            elif type_['value'] == 'Real':
                variable = Symbol(id_, REAL)
                self.variables[id_] = {"value":variable, "type":'float', "var":True, "obj":"variable"}
                self.real_variables.append(variable)
            elif type_['value'] == 'Bool':
                variable = Symbol(id_, BOOL)
                self.variables[id_] = {"value":variable, "type":'bool', "var":True, "obj":"variable"}
                self.boolean_variables.append(variable)
            else:
                err = self._ctx_text(ctx)
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.cmd_declareDatatype():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('declare-datatpye', ctx))
        elif ctx.cmd_declareDatatypes():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('declare-datatpyes', ctx))
        elif ctx.cmd_declareFun():
            symbol = self.visitSymbol(ctx.symbol()[0])
            id_ = symbol['value']
            if id_ in self.variables:
                raise WMIParsingFileException(WMIParsingFileException.DOUBLE_DECLARATION, self._err(id_, ctx))
                
            sort = ctx.sort()
            if len(sort)>1:
                err = ", ".join([self._ctx_text(s) for s in ctx.sort()[:-1]])
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(err, ctx))
            type_ = self.visitSort(sort[-1])
            if type_['value'] == 'Int':
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('int', ctx))
            elif type_['value'] == 'Real':
                variable = Symbol(id_, REAL)
                self.variables[id_] = {"value":variable, "type":'float', "var":True, "obj":"variable"}
                self.real_variables.append(variable)
            elif type_['value'] == 'Bool':
                variable = Symbol(id_, BOOL)
                self.variables[id_] = {"value":variable, "type":'bool', "var":True, "obj":"variable"}
                self.boolean_variables.append(variable)
            else:
                err = self._ctx_text(ctx)
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.cmd_declareSort():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('declare-sort', ctx))
        elif ctx.cmd_defineFun():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('define-fun', ctx))
        elif ctx.cmd_defineFunRec():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('define-fun-rec', ctx))
        elif ctx.cmd_defineFunsRec():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('define-funs-rec', ctx))
        elif ctx.cmd_defineSort():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('define-sort', ctx))
        elif ctx.cmd_echo():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('echo', ctx))
        elif ctx.cmd_exit():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('exit', ctx))
        elif ctx.cmd_getAssertions():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-assertions', ctx))
        elif ctx.cmd_getAssignment():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-assignment', ctx))
        elif ctx.cmd_getInfo():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-info', ctx))
        elif ctx.cmd_getModel():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-model', ctx))
        elif ctx.cmd_getOption():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-option', ctx))
        elif ctx.cmd_getProof():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-proof', ctx))
        elif ctx.cmd_getUnsatAssumptions():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-unsat-assumptions', ctx))
        elif ctx.cmd_getUnsatCore():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-unsat-core', ctx))
        elif ctx.cmd_getValue():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('get-value', ctx))
        elif ctx.cmd_pop():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('pop', ctx))
        elif ctx.cmd_push():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('push', ctx))
        elif ctx.cmd_reset():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('reset', ctx))
        elif ctx.cmd_resetAssertions():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('reset-assertions', ctx))
        elif ctx.cmd_setInfo():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('set-info', ctx))
        elif ctx.cmd_setLogic():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('set-logic', ctx))
        elif ctx.cmd_setOption():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('set-option', ctx))
        elif ctx.cmd_weight():
            term = self.visitTerm(ctx.term()[0])
            
            if self.weight != None:
                raise WMIParsingFileException(WMIParsingFileException.DOUBLE_WEIGHT_DECLARATION, self._err('', ctx))
                
            if term['type'] != 'float':
                # cast weight to float
                if term['type'] == 'int':
                    term['value'] = ToReal(term['value'])
                else:
                    err = 'Expected real or int, found {}: \'{}\''.format(term['type'], self._ctx_text(ctx.expr()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                    
            self.weight = term['value']
        elif ctx.cmd_query():
            if not self.query:
                raise WMIParsingFileException(WMIParsingFileException.QUERY_IN_MODEL, self._err('', ctx))
                
            term = self.visitTerm(ctx.term()[0])
            
            if term['type'] != 'bool':
                # cast weight to float
                if term['type'] == 'int':
                    term['value'] = ToReal(term['value'])
                else:
                    err = 'Expected bool, found {}: \'{}\''.format(term['type'], self._ctx_text(ctx.expr()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                    
            self.queries.append(term['value'])
            

    # Visit a parse tree produced by smtlibParser#b_value.
    def visitB_value(self, ctx:smtlibParser.B_valueContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#option.
    def visitOption(self, ctx:smtlibParser.OptionContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#info_flag.
    def visitInfo_flag(self, ctx:smtlibParser.Info_flagContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#error_behaviour.
    def visitError_behaviour(self, ctx:smtlibParser.Error_behaviourContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#reason_unknown.
    def visitReason_unknown(self, ctx:smtlibParser.Reason_unknownContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#model_response.
    def visitModel_response(self, ctx:smtlibParser.Model_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#info_response.
    def visitInfo_response(self, ctx:smtlibParser.Info_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#valuation_pair.
    def visitValuation_pair(self, ctx:smtlibParser.Valuation_pairContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#t_valuation_pair.
    def visitT_valuation_pair(self, ctx:smtlibParser.T_valuation_pairContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#check_sat_response.
    def visitCheck_sat_response(self, ctx:smtlibParser.Check_sat_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#echo_response.
    def visitEcho_response(self, ctx:smtlibParser.Echo_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_assertions_response.
    def visitGet_assertions_response(self, ctx:smtlibParser.Get_assertions_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_assignment_response.
    def visitGet_assignment_response(self, ctx:smtlibParser.Get_assignment_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_info_response.
    def visitGet_info_response(self, ctx:smtlibParser.Get_info_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_model_response.
    def visitGet_model_response(self, ctx:smtlibParser.Get_model_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_option_response.
    def visitGet_option_response(self, ctx:smtlibParser.Get_option_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_proof_response.
    def visitGet_proof_response(self, ctx:smtlibParser.Get_proof_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_unsat_assump_response.
    def visitGet_unsat_assump_response(self, ctx:smtlibParser.Get_unsat_assump_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_unsat_core_response.
    def visitGet_unsat_core_response(self, ctx:smtlibParser.Get_unsat_core_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#get_value_response.
    def visitGet_value_response(self, ctx:smtlibParser.Get_value_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#specific_success_response.
    def visitSpecific_success_response(self, ctx:smtlibParser.Specific_success_responseContext):
        pass # function never called


    # Visit a parse tree produced by smtlibParser#general_response.
    def visitGeneral_response(self, ctx:smtlibParser.General_responseContext):
        pass # function never called
