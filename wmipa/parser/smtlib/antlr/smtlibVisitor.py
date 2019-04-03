# Generated from smtlib.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .smtlibParser import smtlibParser
else:
    from smtlibParser import smtlibParser

# This class defines a complete generic visitor for a parse tree produced by smtlibParser.

class smtlibVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by smtlibParser#start.
    def visitStart(self, ctx:smtlibParser.StartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#response.
    def visitResponse(self, ctx:smtlibParser.ResponseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#generalReservedWord.
    def visitGeneralReservedWord(self, ctx:smtlibParser.GeneralReservedWordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#simpleSymbol.
    def visitSimpleSymbol(self, ctx:smtlibParser.SimpleSymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#quotedSymbol.
    def visitQuotedSymbol(self, ctx:smtlibParser.QuotedSymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#predefSymbol.
    def visitPredefSymbol(self, ctx:smtlibParser.PredefSymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#predefKeyword.
    def visitPredefKeyword(self, ctx:smtlibParser.PredefKeywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#symbol.
    def visitSymbol(self, ctx:smtlibParser.SymbolContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#numeral.
    def visitNumeral(self, ctx:smtlibParser.NumeralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#decimal.
    def visitDecimal(self, ctx:smtlibParser.DecimalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#hexadecimal.
    def visitHexadecimal(self, ctx:smtlibParser.HexadecimalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#binary.
    def visitBinary(self, ctx:smtlibParser.BinaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#string.
    def visitString(self, ctx:smtlibParser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#keyword.
    def visitKeyword(self, ctx:smtlibParser.KeywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#spec_constant.
    def visitSpec_constant(self, ctx:smtlibParser.Spec_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#s_expr.
    def visitS_expr(self, ctx:smtlibParser.S_exprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#index.
    def visitIndex(self, ctx:smtlibParser.IndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#identifier.
    def visitIdentifier(self, ctx:smtlibParser.IdentifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#attribute_value.
    def visitAttribute_value(self, ctx:smtlibParser.Attribute_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#attribute.
    def visitAttribute(self, ctx:smtlibParser.AttributeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#sort.
    def visitSort(self, ctx:smtlibParser.SortContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#qual_identifer.
    def visitQual_identifer(self, ctx:smtlibParser.Qual_identiferContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#var_binding.
    def visitVar_binding(self, ctx:smtlibParser.Var_bindingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#sorted_var.
    def visitSorted_var(self, ctx:smtlibParser.Sorted_varContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#pattern.
    def visitPattern(self, ctx:smtlibParser.PatternContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#match_case.
    def visitMatch_case(self, ctx:smtlibParser.Match_caseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#term.
    def visitTerm(self, ctx:smtlibParser.TermContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#sort_symbol_decl.
    def visitSort_symbol_decl(self, ctx:smtlibParser.Sort_symbol_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#meta_spec_constant.
    def visitMeta_spec_constant(self, ctx:smtlibParser.Meta_spec_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#fun_symbol_decl.
    def visitFun_symbol_decl(self, ctx:smtlibParser.Fun_symbol_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#par_fun_symbol_decl.
    def visitPar_fun_symbol_decl(self, ctx:smtlibParser.Par_fun_symbol_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#theory_attribute.
    def visitTheory_attribute(self, ctx:smtlibParser.Theory_attributeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#theory_decl.
    def visitTheory_decl(self, ctx:smtlibParser.Theory_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#logic_attribue.
    def visitLogic_attribue(self, ctx:smtlibParser.Logic_attribueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#logic.
    def visitLogic(self, ctx:smtlibParser.LogicContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#sort_dec.
    def visitSort_dec(self, ctx:smtlibParser.Sort_decContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#selector_dec.
    def visitSelector_dec(self, ctx:smtlibParser.Selector_decContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#constructor_dec.
    def visitConstructor_dec(self, ctx:smtlibParser.Constructor_decContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#datatype_dec.
    def visitDatatype_dec(self, ctx:smtlibParser.Datatype_decContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#function_dec.
    def visitFunction_dec(self, ctx:smtlibParser.Function_decContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#function_def.
    def visitFunction_def(self, ctx:smtlibParser.Function_defContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#prop_literal.
    def visitProp_literal(self, ctx:smtlibParser.Prop_literalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#script.
    def visitScript(self, ctx:smtlibParser.ScriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_assert.
    def visitCmd_assert(self, ctx:smtlibParser.Cmd_assertContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_checkSat.
    def visitCmd_checkSat(self, ctx:smtlibParser.Cmd_checkSatContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_checkSatAssuming.
    def visitCmd_checkSatAssuming(self, ctx:smtlibParser.Cmd_checkSatAssumingContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_declareConst.
    def visitCmd_declareConst(self, ctx:smtlibParser.Cmd_declareConstContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_declareDatatype.
    def visitCmd_declareDatatype(self, ctx:smtlibParser.Cmd_declareDatatypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_declareDatatypes.
    def visitCmd_declareDatatypes(self, ctx:smtlibParser.Cmd_declareDatatypesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_declareFun.
    def visitCmd_declareFun(self, ctx:smtlibParser.Cmd_declareFunContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_declareSort.
    def visitCmd_declareSort(self, ctx:smtlibParser.Cmd_declareSortContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_defineFun.
    def visitCmd_defineFun(self, ctx:smtlibParser.Cmd_defineFunContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_defineFunRec.
    def visitCmd_defineFunRec(self, ctx:smtlibParser.Cmd_defineFunRecContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_defineFunsRec.
    def visitCmd_defineFunsRec(self, ctx:smtlibParser.Cmd_defineFunsRecContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_defineSort.
    def visitCmd_defineSort(self, ctx:smtlibParser.Cmd_defineSortContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_echo.
    def visitCmd_echo(self, ctx:smtlibParser.Cmd_echoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_exit.
    def visitCmd_exit(self, ctx:smtlibParser.Cmd_exitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getAssertions.
    def visitCmd_getAssertions(self, ctx:smtlibParser.Cmd_getAssertionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getAssignment.
    def visitCmd_getAssignment(self, ctx:smtlibParser.Cmd_getAssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getInfo.
    def visitCmd_getInfo(self, ctx:smtlibParser.Cmd_getInfoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getModel.
    def visitCmd_getModel(self, ctx:smtlibParser.Cmd_getModelContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getOption.
    def visitCmd_getOption(self, ctx:smtlibParser.Cmd_getOptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getProof.
    def visitCmd_getProof(self, ctx:smtlibParser.Cmd_getProofContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getUnsatAssumptions.
    def visitCmd_getUnsatAssumptions(self, ctx:smtlibParser.Cmd_getUnsatAssumptionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getUnsatCore.
    def visitCmd_getUnsatCore(self, ctx:smtlibParser.Cmd_getUnsatCoreContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_getValue.
    def visitCmd_getValue(self, ctx:smtlibParser.Cmd_getValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_pop.
    def visitCmd_pop(self, ctx:smtlibParser.Cmd_popContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_push.
    def visitCmd_push(self, ctx:smtlibParser.Cmd_pushContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_reset.
    def visitCmd_reset(self, ctx:smtlibParser.Cmd_resetContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_resetAssertions.
    def visitCmd_resetAssertions(self, ctx:smtlibParser.Cmd_resetAssertionsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_setInfo.
    def visitCmd_setInfo(self, ctx:smtlibParser.Cmd_setInfoContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_setLogic.
    def visitCmd_setLogic(self, ctx:smtlibParser.Cmd_setLogicContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_setOption.
    def visitCmd_setOption(self, ctx:smtlibParser.Cmd_setOptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_weight.
    def visitCmd_weight(self, ctx:smtlibParser.Cmd_weightContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#cmd_query.
    def visitCmd_query(self, ctx:smtlibParser.Cmd_queryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#command.
    def visitCommand(self, ctx:smtlibParser.CommandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#b_value.
    def visitB_value(self, ctx:smtlibParser.B_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#option.
    def visitOption(self, ctx:smtlibParser.OptionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#info_flag.
    def visitInfo_flag(self, ctx:smtlibParser.Info_flagContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#error_behaviour.
    def visitError_behaviour(self, ctx:smtlibParser.Error_behaviourContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#reason_unknown.
    def visitReason_unknown(self, ctx:smtlibParser.Reason_unknownContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#model_response.
    def visitModel_response(self, ctx:smtlibParser.Model_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#info_response.
    def visitInfo_response(self, ctx:smtlibParser.Info_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#valuation_pair.
    def visitValuation_pair(self, ctx:smtlibParser.Valuation_pairContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#t_valuation_pair.
    def visitT_valuation_pair(self, ctx:smtlibParser.T_valuation_pairContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#check_sat_response.
    def visitCheck_sat_response(self, ctx:smtlibParser.Check_sat_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#echo_response.
    def visitEcho_response(self, ctx:smtlibParser.Echo_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_assertions_response.
    def visitGet_assertions_response(self, ctx:smtlibParser.Get_assertions_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_assignment_response.
    def visitGet_assignment_response(self, ctx:smtlibParser.Get_assignment_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_info_response.
    def visitGet_info_response(self, ctx:smtlibParser.Get_info_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_model_response.
    def visitGet_model_response(self, ctx:smtlibParser.Get_model_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_option_response.
    def visitGet_option_response(self, ctx:smtlibParser.Get_option_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_proof_response.
    def visitGet_proof_response(self, ctx:smtlibParser.Get_proof_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_unsat_assump_response.
    def visitGet_unsat_assump_response(self, ctx:smtlibParser.Get_unsat_assump_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_unsat_core_response.
    def visitGet_unsat_core_response(self, ctx:smtlibParser.Get_unsat_core_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#get_value_response.
    def visitGet_value_response(self, ctx:smtlibParser.Get_value_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#specific_success_response.
    def visitSpecific_success_response(self, ctx:smtlibParser.Specific_success_responseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by smtlibParser#general_response.
    def visitGeneral_response(self, ctx:smtlibParser.General_responseContext):
        return self.visitChildren(ctx)



del smtlibParser