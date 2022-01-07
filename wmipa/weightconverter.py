from pysmt.shortcuts import *
from wmipa.utils import is_pow


class WeightConverter:
    def __init__(self, variables):
        self.variables = variables
        self.conv_labels = set()
        self.conversion_list = list()
        self.prod_fn = FreshSymbol(typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s")

    def convert(self, weight_func):
        """Convert the weight function into a LRA formula

        Args:
            weight_func (FNode): The weight function

        Returns:
            FNode: The formula representing the weight function
        """
        w = self.convert_rec(
            weight_func, branch_condition=None)
        if not w.is_symbol():
            y = self.variables.new_weight_label(len(self.conv_labels))
            self.conversion_list.append(Equals(y, w))
            w = y 
        return And(self.conversion_list)

    def convert_rec(self, formula, branch_condition):
        if formula.is_ite():
            return self._process_ite(formula, branch_condition)
        elif formula.is_times():
            return self._process_times(formula, branch_condition)
        elif is_pow(formula):
            return self._process_pow(formula, branch_condition)
        elif len(formula.args()) == 0:
            return formula
        else:
            new_children = (self.convert_rec(arg, branch_condition) for arg in formula.args())
            return get_env().formula_manager.create_node(
                node_type=formula.node_type(), args=tuple(new_children))

    def _process_ite(self, formula, branch_condition):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Not(phi)
        r_cond = phi
        if branch_condition is not None:
            l_cond = Or(branch_condition, l_cond)
            r_cond = Or(branch_condition, r_cond)
        left = self.convert_rec(left, l_cond)
        right = self.convert_rec(right, r_cond)

        # add (    branch_conditions) -> y = left
        # and (not branch_conditions) -> y = right
        y = self.variables.new_weight_label(len(self.conv_labels))
        self.conv_labels.add(y)
        el = Equals(y, left)
        er = Equals(y, right)
        ops = [] if branch_condition is None else [branch_condition]
        self.conversion_list.append(Or(Or(*ops, Not(phi)), el))
        self.conversion_list.append(Or(Or(*ops, phi), er))
        # add also branch_condition -> (not y = left) or (not y = right)
        # to force the enumeration of relevant branch conditions
        self.conversion_list.append(Or(*ops, Not(el), Not(er)))
        return y

    def _process_times(self, formula, branch_condition):
        args = (self.convert_rec(arg, branch_condition) for arg in formula.args())
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

    def _process_pow(self, formula, branch_condition):
        args = (self.convert_rec(arg, branch_condition) for arg in formula.args())
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


