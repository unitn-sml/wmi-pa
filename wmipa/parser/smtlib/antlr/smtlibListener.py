# Generated from smtlib.g4 by ANTLR 4.7.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .smtlibParser import smtlibParser
else:
    from smtlibParser import smtlibParser

# This class defines a complete listener for a parse tree produced by smtlibParser.
class smtlibListener(ParseTreeListener):

    # Enter a parse tree produced by smtlibParser#start.
    def enterStart(self, ctx:smtlibParser.StartContext):
        pass

    # Exit a parse tree produced by smtlibParser#start.
    def exitStart(self, ctx:smtlibParser.StartContext):
        pass


    # Enter a parse tree produced by smtlibParser#response.
    def enterResponse(self, ctx:smtlibParser.ResponseContext):
        pass

    # Exit a parse tree produced by smtlibParser#response.
    def exitResponse(self, ctx:smtlibParser.ResponseContext):
        pass


    # Enter a parse tree produced by smtlibParser#generalReservedWord.
    def enterGeneralReservedWord(self, ctx:smtlibParser.GeneralReservedWordContext):
        pass

    # Exit a parse tree produced by smtlibParser#generalReservedWord.
    def exitGeneralReservedWord(self, ctx:smtlibParser.GeneralReservedWordContext):
        pass


    # Enter a parse tree produced by smtlibParser#simpleSymbol.
    def enterSimpleSymbol(self, ctx:smtlibParser.SimpleSymbolContext):
        pass

    # Exit a parse tree produced by smtlibParser#simpleSymbol.
    def exitSimpleSymbol(self, ctx:smtlibParser.SimpleSymbolContext):
        pass


    # Enter a parse tree produced by smtlibParser#quotedSymbol.
    def enterQuotedSymbol(self, ctx:smtlibParser.QuotedSymbolContext):
        pass

    # Exit a parse tree produced by smtlibParser#quotedSymbol.
    def exitQuotedSymbol(self, ctx:smtlibParser.QuotedSymbolContext):
        pass


    # Enter a parse tree produced by smtlibParser#predefSymbol.
    def enterPredefSymbol(self, ctx:smtlibParser.PredefSymbolContext):
        pass

    # Exit a parse tree produced by smtlibParser#predefSymbol.
    def exitPredefSymbol(self, ctx:smtlibParser.PredefSymbolContext):
        pass


    # Enter a parse tree produced by smtlibParser#predefKeyword.
    def enterPredefKeyword(self, ctx:smtlibParser.PredefKeywordContext):
        pass

    # Exit a parse tree produced by smtlibParser#predefKeyword.
    def exitPredefKeyword(self, ctx:smtlibParser.PredefKeywordContext):
        pass


    # Enter a parse tree produced by smtlibParser#symbol.
    def enterSymbol(self, ctx:smtlibParser.SymbolContext):
        pass

    # Exit a parse tree produced by smtlibParser#symbol.
    def exitSymbol(self, ctx:smtlibParser.SymbolContext):
        pass


    # Enter a parse tree produced by smtlibParser#numeral.
    def enterNumeral(self, ctx:smtlibParser.NumeralContext):
        pass

    # Exit a parse tree produced by smtlibParser#numeral.
    def exitNumeral(self, ctx:smtlibParser.NumeralContext):
        pass


    # Enter a parse tree produced by smtlibParser#decimal.
    def enterDecimal(self, ctx:smtlibParser.DecimalContext):
        pass

    # Exit a parse tree produced by smtlibParser#decimal.
    def exitDecimal(self, ctx:smtlibParser.DecimalContext):
        pass


    # Enter a parse tree produced by smtlibParser#hexadecimal.
    def enterHexadecimal(self, ctx:smtlibParser.HexadecimalContext):
        pass

    # Exit a parse tree produced by smtlibParser#hexadecimal.
    def exitHexadecimal(self, ctx:smtlibParser.HexadecimalContext):
        pass


    # Enter a parse tree produced by smtlibParser#binary.
    def enterBinary(self, ctx:smtlibParser.BinaryContext):
        pass

    # Exit a parse tree produced by smtlibParser#binary.
    def exitBinary(self, ctx:smtlibParser.BinaryContext):
        pass


    # Enter a parse tree produced by smtlibParser#string.
    def enterString(self, ctx:smtlibParser.StringContext):
        pass

    # Exit a parse tree produced by smtlibParser#string.
    def exitString(self, ctx:smtlibParser.StringContext):
        pass


    # Enter a parse tree produced by smtlibParser#keyword.
    def enterKeyword(self, ctx:smtlibParser.KeywordContext):
        pass

    # Exit a parse tree produced by smtlibParser#keyword.
    def exitKeyword(self, ctx:smtlibParser.KeywordContext):
        pass


    # Enter a parse tree produced by smtlibParser#spec_constant.
    def enterSpec_constant(self, ctx:smtlibParser.Spec_constantContext):
        pass

    # Exit a parse tree produced by smtlibParser#spec_constant.
    def exitSpec_constant(self, ctx:smtlibParser.Spec_constantContext):
        pass


    # Enter a parse tree produced by smtlibParser#s_expr.
    def enterS_expr(self, ctx:smtlibParser.S_exprContext):
        pass

    # Exit a parse tree produced by smtlibParser#s_expr.
    def exitS_expr(self, ctx:smtlibParser.S_exprContext):
        pass


    # Enter a parse tree produced by smtlibParser#index.
    def enterIndex(self, ctx:smtlibParser.IndexContext):
        pass

    # Exit a parse tree produced by smtlibParser#index.
    def exitIndex(self, ctx:smtlibParser.IndexContext):
        pass


    # Enter a parse tree produced by smtlibParser#identifier.
    def enterIdentifier(self, ctx:smtlibParser.IdentifierContext):
        pass

    # Exit a parse tree produced by smtlibParser#identifier.
    def exitIdentifier(self, ctx:smtlibParser.IdentifierContext):
        pass


    # Enter a parse tree produced by smtlibParser#attribute_value.
    def enterAttribute_value(self, ctx:smtlibParser.Attribute_valueContext):
        pass

    # Exit a parse tree produced by smtlibParser#attribute_value.
    def exitAttribute_value(self, ctx:smtlibParser.Attribute_valueContext):
        pass


    # Enter a parse tree produced by smtlibParser#attribute.
    def enterAttribute(self, ctx:smtlibParser.AttributeContext):
        pass

    # Exit a parse tree produced by smtlibParser#attribute.
    def exitAttribute(self, ctx:smtlibParser.AttributeContext):
        pass


    # Enter a parse tree produced by smtlibParser#sort.
    def enterSort(self, ctx:smtlibParser.SortContext):
        pass

    # Exit a parse tree produced by smtlibParser#sort.
    def exitSort(self, ctx:smtlibParser.SortContext):
        pass


    # Enter a parse tree produced by smtlibParser#qual_identifer.
    def enterQual_identifer(self, ctx:smtlibParser.Qual_identiferContext):
        pass

    # Exit a parse tree produced by smtlibParser#qual_identifer.
    def exitQual_identifer(self, ctx:smtlibParser.Qual_identiferContext):
        pass


    # Enter a parse tree produced by smtlibParser#var_binding.
    def enterVar_binding(self, ctx:smtlibParser.Var_bindingContext):
        pass

    # Exit a parse tree produced by smtlibParser#var_binding.
    def exitVar_binding(self, ctx:smtlibParser.Var_bindingContext):
        pass


    # Enter a parse tree produced by smtlibParser#sorted_var.
    def enterSorted_var(self, ctx:smtlibParser.Sorted_varContext):
        pass

    # Exit a parse tree produced by smtlibParser#sorted_var.
    def exitSorted_var(self, ctx:smtlibParser.Sorted_varContext):
        pass


    # Enter a parse tree produced by smtlibParser#pattern.
    def enterPattern(self, ctx:smtlibParser.PatternContext):
        pass

    # Exit a parse tree produced by smtlibParser#pattern.
    def exitPattern(self, ctx:smtlibParser.PatternContext):
        pass


    # Enter a parse tree produced by smtlibParser#match_case.
    def enterMatch_case(self, ctx:smtlibParser.Match_caseContext):
        pass

    # Exit a parse tree produced by smtlibParser#match_case.
    def exitMatch_case(self, ctx:smtlibParser.Match_caseContext):
        pass


    # Enter a parse tree produced by smtlibParser#term.
    def enterTerm(self, ctx:smtlibParser.TermContext):
        pass

    # Exit a parse tree produced by smtlibParser#term.
    def exitTerm(self, ctx:smtlibParser.TermContext):
        pass


    # Enter a parse tree produced by smtlibParser#sort_symbol_decl.
    def enterSort_symbol_decl(self, ctx:smtlibParser.Sort_symbol_declContext):
        pass

    # Exit a parse tree produced by smtlibParser#sort_symbol_decl.
    def exitSort_symbol_decl(self, ctx:smtlibParser.Sort_symbol_declContext):
        pass


    # Enter a parse tree produced by smtlibParser#meta_spec_constant.
    def enterMeta_spec_constant(self, ctx:smtlibParser.Meta_spec_constantContext):
        pass

    # Exit a parse tree produced by smtlibParser#meta_spec_constant.
    def exitMeta_spec_constant(self, ctx:smtlibParser.Meta_spec_constantContext):
        pass


    # Enter a parse tree produced by smtlibParser#fun_symbol_decl.
    def enterFun_symbol_decl(self, ctx:smtlibParser.Fun_symbol_declContext):
        pass

    # Exit a parse tree produced by smtlibParser#fun_symbol_decl.
    def exitFun_symbol_decl(self, ctx:smtlibParser.Fun_symbol_declContext):
        pass


    # Enter a parse tree produced by smtlibParser#par_fun_symbol_decl.
    def enterPar_fun_symbol_decl(self, ctx:smtlibParser.Par_fun_symbol_declContext):
        pass

    # Exit a parse tree produced by smtlibParser#par_fun_symbol_decl.
    def exitPar_fun_symbol_decl(self, ctx:smtlibParser.Par_fun_symbol_declContext):
        pass


    # Enter a parse tree produced by smtlibParser#theory_attribute.
    def enterTheory_attribute(self, ctx:smtlibParser.Theory_attributeContext):
        pass

    # Exit a parse tree produced by smtlibParser#theory_attribute.
    def exitTheory_attribute(self, ctx:smtlibParser.Theory_attributeContext):
        pass


    # Enter a parse tree produced by smtlibParser#theory_decl.
    def enterTheory_decl(self, ctx:smtlibParser.Theory_declContext):
        pass

    # Exit a parse tree produced by smtlibParser#theory_decl.
    def exitTheory_decl(self, ctx:smtlibParser.Theory_declContext):
        pass


    # Enter a parse tree produced by smtlibParser#logic_attribue.
    def enterLogic_attribue(self, ctx:smtlibParser.Logic_attribueContext):
        pass

    # Exit a parse tree produced by smtlibParser#logic_attribue.
    def exitLogic_attribue(self, ctx:smtlibParser.Logic_attribueContext):
        pass


    # Enter a parse tree produced by smtlibParser#logic.
    def enterLogic(self, ctx:smtlibParser.LogicContext):
        pass

    # Exit a parse tree produced by smtlibParser#logic.
    def exitLogic(self, ctx:smtlibParser.LogicContext):
        pass


    # Enter a parse tree produced by smtlibParser#sort_dec.
    def enterSort_dec(self, ctx:smtlibParser.Sort_decContext):
        pass

    # Exit a parse tree produced by smtlibParser#sort_dec.
    def exitSort_dec(self, ctx:smtlibParser.Sort_decContext):
        pass


    # Enter a parse tree produced by smtlibParser#selector_dec.
    def enterSelector_dec(self, ctx:smtlibParser.Selector_decContext):
        pass

    # Exit a parse tree produced by smtlibParser#selector_dec.
    def exitSelector_dec(self, ctx:smtlibParser.Selector_decContext):
        pass


    # Enter a parse tree produced by smtlibParser#constructor_dec.
    def enterConstructor_dec(self, ctx:smtlibParser.Constructor_decContext):
        pass

    # Exit a parse tree produced by smtlibParser#constructor_dec.
    def exitConstructor_dec(self, ctx:smtlibParser.Constructor_decContext):
        pass


    # Enter a parse tree produced by smtlibParser#datatype_dec.
    def enterDatatype_dec(self, ctx:smtlibParser.Datatype_decContext):
        pass

    # Exit a parse tree produced by smtlibParser#datatype_dec.
    def exitDatatype_dec(self, ctx:smtlibParser.Datatype_decContext):
        pass


    # Enter a parse tree produced by smtlibParser#function_dec.
    def enterFunction_dec(self, ctx:smtlibParser.Function_decContext):
        pass

    # Exit a parse tree produced by smtlibParser#function_dec.
    def exitFunction_dec(self, ctx:smtlibParser.Function_decContext):
        pass


    # Enter a parse tree produced by smtlibParser#function_def.
    def enterFunction_def(self, ctx:smtlibParser.Function_defContext):
        pass

    # Exit a parse tree produced by smtlibParser#function_def.
    def exitFunction_def(self, ctx:smtlibParser.Function_defContext):
        pass


    # Enter a parse tree produced by smtlibParser#prop_literal.
    def enterProp_literal(self, ctx:smtlibParser.Prop_literalContext):
        pass

    # Exit a parse tree produced by smtlibParser#prop_literal.
    def exitProp_literal(self, ctx:smtlibParser.Prop_literalContext):
        pass


    # Enter a parse tree produced by smtlibParser#script.
    def enterScript(self, ctx:smtlibParser.ScriptContext):
        pass

    # Exit a parse tree produced by smtlibParser#script.
    def exitScript(self, ctx:smtlibParser.ScriptContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_assert.
    def enterCmd_assert(self, ctx:smtlibParser.Cmd_assertContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_assert.
    def exitCmd_assert(self, ctx:smtlibParser.Cmd_assertContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_checkSat.
    def enterCmd_checkSat(self, ctx:smtlibParser.Cmd_checkSatContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_checkSat.
    def exitCmd_checkSat(self, ctx:smtlibParser.Cmd_checkSatContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_checkSatAssuming.
    def enterCmd_checkSatAssuming(self, ctx:smtlibParser.Cmd_checkSatAssumingContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_checkSatAssuming.
    def exitCmd_checkSatAssuming(self, ctx:smtlibParser.Cmd_checkSatAssumingContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_declareConst.
    def enterCmd_declareConst(self, ctx:smtlibParser.Cmd_declareConstContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_declareConst.
    def exitCmd_declareConst(self, ctx:smtlibParser.Cmd_declareConstContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_declareDatatype.
    def enterCmd_declareDatatype(self, ctx:smtlibParser.Cmd_declareDatatypeContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_declareDatatype.
    def exitCmd_declareDatatype(self, ctx:smtlibParser.Cmd_declareDatatypeContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_declareDatatypes.
    def enterCmd_declareDatatypes(self, ctx:smtlibParser.Cmd_declareDatatypesContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_declareDatatypes.
    def exitCmd_declareDatatypes(self, ctx:smtlibParser.Cmd_declareDatatypesContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_declareFun.
    def enterCmd_declareFun(self, ctx:smtlibParser.Cmd_declareFunContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_declareFun.
    def exitCmd_declareFun(self, ctx:smtlibParser.Cmd_declareFunContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_declareSort.
    def enterCmd_declareSort(self, ctx:smtlibParser.Cmd_declareSortContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_declareSort.
    def exitCmd_declareSort(self, ctx:smtlibParser.Cmd_declareSortContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_defineFun.
    def enterCmd_defineFun(self, ctx:smtlibParser.Cmd_defineFunContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_defineFun.
    def exitCmd_defineFun(self, ctx:smtlibParser.Cmd_defineFunContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_defineFunRec.
    def enterCmd_defineFunRec(self, ctx:smtlibParser.Cmd_defineFunRecContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_defineFunRec.
    def exitCmd_defineFunRec(self, ctx:smtlibParser.Cmd_defineFunRecContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_defineFunsRec.
    def enterCmd_defineFunsRec(self, ctx:smtlibParser.Cmd_defineFunsRecContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_defineFunsRec.
    def exitCmd_defineFunsRec(self, ctx:smtlibParser.Cmd_defineFunsRecContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_defineSort.
    def enterCmd_defineSort(self, ctx:smtlibParser.Cmd_defineSortContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_defineSort.
    def exitCmd_defineSort(self, ctx:smtlibParser.Cmd_defineSortContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_echo.
    def enterCmd_echo(self, ctx:smtlibParser.Cmd_echoContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_echo.
    def exitCmd_echo(self, ctx:smtlibParser.Cmd_echoContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_exit.
    def enterCmd_exit(self, ctx:smtlibParser.Cmd_exitContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_exit.
    def exitCmd_exit(self, ctx:smtlibParser.Cmd_exitContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getAssertions.
    def enterCmd_getAssertions(self, ctx:smtlibParser.Cmd_getAssertionsContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getAssertions.
    def exitCmd_getAssertions(self, ctx:smtlibParser.Cmd_getAssertionsContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getAssignment.
    def enterCmd_getAssignment(self, ctx:smtlibParser.Cmd_getAssignmentContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getAssignment.
    def exitCmd_getAssignment(self, ctx:smtlibParser.Cmd_getAssignmentContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getInfo.
    def enterCmd_getInfo(self, ctx:smtlibParser.Cmd_getInfoContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getInfo.
    def exitCmd_getInfo(self, ctx:smtlibParser.Cmd_getInfoContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getModel.
    def enterCmd_getModel(self, ctx:smtlibParser.Cmd_getModelContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getModel.
    def exitCmd_getModel(self, ctx:smtlibParser.Cmd_getModelContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getOption.
    def enterCmd_getOption(self, ctx:smtlibParser.Cmd_getOptionContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getOption.
    def exitCmd_getOption(self, ctx:smtlibParser.Cmd_getOptionContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getProof.
    def enterCmd_getProof(self, ctx:smtlibParser.Cmd_getProofContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getProof.
    def exitCmd_getProof(self, ctx:smtlibParser.Cmd_getProofContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getUnsatAssumptions.
    def enterCmd_getUnsatAssumptions(self, ctx:smtlibParser.Cmd_getUnsatAssumptionsContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getUnsatAssumptions.
    def exitCmd_getUnsatAssumptions(self, ctx:smtlibParser.Cmd_getUnsatAssumptionsContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getUnsatCore.
    def enterCmd_getUnsatCore(self, ctx:smtlibParser.Cmd_getUnsatCoreContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getUnsatCore.
    def exitCmd_getUnsatCore(self, ctx:smtlibParser.Cmd_getUnsatCoreContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_getValue.
    def enterCmd_getValue(self, ctx:smtlibParser.Cmd_getValueContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_getValue.
    def exitCmd_getValue(self, ctx:smtlibParser.Cmd_getValueContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_pop.
    def enterCmd_pop(self, ctx:smtlibParser.Cmd_popContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_pop.
    def exitCmd_pop(self, ctx:smtlibParser.Cmd_popContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_push.
    def enterCmd_push(self, ctx:smtlibParser.Cmd_pushContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_push.
    def exitCmd_push(self, ctx:smtlibParser.Cmd_pushContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_reset.
    def enterCmd_reset(self, ctx:smtlibParser.Cmd_resetContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_reset.
    def exitCmd_reset(self, ctx:smtlibParser.Cmd_resetContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_resetAssertions.
    def enterCmd_resetAssertions(self, ctx:smtlibParser.Cmd_resetAssertionsContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_resetAssertions.
    def exitCmd_resetAssertions(self, ctx:smtlibParser.Cmd_resetAssertionsContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_setInfo.
    def enterCmd_setInfo(self, ctx:smtlibParser.Cmd_setInfoContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_setInfo.
    def exitCmd_setInfo(self, ctx:smtlibParser.Cmd_setInfoContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_setLogic.
    def enterCmd_setLogic(self, ctx:smtlibParser.Cmd_setLogicContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_setLogic.
    def exitCmd_setLogic(self, ctx:smtlibParser.Cmd_setLogicContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_setOption.
    def enterCmd_setOption(self, ctx:smtlibParser.Cmd_setOptionContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_setOption.
    def exitCmd_setOption(self, ctx:smtlibParser.Cmd_setOptionContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_weight.
    def enterCmd_weight(self, ctx:smtlibParser.Cmd_weightContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_weight.
    def exitCmd_weight(self, ctx:smtlibParser.Cmd_weightContext):
        pass


    # Enter a parse tree produced by smtlibParser#cmd_query.
    def enterCmd_query(self, ctx:smtlibParser.Cmd_queryContext):
        pass

    # Exit a parse tree produced by smtlibParser#cmd_query.
    def exitCmd_query(self, ctx:smtlibParser.Cmd_queryContext):
        pass


    # Enter a parse tree produced by smtlibParser#command.
    def enterCommand(self, ctx:smtlibParser.CommandContext):
        pass

    # Exit a parse tree produced by smtlibParser#command.
    def exitCommand(self, ctx:smtlibParser.CommandContext):
        pass


    # Enter a parse tree produced by smtlibParser#b_value.
    def enterB_value(self, ctx:smtlibParser.B_valueContext):
        pass

    # Exit a parse tree produced by smtlibParser#b_value.
    def exitB_value(self, ctx:smtlibParser.B_valueContext):
        pass


    # Enter a parse tree produced by smtlibParser#option.
    def enterOption(self, ctx:smtlibParser.OptionContext):
        pass

    # Exit a parse tree produced by smtlibParser#option.
    def exitOption(self, ctx:smtlibParser.OptionContext):
        pass


    # Enter a parse tree produced by smtlibParser#info_flag.
    def enterInfo_flag(self, ctx:smtlibParser.Info_flagContext):
        pass

    # Exit a parse tree produced by smtlibParser#info_flag.
    def exitInfo_flag(self, ctx:smtlibParser.Info_flagContext):
        pass


    # Enter a parse tree produced by smtlibParser#error_behaviour.
    def enterError_behaviour(self, ctx:smtlibParser.Error_behaviourContext):
        pass

    # Exit a parse tree produced by smtlibParser#error_behaviour.
    def exitError_behaviour(self, ctx:smtlibParser.Error_behaviourContext):
        pass


    # Enter a parse tree produced by smtlibParser#reason_unknown.
    def enterReason_unknown(self, ctx:smtlibParser.Reason_unknownContext):
        pass

    # Exit a parse tree produced by smtlibParser#reason_unknown.
    def exitReason_unknown(self, ctx:smtlibParser.Reason_unknownContext):
        pass


    # Enter a parse tree produced by smtlibParser#model_response.
    def enterModel_response(self, ctx:smtlibParser.Model_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#model_response.
    def exitModel_response(self, ctx:smtlibParser.Model_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#info_response.
    def enterInfo_response(self, ctx:smtlibParser.Info_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#info_response.
    def exitInfo_response(self, ctx:smtlibParser.Info_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#valuation_pair.
    def enterValuation_pair(self, ctx:smtlibParser.Valuation_pairContext):
        pass

    # Exit a parse tree produced by smtlibParser#valuation_pair.
    def exitValuation_pair(self, ctx:smtlibParser.Valuation_pairContext):
        pass


    # Enter a parse tree produced by smtlibParser#t_valuation_pair.
    def enterT_valuation_pair(self, ctx:smtlibParser.T_valuation_pairContext):
        pass

    # Exit a parse tree produced by smtlibParser#t_valuation_pair.
    def exitT_valuation_pair(self, ctx:smtlibParser.T_valuation_pairContext):
        pass


    # Enter a parse tree produced by smtlibParser#check_sat_response.
    def enterCheck_sat_response(self, ctx:smtlibParser.Check_sat_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#check_sat_response.
    def exitCheck_sat_response(self, ctx:smtlibParser.Check_sat_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#echo_response.
    def enterEcho_response(self, ctx:smtlibParser.Echo_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#echo_response.
    def exitEcho_response(self, ctx:smtlibParser.Echo_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_assertions_response.
    def enterGet_assertions_response(self, ctx:smtlibParser.Get_assertions_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_assertions_response.
    def exitGet_assertions_response(self, ctx:smtlibParser.Get_assertions_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_assignment_response.
    def enterGet_assignment_response(self, ctx:smtlibParser.Get_assignment_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_assignment_response.
    def exitGet_assignment_response(self, ctx:smtlibParser.Get_assignment_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_info_response.
    def enterGet_info_response(self, ctx:smtlibParser.Get_info_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_info_response.
    def exitGet_info_response(self, ctx:smtlibParser.Get_info_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_model_response.
    def enterGet_model_response(self, ctx:smtlibParser.Get_model_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_model_response.
    def exitGet_model_response(self, ctx:smtlibParser.Get_model_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_option_response.
    def enterGet_option_response(self, ctx:smtlibParser.Get_option_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_option_response.
    def exitGet_option_response(self, ctx:smtlibParser.Get_option_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_proof_response.
    def enterGet_proof_response(self, ctx:smtlibParser.Get_proof_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_proof_response.
    def exitGet_proof_response(self, ctx:smtlibParser.Get_proof_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_unsat_assump_response.
    def enterGet_unsat_assump_response(self, ctx:smtlibParser.Get_unsat_assump_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_unsat_assump_response.
    def exitGet_unsat_assump_response(self, ctx:smtlibParser.Get_unsat_assump_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_unsat_core_response.
    def enterGet_unsat_core_response(self, ctx:smtlibParser.Get_unsat_core_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_unsat_core_response.
    def exitGet_unsat_core_response(self, ctx:smtlibParser.Get_unsat_core_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#get_value_response.
    def enterGet_value_response(self, ctx:smtlibParser.Get_value_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#get_value_response.
    def exitGet_value_response(self, ctx:smtlibParser.Get_value_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#specific_success_response.
    def enterSpecific_success_response(self, ctx:smtlibParser.Specific_success_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#specific_success_response.
    def exitSpecific_success_response(self, ctx:smtlibParser.Specific_success_responseContext):
        pass


    # Enter a parse tree produced by smtlibParser#general_response.
    def enterGeneral_response(self, ctx:smtlibParser.General_responseContext):
        pass

    # Exit a parse tree produced by smtlibParser#general_response.
    def exitGeneral_response(self, ctx:smtlibParser.General_responseContext):
        pass


