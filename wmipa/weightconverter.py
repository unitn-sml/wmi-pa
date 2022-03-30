from itertools import islice, product
from pysmt.shortcuts import *
from wmipa.utils import is_pow
from pysmt.walkers import IdentityDagWalker
from pysmt.rewritings import nnf
from pysmt.fnode import FNode


class WeightConverter:
    MODE_EUF = "euf"
    MODE_BOOL = "bool"
    MODE_SK = "sk"
    MODES = [MODE_EUF, MODE_SK, MODE_BOOL]

    def __init__(self, variables):
        self.variables = variables
        self.conv_aliases = set()
        self.conv_bools = set()
        self.prod_fn = FreshSymbol(typename=FunctionType(
            REAL, (REAL, REAL)), template="PROD%s")

    def convert(self, weight_func, mode):
        """Convert the weight function into a LRA formula

        Args:
            weight_func (FNode): The weight function

        Returns:
            FNode: The formula representing the weight function
        """
        assert mode in WeightConverter.MODES, "Available modes: {}".format(
            WeightConverter.MODES)
        formula = Bool(True)
        # expand_cnf = False
        if mode == WeightConverter.MODE_EUF:
            formula = self.convert_euf(weight_func)
        elif mode == WeightConverter.MODE_BOOL:
            formula = self.convert_bool(weight_func)
            # expand_cnf = True
        elif mode == WeightConverter.MODE_SK:
            formula = self.convert_sk(weight_func)

        # if expand_cnf:
        #     # print("Conversion:", formula.serialize())
        #     formula = self.cnfizer.convert(formula)
            # print("CNF:", formula.serialize())
        return formula

    def convert_euf(self, weight_func):
        conversion_list = list()
        w = self.convert_rec_euf(weight_func, Bool(False), conversion_list)
        if not w.is_symbol():
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            conversion_list.append(Equals(y, w))
            w = y
        return And(conversion_list)

    def convert_rec_euf(self, formula, branch_condition, conversion_list):
        if formula.is_ite():
            return self._process_ite_euf(formula, branch_condition, conversion_list)
        elif formula.is_times():
            return self._process_times_euf(formula, branch_condition, conversion_list)
        elif is_pow(formula):
            return self._process_pow_euf(formula, branch_condition, conversion_list)
        elif len(formula.args()) == 0:
            return formula
        else:
            new_children = (self.convert_rec_euf(
                arg, branch_condition, conversion_list) for arg in formula.args())
            return get_env().formula_manager.create_node(
                node_type=formula.node_type(), args=tuple(new_children))

    def _process_ite_euf(self, formula, branch_condition, conversion_list):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Or(branch_condition, Not(phi))
        r_cond = Or(branch_condition, phi)
        left = self.convert_rec_euf(left, l_cond, conversion_list)
        right = self.convert_rec_euf(right, r_cond, conversion_list)

        # add (    branch_conditions) -> y = left
        # and (not branch_conditions) -> y = right
        y = self.variables.new_weight_alias(len(self.conv_aliases))
        self.conv_aliases.add(y)
        el = Equals(y, left)
        er = Equals(y, right)
        conversion_list.append(Or(Or(branch_condition, Not(phi)), el))
        conversion_list.append(Or(Or(branch_condition, phi), er))
        # add also branch_condition -> (not y = left) or (not y = right)
        # to force the enumeration of relevant branch conditions
        conversion_list.append(Or(branch_condition, Not(el), Not(er)))
        return y

    def _process_times_euf(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec_euf(arg, branch_condition, conversion_list)
                for arg in formula.args())
        const_val = 1
        others = []
        for arg in args:
            if arg.is_real_constant():
                const_val *= arg.constant_value()
            else:
                others.append(arg)
        const_val = Real(const_val)
        if not others:
            return const_val
        else:
            # abstract product between non-constant nodes with EUF
            return Times(const_val, self._prod_euf(others))

    def _process_pow_euf(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec_euf(arg, branch_condition, conversion_list)
                for arg in formula.args())
        base, exponent = args
        if exponent.is_zero():
            return Real(1)
        else:
            # expand power into product and abstract it with EUF
            n, d = exponent.constant_value().numerator, exponent.constant_value().denominator
            return self._prod_euf([base for _ in range(n // d)])

    def _prod_euf(self, args):
        """Abstract the product between args with EUF

        Args:
            args (list(FNode)): List of nodes to multiply. The list is emptied

        Returns:
            FNode: node representing abstracted product
        """
        assert isinstance(args, list)
        if len(args) == 1:
            return args.pop()
        curr = args.pop()
        while args:
            curr = self.prod_fn(args.pop(), curr)
        return curr

    def convert_sk(self, formula: FNode):
        if formula.is_ite():
            return self._process_ite_sk(formula)
        elif formula.is_theory_op():
            results = (s for a in formula.args() if not (
                s := self.convert_sk(a)).is_true())
            return And(results)
        else:
            return TRUE()

    def _process_ite_sk(self, formula):
        phi, left, right = formula.args()

        skl = self.convert_sk(left)
        skr = self.convert_sk(right)
        if skl.is_true() and skr.is_true():
            C = self.variables.new_weight_bool(len(self.conv_bools))
            self.conv_bools.add(C)
            skl = C
            skr = Not(C)
        return Or(And(phi, skl), And(Not(phi), skr))

    def convert_bool(self, weight_func):
        conversion_list = list()
        self._convert_rec_bool(weight_func, Bool(False), conversion_list)
        return And(conversion_list)

    def _convert_rec_bool(self, formula, branch_condition, conversion_list):
        if formula.is_ite():
            return self._process_ite_bool(formula, branch_condition, conversion_list)
        else:
            for arg in formula.args():
                self._convert_rec_bool(arg, branch_condition, conversion_list)

    def _process_ite_bool(self, formula, branch_condition, conversion_list):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        w = self.variables.new_weight_bool(len(self.conv_bools))
        self.conv_bools.add(w)
        conversion_list.append(Or(branch_condition, Not(w), phi))
        conversion_list.append(Or(branch_condition, w, Not(phi)))
        l_cond = Or(branch_condition, Not(w))
        r_cond = Or(branch_condition, w)
        self._convert_rec_bool(left, l_cond, conversion_list)
        self._convert_rec_bool(right, r_cond, conversion_list)


# class DeMorganCNFizer(IdentityDagWalker):
#     def convert(self, formula):
#         # convert in Negative Normal Form
#         formula = nnf(formula)
#         # print("NNF:", formula.serialize())
#         formula = self.walk(formula)
#         assert self.is_cnf(formula), formula.serialize()
#         return formula

#     def is_atom(self, node):
#         return node.is_symbol(BOOL) or node.is_theory_relation()

#     def is_literal(self, node):
#         return self.is_atom(node) or (node.is_not() and self.is_atom(node.arg(0)))

#     def walk_and(self, formula, args, **kwargs):
#         # print("Walking and: ", formula.serialize(), "args: ", args)

#         and_args = set()
#         for a in args:
#             if a.is_true():
#                 continue
#             elif a.is_false():
#                 return FALSE()
#             elif self.is_literal(a) or a.is_or():
#                 and_args.add(a)
#             else:
#                 assert a.is_and(), "{} {}".format(formula.serialize(), a.serialize())
#                 # flatten AND
#                 and_args.update(a.args())
#         # print("Returning", And(and_args).serialize())
#         return And(and_args)

#     def walk_or(self, formula, args, **kwargs):
#         # print("Walking or: ", formula.serialize(), "args: ", args)
#         # flatten or
#         or_literals = set()
#         list_of_and = list()
#         for a in args:
#             if a.is_false():
#                 continue
#             elif a.is_true():
#                 return TRUE()
#             elif self.is_literal(a):
#                 or_literals.add(a)
#             elif a.is_or():
#                 or_literals.update(a.args())
#             else:
#                 assert a.is_and(), "{} {}".format(formula.serialize(), a.serialize())
#                 list_of_and.append(a.args())

#         list_of_and.extend((x,) for x in or_literals)
#         # print("Flatten_args:", list_of_and)
#         and_args = set()

#         for comb in product(*list_of_and):
#             # print("Comb:", comb)
#             or_args = set()
#             for item in comb:
#                 if self.is_literal(item):
#                     or_args.add(item)
#                 elif item.is_or():
#                     or_args.update(item.args())
#                 else:
#                     assert item.is_and(), "{}".format(item.serialize())
#                     or_args.update(item.args())
#             and_args.add(Or(or_args))
#         # print("Returning", And(and_args).serialize())

#         return And(and_args)

#     def is_clause(self, formula):
#         return self.is_literal(formula) or (formula.is_or() and all(self.is_literal(l) for l in formula.args()))

#     def is_cnf(self, formula):
#         return self.is_clause(formula) or (formula.is_and() and all(self.is_clause(c) for c in formula.args()))
