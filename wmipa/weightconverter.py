from itertools import product
from pysmt.shortcuts import *
from wmipa.utils import is_pow
from pysmt.walkers import IdentityDagWalker
from pysmt.rewritings import nnf

class WeightConverter:
    MODE_EUF = "euf"
    MODE_BOOL = "bool"
    MODE_SK = "sk"
    MODES = [MODE_EUF, MODE_SK, MODE_BOOL]

    def __init__(self, variables):
        self.cnfizer = DeMorganCNFizer()
        self.variables = variables
        self.conv_aliases = set()
        self.conv_bools = set()
        self.conversion_list = list()
        self.prod_fn = FreshSymbol(typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s")

    def convert(self, weight_func, mode, expand_cnf=True):
        """Convert the weight function into a LRA formula

        Args:
            weight_func (FNode): The weight function

        Returns:
            FNode: The formula representing the weight function
        """
        assert mode in WeightConverter.MODES, "Available modes: {}".format(WeightConverter.MODES)
        formula = Bool(True)
        if mode == WeightConverter.MODE_EUF:
            formula = self.convert_euf(weight_func)
        elif mode == WeightConverter.MODE_BOOL:
            formula = self.convert_bool(weight_func)
        elif mode == WeightConverter.MODE_SK:
            formula = self.convert_sk(weight_func)
        
        if expand_cnf:
            formula = self.cnfizer.convert(formula)
        # print("Conversion:", formula.serialize())
        # print("CNF:", cnf.serialize())
        return formula

    def convert_euf(self, weight_func):
        self.conversion_list = list()
        w = self.convert_rec_euf(
            weight_func, branch_condition=None)
        if not w.is_symbol():
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            self.conversion_list.append(Equals(y, w))
            w = y 
        return And(self.conversion_list)

    def convert_rec_euf(self, formula, branch_condition):
        if formula.is_ite():
            return self._process_ite_euf(formula, branch_condition)
        elif formula.is_times():
            return self._process_times_euf(formula, branch_condition)
        elif is_pow(formula):
            return self._process_pow_euf(formula, branch_condition)
        elif len(formula.args()) == 0:
            return formula
        else:
            new_children = (self.convert_rec_euf(arg, branch_condition) for arg in formula.args())
            return get_env().formula_manager.create_node(
                node_type=formula.node_type(), args=tuple(new_children))

    def _process_ite_euf(self, formula, branch_condition):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Not(phi)
        r_cond = phi
        if branch_condition is not None:
            l_cond = Or(branch_condition, l_cond)
            r_cond = Or(branch_condition, r_cond)
        left = self.convert_rec_euf(left, l_cond)
        right = self.convert_rec_euf(right, r_cond)

        # add (    branch_conditions) -> y = left
        # and (not branch_conditions) -> y = right
        y = self.variables.new_weight_alias(len(self.conv_aliases))
        self.conv_aliases.add(y)
        el = Equals(y, left)
        er = Equals(y, right)
        ops = [] if branch_condition is None else [branch_condition]
        self.conversion_list.append(Or(Or(*ops, Not(phi)), el))
        self.conversion_list.append(Or(Or(*ops, phi), er))
        # add also branch_condition -> (not y = left) or (not y = right)
        # to force the enumeration of relevant branch conditions
        self.conversion_list.append(Or(*ops, Not(el), Not(er)))
        return y

    def _process_times_euf(self, formula, branch_condition):
        args = (self.convert_rec_euf(arg, branch_condition) for arg in formula.args())
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

    def _process_pow_euf(self, formula, branch_condition):
        args = (self.convert_rec_euf(arg, branch_condition) for arg in formula.args())
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


    def convert_sk(self, weight_func):
        self.conversion_list = list()
        self._convert_rec_sk(weight_func, None)
        return And(self.conversion_list)

    def _convert_rec_sk(self, formula, branch_condition):
        if formula.is_ite():
            return self._process_ite_sk(formula, branch_condition)
        else:
            for arg in formula.args():
                self._convert_rec_sk(arg, branch_condition)

    def _process_ite_sk(self, formula, branch_condition):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Not(phi)
        r_cond = phi
        if branch_condition is not None:
            l_cond = Or(branch_condition, l_cond)
            r_cond = Or(branch_condition, r_cond)
        self._convert_rec_sk(left, l_cond)
        self._convert_rec_sk(right, r_cond)

        ops = [] if branch_condition is None else [branch_condition]
        self.conversion_list.append(Or(*ops, phi, Not(phi)))

    def convert_bool(self, weight_func):
        self.conversion_list = list()
        self._convert_rec_bool(weight_func, None)
        return And(self.conversion_list)

    def _convert_rec_bool(self, formula, branch_condition):
        if formula.is_ite():
            return self._process_ite_bool(formula, branch_condition)
        else:
            for arg in formula.args():
                self._convert_rec_bool(arg, branch_condition)
    
    def _process_ite_bool(self, formula, branch_condition):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Not(phi)
        r_cond = phi
        if branch_condition is not None:
            l_cond = Or(branch_condition, l_cond)
            r_cond = Or(branch_condition, r_cond)
        self._convert_rec_bool(left, l_cond)
        self._convert_rec_bool(right, r_cond)

        w = self.variables.new_weight_bool(len(self.conv_bools))
        self.conv_bools.add(w)
        el = w
        er = Not(w)
        ops = [] if branch_condition is None else [branch_condition]
        self.conversion_list.append(Or(Or(*ops, Not(phi)), el))
        self.conversion_list.append(Or(Or(*ops, phi), er))


class DeMorganCNFizer(IdentityDagWalker):
    def convert(self, formula):
        # convert in Negative Normal Form
        formula = nnf(formula)
        # print("NNF:", formula.serialize())
        return self.walk(formula)

    def is_atom(self, node):
        return node.is_constant(BOOL) or node.is_symbol(BOOL) or node.is_theory_relation()

    def is_literal(self, node):
        return self.is_atom(node) or (node.is_not() and self.is_atom(node.arg(0)))

    def walk_and(self, formula, args, **kwargs):
        # print("Walking and: ", formula.serialize(), "args: ", args)
        
        and_args = set()
        for a in args:
            if self.is_literal(a) or a.is_or():
                and_args.add(a)
            else:
                assert a.is_and(), "{} {}".format(formula.serialize(), a.serialize())
                # flatten AND
                and_args.update(a.args())
        # print("Returning", And(and_args).serialize())
        return And(and_args)
    
    def walk_or(self, formula, args, **kwargs):
        # print("Walking or: ", formula.serialize(), "args: ", args)
        # flatten or
        or_literals = set()
        list_of_and = list()
        for a in args:
            if self.is_literal(a):
                or_literals.add(a)
            elif a.is_or():
                or_literals.update(a.args())
            else:
                assert a.is_and(), "{} {}".format(formula.serialize(), a.serialize())
                list_of_and.append(a.args())
                
        list_of_and.extend((x,) for x in or_literals)
        # print("Flatten_args:", list_of_and)
        and_args = set()
        
        for comb in product(*list_of_and):
            # print("Comb:", comb)
            or_args = set()
            for item in comb:
                if self.is_literal(item):
                    or_args.add(item)
                elif item.is_or():
                    or_args.update(item.args())
                else:
                    assert item.is_and(), "{}".format(item.serialize())
                    or_args.update(item.args())
            and_args.add(Or(or_args))
        # print("Returning", And(and_args).serialize())

        return And(and_args)
