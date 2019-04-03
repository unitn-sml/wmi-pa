# Generated from minizinc.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .minizincParser import minizincParser
else:
    from minizincParser import minizincParser

# This class defines a complete listener for a parse tree produced by minizincParser.
class minizincListener(ParseTreeListener):

    # Enter a parse tree produced by minizincParser#minizinc.
    def enterMinizinc(self, ctx:minizincParser.MinizincContext):
        pass

    # Exit a parse tree produced by minizincParser#minizinc.
    def exitMinizinc(self, ctx:minizincParser.MinizincContext):
        pass


    # Enter a parse tree produced by minizincParser#item.
    def enterItem(self, ctx:minizincParser.ItemContext):
        pass

    # Exit a parse tree produced by minizincParser#item.
    def exitItem(self, ctx:minizincParser.ItemContext):
        pass


    # Enter a parse tree produced by minizincParser#ti_expr_and_id.
    def enterTi_expr_and_id(self, ctx:minizincParser.Ti_expr_and_idContext):
        pass

    # Exit a parse tree produced by minizincParser#ti_expr_and_id.
    def exitTi_expr_and_id(self, ctx:minizincParser.Ti_expr_and_idContext):
        pass


    # Enter a parse tree produced by minizincParser#include_item.
    def enterInclude_item(self, ctx:minizincParser.Include_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#include_item.
    def exitInclude_item(self, ctx:minizincParser.Include_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#var_decl_item.
    def enterVar_decl_item(self, ctx:minizincParser.Var_decl_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#var_decl_item.
    def exitVar_decl_item(self, ctx:minizincParser.Var_decl_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#enum_item.
    def enterEnum_item(self, ctx:minizincParser.Enum_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#enum_item.
    def exitEnum_item(self, ctx:minizincParser.Enum_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#enum_cases.
    def enterEnum_cases(self, ctx:minizincParser.Enum_casesContext):
        pass

    # Exit a parse tree produced by minizincParser#enum_cases.
    def exitEnum_cases(self, ctx:minizincParser.Enum_casesContext):
        pass


    # Enter a parse tree produced by minizincParser#assign_item.
    def enterAssign_item(self, ctx:minizincParser.Assign_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#assign_item.
    def exitAssign_item(self, ctx:minizincParser.Assign_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#constraint_item.
    def enterConstraint_item(self, ctx:minizincParser.Constraint_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#constraint_item.
    def exitConstraint_item(self, ctx:minizincParser.Constraint_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#solve_item.
    def enterSolve_item(self, ctx:minizincParser.Solve_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#solve_item.
    def exitSolve_item(self, ctx:minizincParser.Solve_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#output_item.
    def enterOutput_item(self, ctx:minizincParser.Output_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#output_item.
    def exitOutput_item(self, ctx:minizincParser.Output_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#predicate_item.
    def enterPredicate_item(self, ctx:minizincParser.Predicate_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#predicate_item.
    def exitPredicate_item(self, ctx:minizincParser.Predicate_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#test_item.
    def enterTest_item(self, ctx:minizincParser.Test_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#test_item.
    def exitTest_item(self, ctx:minizincParser.Test_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#function_item.
    def enterFunction_item(self, ctx:minizincParser.Function_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#function_item.
    def exitFunction_item(self, ctx:minizincParser.Function_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#annotation_item.
    def enterAnnotation_item(self, ctx:minizincParser.Annotation_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#annotation_item.
    def exitAnnotation_item(self, ctx:minizincParser.Annotation_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#weight_item.
    def enterWeight_item(self, ctx:minizincParser.Weight_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#weight_item.
    def exitWeight_item(self, ctx:minizincParser.Weight_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#query_item.
    def enterQuery_item(self, ctx:minizincParser.Query_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#query_item.
    def exitQuery_item(self, ctx:minizincParser.Query_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#operation_item_tail.
    def enterOperation_item_tail(self, ctx:minizincParser.Operation_item_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#operation_item_tail.
    def exitOperation_item_tail(self, ctx:minizincParser.Operation_item_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#params.
    def enterParams(self, ctx:minizincParser.ParamsContext):
        pass

    # Exit a parse tree produced by minizincParser#params.
    def exitParams(self, ctx:minizincParser.ParamsContext):
        pass


    # Enter a parse tree produced by minizincParser#ti_expr.
    def enterTi_expr(self, ctx:minizincParser.Ti_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#ti_expr.
    def exitTi_expr(self, ctx:minizincParser.Ti_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#base_ti_expr.
    def enterBase_ti_expr(self, ctx:minizincParser.Base_ti_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#base_ti_expr.
    def exitBase_ti_expr(self, ctx:minizincParser.Base_ti_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#var_par.
    def enterVar_par(self, ctx:minizincParser.Var_parContext):
        pass

    # Exit a parse tree produced by minizincParser#var_par.
    def exitVar_par(self, ctx:minizincParser.Var_parContext):
        pass


    # Enter a parse tree produced by minizincParser#base_type.
    def enterBase_type(self, ctx:minizincParser.Base_typeContext):
        pass

    # Exit a parse tree produced by minizincParser#base_type.
    def exitBase_type(self, ctx:minizincParser.Base_typeContext):
        pass


    # Enter a parse tree produced by minizincParser#base_ti_expr_tail.
    def enterBase_ti_expr_tail(self, ctx:minizincParser.Base_ti_expr_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#base_ti_expr_tail.
    def exitBase_ti_expr_tail(self, ctx:minizincParser.Base_ti_expr_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#ti_variable_expr_tail.
    def enterTi_variable_expr_tail(self, ctx:minizincParser.Ti_variable_expr_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#ti_variable_expr_tail.
    def exitTi_variable_expr_tail(self, ctx:minizincParser.Ti_variable_expr_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#set_ti_expr_tail.
    def enterSet_ti_expr_tail(self, ctx:minizincParser.Set_ti_expr_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#set_ti_expr_tail.
    def exitSet_ti_expr_tail(self, ctx:minizincParser.Set_ti_expr_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#array_ti_expr_tail.
    def enterArray_ti_expr_tail(self, ctx:minizincParser.Array_ti_expr_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#array_ti_expr_tail.
    def exitArray_ti_expr_tail(self, ctx:minizincParser.Array_ti_expr_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#expr.
    def enterExpr(self, ctx:minizincParser.ExprContext):
        pass

    # Exit a parse tree produced by minizincParser#expr.
    def exitExpr(self, ctx:minizincParser.ExprContext):
        pass


    # Enter a parse tree produced by minizincParser#expr_atom.
    def enterExpr_atom(self, ctx:minizincParser.Expr_atomContext):
        pass

    # Exit a parse tree produced by minizincParser#expr_atom.
    def exitExpr_atom(self, ctx:minizincParser.Expr_atomContext):
        pass


    # Enter a parse tree produced by minizincParser#expr_atom_head.
    def enterExpr_atom_head(self, ctx:minizincParser.Expr_atom_headContext):
        pass

    # Exit a parse tree produced by minizincParser#expr_atom_head.
    def exitExpr_atom_head(self, ctx:minizincParser.Expr_atom_headContext):
        pass


    # Enter a parse tree produced by minizincParser#expr_atom_tail.
    def enterExpr_atom_tail(self, ctx:minizincParser.Expr_atom_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#expr_atom_tail.
    def exitExpr_atom_tail(self, ctx:minizincParser.Expr_atom_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#num_expr.
    def enterNum_expr(self, ctx:minizincParser.Num_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#num_expr.
    def exitNum_expr(self, ctx:minizincParser.Num_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#num_expr_atom.
    def enterNum_expr_atom(self, ctx:minizincParser.Num_expr_atomContext):
        pass

    # Exit a parse tree produced by minizincParser#num_expr_atom.
    def exitNum_expr_atom(self, ctx:minizincParser.Num_expr_atomContext):
        pass


    # Enter a parse tree produced by minizincParser#num_expr_atom_head.
    def enterNum_expr_atom_head(self, ctx:minizincParser.Num_expr_atom_headContext):
        pass

    # Exit a parse tree produced by minizincParser#num_expr_atom_head.
    def exitNum_expr_atom_head(self, ctx:minizincParser.Num_expr_atom_headContext):
        pass


    # Enter a parse tree produced by minizincParser#builtin_un_op.
    def enterBuiltin_un_op(self, ctx:minizincParser.Builtin_un_opContext):
        pass

    # Exit a parse tree produced by minizincParser#builtin_un_op.
    def exitBuiltin_un_op(self, ctx:minizincParser.Builtin_un_opContext):
        pass


    # Enter a parse tree produced by minizincParser#builtin_num_un_op.
    def enterBuiltin_num_un_op(self, ctx:minizincParser.Builtin_num_un_opContext):
        pass

    # Exit a parse tree produced by minizincParser#builtin_num_un_op.
    def exitBuiltin_num_un_op(self, ctx:minizincParser.Builtin_num_un_opContext):
        pass


    # Enter a parse tree produced by minizincParser#bool_literal.
    def enterBool_literal(self, ctx:minizincParser.Bool_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#bool_literal.
    def exitBool_literal(self, ctx:minizincParser.Bool_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#int_literal.
    def enterInt_literal(self, ctx:minizincParser.Int_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#int_literal.
    def exitInt_literal(self, ctx:minizincParser.Int_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#float_literal.
    def enterFloat_literal(self, ctx:minizincParser.Float_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#float_literal.
    def exitFloat_literal(self, ctx:minizincParser.Float_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#string_literal.
    def enterString_literal(self, ctx:minizincParser.String_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#string_literal.
    def exitString_literal(self, ctx:minizincParser.String_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#set_literal.
    def enterSet_literal(self, ctx:minizincParser.Set_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#set_literal.
    def exitSet_literal(self, ctx:minizincParser.Set_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#set_comp.
    def enterSet_comp(self, ctx:minizincParser.Set_compContext):
        pass

    # Exit a parse tree produced by minizincParser#set_comp.
    def exitSet_comp(self, ctx:minizincParser.Set_compContext):
        pass


    # Enter a parse tree produced by minizincParser#comp_tail.
    def enterComp_tail(self, ctx:minizincParser.Comp_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#comp_tail.
    def exitComp_tail(self, ctx:minizincParser.Comp_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#generator.
    def enterGenerator(self, ctx:minizincParser.GeneratorContext):
        pass

    # Exit a parse tree produced by minizincParser#generator.
    def exitGenerator(self, ctx:minizincParser.GeneratorContext):
        pass


    # Enter a parse tree produced by minizincParser#array_literal.
    def enterArray_literal(self, ctx:minizincParser.Array_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#array_literal.
    def exitArray_literal(self, ctx:minizincParser.Array_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#array_literal_2d.
    def enterArray_literal_2d(self, ctx:minizincParser.Array_literal_2dContext):
        pass

    # Exit a parse tree produced by minizincParser#array_literal_2d.
    def exitArray_literal_2d(self, ctx:minizincParser.Array_literal_2dContext):
        pass


    # Enter a parse tree produced by minizincParser#array_comp.
    def enterArray_comp(self, ctx:minizincParser.Array_compContext):
        pass

    # Exit a parse tree produced by minizincParser#array_comp.
    def exitArray_comp(self, ctx:minizincParser.Array_compContext):
        pass


    # Enter a parse tree produced by minizincParser#array_access_tail.
    def enterArray_access_tail(self, ctx:minizincParser.Array_access_tailContext):
        pass

    # Exit a parse tree produced by minizincParser#array_access_tail.
    def exitArray_access_tail(self, ctx:minizincParser.Array_access_tailContext):
        pass


    # Enter a parse tree produced by minizincParser#ann_literal.
    def enterAnn_literal(self, ctx:minizincParser.Ann_literalContext):
        pass

    # Exit a parse tree produced by minizincParser#ann_literal.
    def exitAnn_literal(self, ctx:minizincParser.Ann_literalContext):
        pass


    # Enter a parse tree produced by minizincParser#if_then_else_expr.
    def enterIf_then_else_expr(self, ctx:minizincParser.If_then_else_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#if_then_else_expr.
    def exitIf_then_else_expr(self, ctx:minizincParser.If_then_else_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#call_expr.
    def enterCall_expr(self, ctx:minizincParser.Call_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#call_expr.
    def exitCall_expr(self, ctx:minizincParser.Call_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#let_expr.
    def enterLet_expr(self, ctx:minizincParser.Let_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#let_expr.
    def exitLet_expr(self, ctx:minizincParser.Let_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#let_item.
    def enterLet_item(self, ctx:minizincParser.Let_itemContext):
        pass

    # Exit a parse tree produced by minizincParser#let_item.
    def exitLet_item(self, ctx:minizincParser.Let_itemContext):
        pass


    # Enter a parse tree produced by minizincParser#gen_call_expr.
    def enterGen_call_expr(self, ctx:minizincParser.Gen_call_exprContext):
        pass

    # Exit a parse tree produced by minizincParser#gen_call_expr.
    def exitGen_call_expr(self, ctx:minizincParser.Gen_call_exprContext):
        pass


    # Enter a parse tree produced by minizincParser#ident.
    def enterIdent(self, ctx:minizincParser.IdentContext):
        pass

    # Exit a parse tree produced by minizincParser#ident.
    def exitIdent(self, ctx:minizincParser.IdentContext):
        pass


    # Enter a parse tree produced by minizincParser#ident_or_quoted_op.
    def enterIdent_or_quoted_op(self, ctx:minizincParser.Ident_or_quoted_opContext):
        pass

    # Exit a parse tree produced by minizincParser#ident_or_quoted_op.
    def exitIdent_or_quoted_op(self, ctx:minizincParser.Ident_or_quoted_opContext):
        pass


    # Enter a parse tree produced by minizincParser#quoted_op.
    def enterQuoted_op(self, ctx:minizincParser.Quoted_opContext):
        pass

    # Exit a parse tree produced by minizincParser#quoted_op.
    def exitQuoted_op(self, ctx:minizincParser.Quoted_opContext):
        pass


    # Enter a parse tree produced by minizincParser#annotations.
    def enterAnnotations(self, ctx:minizincParser.AnnotationsContext):
        pass

    # Exit a parse tree produced by minizincParser#annotations.
    def exitAnnotations(self, ctx:minizincParser.AnnotationsContext):
        pass


    # Enter a parse tree produced by minizincParser#annotation.
    def enterAnnotation(self, ctx:minizincParser.AnnotationContext):
        pass

    # Exit a parse tree produced by minizincParser#annotation.
    def exitAnnotation(self, ctx:minizincParser.AnnotationContext):
        pass


    # Enter a parse tree produced by minizincParser#string_annotation.
    def enterString_annotation(self, ctx:minizincParser.String_annotationContext):
        pass

    # Exit a parse tree produced by minizincParser#string_annotation.
    def exitString_annotation(self, ctx:minizincParser.String_annotationContext):
        pass


