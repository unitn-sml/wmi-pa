import sys
import warnings
from antlr4 import *
from .antlr.minizincParser import minizincParser
from .antlr.minizincVisitor import minizincVisitor
from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL
from wmipa.wmiexception import WMIParsingFileException, WMIRuntimeException

# This class defines a complete listener for a parse tree produced by minizincParser.
class Visitor(minizincVisitor):

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
        

    # Visit a parse tree produced by minizincParser#minizinc.
    def visitMinizinc(self, ctx:minizincParser.MinizincContext):
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


    # Visit a parse tree produced by minizincParser#item.
    def visitItem(self, ctx:minizincParser.ItemContext):
        if not self.model and not ctx.query_item():
            warnings.warn("in query file every command except 'query' will be ignored", RuntimeWarning)
            return
        
        return self.visitChildren(ctx)
        

    # Visit a parse tree produced by minizincParser#ti_expr_and_id.
    def visitTi_expr_and_id(self, ctx:minizincParser.Ti_expr_and_idContext):
        type_ = self.visitTi_expr(ctx.ti_expr())
        id_ = self.visitIdent(ctx.ident())
        type_['id'] = id_
        type_['type'] = type_['value']
        return type_


    # Visit a parse tree produced by minizincParser#include_item.
    def visitInclude_item(self, ctx:minizincParser.Include_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('include', ctx))


    # Visit a parse tree produced by minizincParser#var_decl_item.
    def visitVar_decl_item(self, ctx:minizincParser.Var_decl_itemContext):
        # id (str): the name of the variable
        # var_type (str): the type of the variable (float, int, string or bool)
        # var (bool): if the variable is a decision variabile or a parameter
        decl = self.visitTi_expr_and_id(ctx.ti_expr_and_id())
        id_ = decl['id']
        annotations = self.visitAnnotations(ctx.annotations())
        expr = None
        
        # check if the variable is already declared
        if id_ in self.variables:
            raise WMIParsingFileException(WMIParsingFileException.DOUBLE_DECLARATION, self._err(id_, ctx))
            
        if ctx.expr() != None:
            expr = self.visitExpr(ctx.expr())
            
        if expr:
            # if the variable is initiated as parameter and the expression depends on a decision variable
            if (not decl['var'] and expr['var']):
                err = 'Expected decision variabile, found parameter: '+id_
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
        
            if (decl['type'] != expr['type']):
                # cast expression to float if it is int
                if decl['type'] == 'float' and expr['type'] == 'int':
                    expr['value'] = ToReal(expr['value'])
                else:
                    err = 'Expected {}, found {}: \'{}\''.format(decl['type'], expr['type'], self._ctx_text(ctx.expr()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                    
        if decl['var']:
            if decl['type'] == 'float':
                variable = Symbol(id_, REAL)
                self.variables[id_] = {"value":variable, "type":'float', "var":True, "obj":"variable"}
                self.real_variables.append(variable)
            elif decl['type'] == 'bool':
                variable = Symbol(id_, BOOL)
                self.variables[id_] = {"value":variable, "type":'bool', "var":True, "obj":"variable"}
                self.boolean_variables.append(variable)
            elif decl['type'] == 'int':
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('int', ctx))
            elif decl['type'] == 'string':
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))
            
            # add range of variable to support
            if decl['obj'] == "range_type":
                min_ = decl['min']
                max_ = decl['max']
                self.support.extend( [GE(variable, min_), LE(variable, max_)] )
                
            # add value of variable to support
            if expr:
                self.support.append( EqualsOrIff(variable, expr['value']) )
            
        else:
            if decl['type'] == 'string':
                raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))
            else:
                value = None
                if expr:
                    value = simplify(expr['value'])
                self.variables[id_] = {"value":value, "type":decl['type'], "var":False, "obj":"variable"}


    # Visit a parse tree produced by minizincParser#enum_item.
    def visitEnum_item(self, ctx:minizincParser.Enum_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('enum', ctx))


    # Visit a parse tree produced by minizincParser#enum_cases.
    def visitEnum_cases(self, ctx:minizincParser.Enum_casesContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#assign_item.
    def visitAssign_item(self, ctx:minizincParser.Assign_itemContext):
        id_ = self.visitIdent(ctx.ident())
        expr = self.visitExpr(ctx.expr())
        
        if id_ not in self.variables:
            raise WMIParsingFileException(WMIParsingFileException.VARIABLE_NOT_DECLARED, self._err(id_, ctx))
        ident = self.variables[id_]
        
        if ident['value'] != None:
            raise WMIParsingFileException(WMIParsingFileException.DOUBLE_DECLARATION, self._err(id_, ctx))
        
        # if the variable is initiated as parameter and the expression depends on a decision variable
        if (not ident['var'] and expr['var']):
            err = 'Expected decision variabile, found parameter: '+id_
            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
    
        if (ident['type'] != expr['type']):
            # cast expression to float if it is int
            if ident['type'] == 'float' and expr['type'] == 'int':
                expr['value'] = ToReal(expr['value'])
            else:
                err = 'Expected {}, found {}: \'{}\''.format(ident['type'], expr['type'], self._ctx_text(ctx.expr()))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                
        expr['value'] = simplify(expr['value'])
                
        if ident['var']:
            self.support.append( EqualsOrIff(var, expr['value']) )
        else:
            ident['value'] = expr['value']
                

    # Visit a parse tree produced by minizincParser#constraint_item.
    def visitConstraint_item(self, ctx:minizincParser.Constraint_itemContext):
        expr = self.visitExpr(ctx.expr())
        if expr['type'] != "bool":
            err = 'Expected bool, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.expr()))
            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
        self.support.append( expr['value'] )


    # Visit a parse tree produced by minizincParser#solve_item.
    def visitSolve_item(self, ctx:minizincParser.Solve_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('solve', ctx))


    # Visit a parse tree produced by minizincParser#output_item.
    def visitOutput_item(self, ctx:minizincParser.Output_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('output', ctx))


    # Visit a parse tree produced by minizincParser#predicate_item.
    def visitPredicate_item(self, ctx:minizincParser.Predicate_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('predicate', ctx))


    # Visit a parse tree produced by minizincParser#test_item.
    def visitTest_item(self, ctx:minizincParser.Test_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('test', ctx))


    # Visit a parse tree produced by minizincParser#function_item.
    def visitFunction_item(self, ctx:minizincParser.Function_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('function', ctx))


    # Visit a parse tree produced by minizincParser#annotation_item.
    def visitAnnotation_item(self, ctx:minizincParser.Annotation_itemContext):
        raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('annotation', ctx))


    # Visit a parse tree produced by minizincParser#weight_item.
    def visitWeight_item(self, ctx:minizincParser.Weight_itemContext):
        expr = self.visitExpr(ctx.expr())
        if self.weight != None:
            raise WMIParsingFileException(WMIParsingFileException.DOUBLE_WEIGHT_DECLARATION, self._err('', ctx))
            
        if expr['type'] != 'float':
            # cast weight to float
            if expr['type'] == 'int':
                expr['value'] = ToReal(expr['value'])
            else:
                err = 'Expected real or int, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.expr()))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
        
        self.weight = expr['value']
        

    # Visit a parse tree produced by minizincParser#query_item.
    def visitQuery_item(self, ctx:minizincParser.Query_itemContext):
        if not self.query:
            raise WMIParsingFileException(WMIParsingFileException.QUERY_IN_MODEL, self._err('', ctx))
        
        expr = self.visitExpr(ctx.expr())
            
        if expr['type'] != 'bool':
            err = 'Expected bool, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.expr()))
            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
        
        self.queries.append(expr['value'])


    # Visit a parse tree produced by minizincParser#operation_item_tail.
    def visitOperation_item_tail(self, ctx:minizincParser.Operation_item_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#params.
    def visitParams(self, ctx:minizincParser.ParamsContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#ti_expr.
    def visitTi_expr(self, ctx:minizincParser.Ti_exprContext):
        return self.visitBase_ti_expr(ctx.base_ti_expr())


    # Visit a parse tree produced by minizincParser#base_ti_expr.
    def visitBase_ti_expr(self, ctx:minizincParser.Base_ti_exprContext):
        var = self.visitVar_par(ctx.var_par())
        type_ = self.visitBase_ti_expr_tail(ctx.base_ti_expr_tail())
        
        if type_['value'] == "string":
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))
        
        if type_['obj'] == "range_type":
            if not var:
                err = 'Only decision variable can be initialized with interval,'
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                
            min_ = type_['min']
            max_ = type_['max']
            type_['min'] = min_['value']
            type_['max'] = max_['value']
            
        type_['var'] = var
        return type_


    # Visit a parse tree produced by minizincParser#var_par.
    def visitVar_par(self, ctx:minizincParser.Var_parContext):
        if ctx.VAR():
            return True
        else:
            return False


    # Visit a parse tree produced by minizincParser#base_type.
    def visitBase_type(self, ctx:minizincParser.Base_typeContext):
        if ctx.BOOL():
            return {"value":"bool", "obj":"type"}
        elif ctx.INT():
            return {"value":"int", "obj":"type"}
        elif ctx.FLOAT():
            return {"value":"float", "obj":"type"}
        elif ctx.STRING():
            return {"value":"string", "obj":"type"}
        elif ctx.ident():
            return self.visitIdent(ctx.ident())


    # Visit a parse tree produced by minizincParser#base_ti_expr_tail.
    def visitBase_ti_expr_tail(self, ctx:minizincParser.Base_ti_expr_tailContext):
        err = self._ctx_text(ctx)
        
        if ctx.base_type():
            return self.visitBase_type(ctx.base_type())
        elif ctx.set_ti_expr_tail():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.ti_variable_expr_tail():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.array_ti_expr_tail():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.ANN():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.OPT():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.expr():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err(err, ctx))
        elif ctx.num_expr():
            min_ = self.visitNum_expr(ctx.num_expr()[0])
            max_ = self.visitNum_expr(ctx.num_expr()[1])
            if not self._cast(min_, max_):
                err = 'Endpoints of interval must be int or float,'
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            if min_['type'] != 'int' and min_['type'] != 'float':
                err = 'Endpoints of interval must be int or float,'
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            return {"value":min_['type'], "min":min_, "max":max_, "obj":"range_type"}


    # Visit a parse tree produced by minizincParser#ti_variable_expr_tail.
    def visitTi_variable_expr_tail(self, ctx:minizincParser.Ti_variable_expr_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#set_ti_expr_tail.
    def visitSet_ti_expr_tail(self, ctx:minizincParser.Set_ti_expr_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#array_ti_expr_tail.
    def visitArray_ti_expr_tail(self, ctx:minizincParser.Array_ti_expr_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#expr.
    def visitExpr(self, ctx:minizincParser.ExprContext):
        if ctx.expr_atom():
            return self.visitExpr_atom(ctx.expr_atom())
        else:
            left = self.visitExpr(ctx.expr()[0])
            right = self.visitExpr(ctx.expr()[1])
            
            if not self._cast(left, right):
                err = 'Expected same type, found {} and {}: {}'.format(left['type'], right['type'], self._ctx_text(ctx))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                
            left_v = left['value']
            right_v = right['value']
            var = (left['var'] or right['var'])
            
            if ctx.BACKTICK():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.BACKTICK(), ctx))
            elif ctx.PLUSPLUS():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.PLUSPLUS(), ctx))
            elif ctx.INTERSECT():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.INTERSECT(), ctx))
            elif ctx.DIV():
                left_v = ToReal(left_v)
                right_v = ToReal(right_v)
                value = Div(left_v, right_v)
                return {"value":value, "type":"float", "var":var, "obj":"expr"}
            elif ctx.MOD():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.MOD(), ctx))
            elif ctx.IDIV():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.IDIV(), ctx))
            elif ctx.MULT():
                value = Times(left_v, right_v)
                return {"value":value, "type":left['type'], "var":var, "obj":"expr"}
            elif ctx.MINUS():
                value = Minus(left_v, right_v)
                return {"value":value, "type":left['type'], "var":var, "obj":"expr"}
            elif ctx.PLUS():
                value = Plus(left_v, right_v)
                return {"value":value, "type":left['type'], "var":var, "obj":"expr"}
            elif ctx.DOTDOT():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.DOTDOT(), ctx))
            elif ctx.SYMDIFF():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.SYMDIFF(), ctx))
            elif ctx.DIFF():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.DIFF(), ctx))
            elif ctx.UNION():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.UNION(), ctx))
            elif ctx.SUPERSET():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.SUPERSET(), ctx))
            elif ctx.SUBSET():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.SUBSET(), ctx))
            elif ctx.IN():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.IN(), ctx))
            elif ctx.NQ():
                value = NotEquals(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif (ctx.EQ() or ctx.EQEQ()):
                value = Iff(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.GE():
                value = GE(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.LE():
                value = LE(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.GT():
                value = GT(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.LT():
                value = LT(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.AND():
                value = And(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.XOR():
                value = Xor(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.OR():
                value = Or(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.RIMPL():
                value = Implies(right_v, left_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.IMPL():
                value = Implies(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            elif ctx.EQUIV():
                value = Iff(left_v, right_v)
                return {"value":value, "type":"bool", "var":var, "obj":"expr"}
            

    # Visit a parse tree produced by minizincParser#expr_atom.
    def visitExpr_atom(self, ctx:minizincParser.Expr_atomContext):
        expr = self.visitExpr_atom_head(ctx.expr_atom_head())
        tail = self.visitExpr_atom_tail(ctx.expr_atom_tail())
        annotations = self.visitAnnotations(ctx.annotations())
        return expr


    # Visit a parse tree produced by minizincParser#expr_atom_head.
    def visitExpr_atom_head(self, ctx:minizincParser.Expr_atom_headContext):
        if ctx.builtin_un_op():
            op = self.visitBuiltin_un_op(ctx.builtin_un_op())
            expr = self.visitExpr_atom(ctx.expr_atom())
            value = expr['value']
            
            if op == 'not':
                if expr['type'] == "bool":
                    value = Not(value)
                else:
                    err = 'Expected bool, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.expr_atom()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            elif op == '-':
                if expr['type'] == "float":
                    value = Times(value, Real(-1))
                elif expr['type'] == "int":
                    value = Times(value, Int(-1))
                else:
                    err = 'Expected int or float, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.expr_atom()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            return {"value":value, "type":expr['type'], "var":expr['var'], "obj":"expr"}
        elif ctx.expr():
            return self.visitExpr(ctx.expr())
        elif ctx.ident():
            id_ = self.visitIdent(ctx.ident())
            if id_ not in self.variables:
                raise WMIParsingFileException(WMIParsingFileException.VARIABLE_NOT_DECLARED, self._err(id_, ctx))
            ident = self.variables[id_]
            if ident['value'] == None:
                raise WMIParsingFileException(WMIParsingFileException.VARIABLE_NOT_INITIALIZED, self._err(id_, ctx))
            return {"value":ident['value'], "type":ident['type'], "var":ident['var'], "obj":"expr"}
        elif ctx.UNDERSCORE():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.UNDERSCORE, ctx))
        elif ctx.bool_literal():
            return self.visitBool_literal(ctx.bool_literal())
        elif ctx.int_literal():
            return self.visitInt_literal(ctx.int_literal())
        elif ctx.float_literal():
            return self.visitFloat_literal(ctx.float_literal())
        elif ctx.string_literal():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('string', ctx))
        elif ctx.set_literal():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('set', ctx))
        elif ctx.set_comp():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('set', ctx))
        elif ctx.array_literal():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('array', ctx))
        elif ctx.array_literal_2d():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('array', ctx))
        elif ctx.array_comp():
            raise WMIParsingFileException(WMIParsingFileException.TYPE_NOT_SUPPORTED, self._err('array', ctx))
        elif ctx.ann_literal():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('annotation', ctx))
        elif ctx.if_then_else_expr():
            return self.visitIf_then_else_expr(ctx.if_then_else_expr())
        elif ctx.let_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('let', ctx))
        elif ctx.call_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('function', ctx))
        elif ctx.gen_call_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('function', ctx))
                

    # Visit a parse tree produced by minizincParser#expr_atom_tail.
    def visitExpr_atom_tail(self, ctx:minizincParser.Expr_atom_tailContext):
        if ctx.array_access_tail():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('array', ctx))


    # Visit a parse tree produced by minizincParser#num_expr.
    def visitNum_expr(self, ctx:minizincParser.Num_exprContext):
        if ctx.num_expr_atom():
            return self.visitNum_expr_atom(ctx.num_expr_atom())
        else:
            left = self.visitNum_expr(ctx.num_expr()[0])
            right = self.visitNum_expr(ctx.num_expr()[1])
            
            if not self._cast(left, right):
                err = 'Expected same type, found {} and {}: {}'.format(left['type'], right['type'], self._ctx_text(ctx))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
                
            left_v = left['value']
            right_v = right['value']
            type_ = left['type']
            var = (left['var'] or right['var'])
            
            if ctx.BACKTICK():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.BACKTICK(), ctx))
            elif ctx.DIV():
                left_v = ToReal(left_v)
                right_v = ToReal(right_v)
                value = Div(left_v, right_v)
                return {"value":value, "type":"float", "var":var, "obj":"expr"}
            elif ctx.MOD():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.MOD(), ctx))
            elif ctx.IDIV():
                raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err(ctx.IDIV(), ctx))
            elif ctx.MULT():
                value = Times(left_v, right_v)
                return {"value":value, "type":type_, "var":var, "obj":"expr"}
            elif ctx.MINUS():
                value = Minus(left_v, right_v)
                return {"value":value, "type":type_, "var":var, "obj":"expr"}
            elif ctx.PLUS():
                value = Plus(left_v, right_v)
                return {"value":value, "type":type_, "var":var, "obj":"expr"}


    # Visit a parse tree produced by minizincParser#num_expr_atom.
    def visitNum_expr_atom(self, ctx:minizincParser.Num_expr_atomContext):
        expr = self.visitNum_expr_atom_head(ctx.num_expr_atom_head())
        tail = self.visitExpr_atom_tail(ctx.expr_atom_tail())
        annotations = self.visitAnnotations(ctx.annotations())
        return expr


    # Visit a parse tree produced by minizincParser#num_expr_atom_head.
    def visitNum_expr_atom_head(self, ctx:minizincParser.Num_expr_atom_headContext):
        if ctx.builtin_num_un_op():
            op = self.visitBuiltin_num_un_op(ctx.builtin_num_un_op())
            expr = self.visitNum_expr_atom(ctx.num_expr_atom())
            if op == '-':
                if expr['type'] == "int":
                    expr['value'] = Times(expr['value'], Int(-1))
                elif expr['type'] == "real":
                    expr['value'] = Times(expr['value'], Real(-1))
                else:
                    err = 'Expected int or float, found {}: \'{}\''.format(expr['type'], self._ctx_text(ctx.num_expr_atom()))
                    raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            return {"value":expr['value'], "type":expr['type'], "var":expr['var'], "obj":"expr"}
        elif ctx.num_expr():
            return self.visitNum_expr(ctx.num_expr())
        elif ctx.ident():
            id_ = self.visitIdent(ctx.ident())
            if id_ not in self.variables:
                raise WMIParsingFileException(WMIParsingFileException.VARIABLE_NOT_DECLARED, self._err(id_, ctx))
            ident = self.variables[id_]
            if ident['value'] == None:
                raise WMIParsingFileException(WMIParsingFileException.VARIABLE_NOT_INITIALIZED, self._err(id_, ctx))
            return {"value":ident['value'], "type":ident['type'], "var":ident['var'], "obj":"expr"}
        elif ctx.int_literal():
            return self.visitInt_literal(ctx.int_literal())
        elif ctx.float_literal():
            return self.visitFloat_literal(ctx.float_literal())
        elif ctx.if_then_else_expr():
            return self.visitIf_then_else_expr(ctx.if_then_else_expr())
        elif ctx.let_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('let', ctx))
        elif ctx.call_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('function', ctx))
        elif ctx.gen_call_expr():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('function', ctx))


    # Visit a parse tree produced by minizincParser#builtin_un_op.
    def visitBuiltin_un_op(self, ctx:minizincParser.Builtin_un_opContext):
        if ctx.NOT():
            return "not"
        elif ctx.builtin_num_un_op():
            return self.visitBuiltin_num_un_op(ctx.builtin_num_un_op())


    # Visit a parse tree produced by minizincParser#builtin_num_un_op.
    def visitBuiltin_num_un_op(self, ctx:minizincParser.Builtin_num_un_opContext):
        if ctx.PLUS():
            return "+"
        elif ctx.MINUS():
            return "-"


    # Visit a parse tree produced by minizincParser#bool_literal.
    def visitBool_literal(self, ctx:minizincParser.Bool_literalContext):
        if ctx.getText() == "true":
            value = True
        else:
            value = False
        value = Bool(value)
        return {"value":value, "type":"bool", "var":False, "obj":"expr"}


    # Visit a parse tree produced by minizincParser#int_literal.
    def visitInt_literal(self, ctx:minizincParser.Int_literalContext):
        value = Int(int(ctx.getText(), 0))
        return {"value":value, "type":"int", "var":False, "obj":"expr"}


    # Visit a parse tree produced by minizincParser#float_literal.
    def visitFloat_literal(self, ctx:minizincParser.Float_literalContext):
        value = Real(float(ctx.getText()))
        return {"value":value, "type":"float", "var":False, "obj":"expr"}


    # Visit a parse tree produced by minizincParser#string_literal.
    def visitString_literal(self, ctx:minizincParser.String_literalContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#set_literal.
    def visitSet_literal(self, ctx:minizincParser.Set_literalContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#set_comp.
    def visitSet_comp(self, ctx:minizincParser.Set_compContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#comp_tail.
    def visitComp_tail(self, ctx:minizincParser.Comp_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#generator.
    def visitGenerator(self, ctx:minizincParser.GeneratorContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#array_literal.
    def visitArray_literal(self, ctx:minizincParser.Array_literalContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#array_literal_2d.
    def visitArray_literal_2d(self, ctx:minizincParser.Array_literal_2dContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#array_comp.
    def visitArray_comp(self, ctx:minizincParser.Array_compContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#array_access_tail.
    def visitArray_access_tail(self, ctx:minizincParser.Array_access_tailContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#ann_literal.
    def visitAnn_literal(self, ctx:minizincParser.Ann_literalContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#if_then_else_expr.
    def visitIf_then_else_expr(self, ctx:minizincParser.If_then_else_exprContext):
        expr = ctx.expr()
        
        # Start from last ite and continue backwards
        index = len(expr)-1
        cond = self.visitExpr(expr[index-2])
        then = self.visitExpr(expr[index-1])
        else_ = self.visitExpr(expr[index])
        
        # check that condition is boolean
        if cond['type'] != "bool":
            err = 'Expected bool, found {}: \'{}\''.format(cond['type'], self._ctx_text(expr[index-2]))
            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
        
        # check that then and else parts are of the same type
        if not self._cast(then, else_):
            err = 'THEN and ELSE parts must be of the same type: {}'.format(self._ctx_text(ctx))
            raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            
        value = Ite ( cond['value'], then['value'], else_['value'] )
        var = cond['var'] or then['var'] or else_['var']
        ite = {"value":value, "type":then['type'], "var":var, "obj":expr}
        
        index -= 3
        while index >= 0:
            then = self.visitExpr(expr[index])
            cond = self.visitExpr(expr[index-1])
            
            # check that condition is boolean
            if cond['type'] != "bool":
                err = 'Expected bool, found {}: \'{}\''.format(cond['type'], self._ctx_text(expr[index-1]))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            
            # check that then and else parts are of the same type
            if not self._cast(then, ite):
                err = 'THEN and ELSE parts must be of the same type: {}'.format(self._ctx_text(ctx))
                raise WMIParsingFileException(WMIParsingFileException.TYPE_ERROR, self._err(err, ctx))
            
            
            value = Ite ( cond['value'], then['value'], ite['value'] )
            var = cond['var'] or then['var'] or ite['var']
            ite = {"value":value, "type":then['type'], "var":var, "obj":expr}
            
            index -= 2
        return ite


    # Visit a parse tree produced by minizincParser#call_expr.
    def visitCall_expr(self, ctx:minizincParser.Call_exprContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#let_expr.
    def visitLet_expr(self, ctx:minizincParser.Let_exprContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#let_item.
    def visitLet_item(self, ctx:minizincParser.Let_itemContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#gen_call_expr.
    def visitGen_call_expr(self, ctx:minizincParser.Gen_call_exprContext):
        pass # function never called


    # Return the ident as a string
    def visitIdent(self, ctx:minizincParser.IdentContext):
        return ctx.getText()


    # Visit a parse tree produced by minizincParser#ident_or_quoted_op.
    def visitIdent_or_quoted_op(self, ctx:minizincParser.Ident_or_quoted_opContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#quoted_op.
    def visitQuoted_op(self, ctx:minizincParser.Quoted_opContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#annotations.
    def visitAnnotations(self, ctx:minizincParser.AnnotationsContext):
        if ctx.annotation():
            raise WMIParsingFileException(WMIParsingFileException.OPERATION_NOT_SUPPORTED, self._err('annotation', ctx))


    # Visit a parse tree produced by minizincParser#annotation.
    def visitAnnotation(self, ctx:minizincParser.AnnotationContext):
        pass # function never called


    # Visit a parse tree produced by minizincParser#string_annotation.
    def visitString_annotation(self, ctx:minizincParser.String_annotationContext):
        pass # function never called

