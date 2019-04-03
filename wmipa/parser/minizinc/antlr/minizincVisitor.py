# Generated from minizinc.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .minizincParser import minizincParser
else:
    from minizincParser import minizincParser

# This class defines a complete generic visitor for a parse tree produced by minizincParser.

class minizincVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by minizincParser#minizinc.
    def visitMinizinc(self, ctx:minizincParser.MinizincContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#item.
    def visitItem(self, ctx:minizincParser.ItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ti_expr_and_id.
    def visitTi_expr_and_id(self, ctx:minizincParser.Ti_expr_and_idContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#include_item.
    def visitInclude_item(self, ctx:minizincParser.Include_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#var_decl_item.
    def visitVar_decl_item(self, ctx:minizincParser.Var_decl_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#enum_item.
    def visitEnum_item(self, ctx:minizincParser.Enum_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#enum_cases.
    def visitEnum_cases(self, ctx:minizincParser.Enum_casesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#assign_item.
    def visitAssign_item(self, ctx:minizincParser.Assign_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#constraint_item.
    def visitConstraint_item(self, ctx:minizincParser.Constraint_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#solve_item.
    def visitSolve_item(self, ctx:minizincParser.Solve_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#output_item.
    def visitOutput_item(self, ctx:minizincParser.Output_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#predicate_item.
    def visitPredicate_item(self, ctx:minizincParser.Predicate_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#test_item.
    def visitTest_item(self, ctx:minizincParser.Test_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#function_item.
    def visitFunction_item(self, ctx:minizincParser.Function_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#annotation_item.
    def visitAnnotation_item(self, ctx:minizincParser.Annotation_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#weight_item.
    def visitWeight_item(self, ctx:minizincParser.Weight_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#query_item.
    def visitQuery_item(self, ctx:minizincParser.Query_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#operation_item_tail.
    def visitOperation_item_tail(self, ctx:minizincParser.Operation_item_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#params.
    def visitParams(self, ctx:minizincParser.ParamsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ti_expr.
    def visitTi_expr(self, ctx:minizincParser.Ti_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#base_ti_expr.
    def visitBase_ti_expr(self, ctx:minizincParser.Base_ti_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#var_par.
    def visitVar_par(self, ctx:minizincParser.Var_parContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#base_type.
    def visitBase_type(self, ctx:minizincParser.Base_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#base_ti_expr_tail.
    def visitBase_ti_expr_tail(self, ctx:minizincParser.Base_ti_expr_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ti_variable_expr_tail.
    def visitTi_variable_expr_tail(self, ctx:minizincParser.Ti_variable_expr_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#set_ti_expr_tail.
    def visitSet_ti_expr_tail(self, ctx:minizincParser.Set_ti_expr_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#array_ti_expr_tail.
    def visitArray_ti_expr_tail(self, ctx:minizincParser.Array_ti_expr_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#expr.
    def visitExpr(self, ctx:minizincParser.ExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#expr_atom.
    def visitExpr_atom(self, ctx:minizincParser.Expr_atomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#expr_atom_head.
    def visitExpr_atom_head(self, ctx:minizincParser.Expr_atom_headContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#expr_atom_tail.
    def visitExpr_atom_tail(self, ctx:minizincParser.Expr_atom_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#num_expr.
    def visitNum_expr(self, ctx:minizincParser.Num_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#num_expr_atom.
    def visitNum_expr_atom(self, ctx:minizincParser.Num_expr_atomContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#num_expr_atom_head.
    def visitNum_expr_atom_head(self, ctx:minizincParser.Num_expr_atom_headContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#builtin_un_op.
    def visitBuiltin_un_op(self, ctx:minizincParser.Builtin_un_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#builtin_num_un_op.
    def visitBuiltin_num_un_op(self, ctx:minizincParser.Builtin_num_un_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#bool_literal.
    def visitBool_literal(self, ctx:minizincParser.Bool_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#int_literal.
    def visitInt_literal(self, ctx:minizincParser.Int_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#float_literal.
    def visitFloat_literal(self, ctx:minizincParser.Float_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#string_literal.
    def visitString_literal(self, ctx:minizincParser.String_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#set_literal.
    def visitSet_literal(self, ctx:minizincParser.Set_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#set_comp.
    def visitSet_comp(self, ctx:minizincParser.Set_compContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#comp_tail.
    def visitComp_tail(self, ctx:minizincParser.Comp_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#generator.
    def visitGenerator(self, ctx:minizincParser.GeneratorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#array_literal.
    def visitArray_literal(self, ctx:minizincParser.Array_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#array_literal_2d.
    def visitArray_literal_2d(self, ctx:minizincParser.Array_literal_2dContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#array_comp.
    def visitArray_comp(self, ctx:minizincParser.Array_compContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#array_access_tail.
    def visitArray_access_tail(self, ctx:minizincParser.Array_access_tailContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ann_literal.
    def visitAnn_literal(self, ctx:minizincParser.Ann_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#if_then_else_expr.
    def visitIf_then_else_expr(self, ctx:minizincParser.If_then_else_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#call_expr.
    def visitCall_expr(self, ctx:minizincParser.Call_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#let_expr.
    def visitLet_expr(self, ctx:minizincParser.Let_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#let_item.
    def visitLet_item(self, ctx:minizincParser.Let_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#gen_call_expr.
    def visitGen_call_expr(self, ctx:minizincParser.Gen_call_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ident.
    def visitIdent(self, ctx:minizincParser.IdentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#ident_or_quoted_op.
    def visitIdent_or_quoted_op(self, ctx:minizincParser.Ident_or_quoted_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#quoted_op.
    def visitQuoted_op(self, ctx:minizincParser.Quoted_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#annotations.
    def visitAnnotations(self, ctx:minizincParser.AnnotationsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#annotation.
    def visitAnnotation(self, ctx:minizincParser.AnnotationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by minizincParser#string_annotation.
    def visitString_annotation(self, ctx:minizincParser.String_annotationContext):
        return self.visitChildren(ctx)



del minizincParser