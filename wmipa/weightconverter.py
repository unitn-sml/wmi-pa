from abc import ABC, abstractmethod

from pysmt.shortcuts import REAL, And, Bool, Equals, FreshSymbol, FunctionType, Not, Or, Real, Times, get_env, get_type

from wmipa.utils import is_pow


class WeightConverter(ABC):
    def __init__(self, variables):
        self.variables = variables

    @abstractmethod
    def convert(self, weight_func, mode):
        """Convert the weight function into a LRA formula

        Args:
            weight_func (FNode): The weight function

        Returns:
            FNode: The formula representing the weight function
        """
        pass


class WeightConverterEUForiginal(WeightConverter):
    def __init__(self, variables):
        super().__init__(variables)
        self.conv_aliases = set()
        self.prod_fn = FreshSymbol(typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s")
        self.counter = 1

    def convert(self, weight_func):
        conversion_list = list()
        w = self.convert_rec(weight_func, Bool(False), conversion_list)
        if not w.is_symbol():
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            conversion_list.append(Equals(y, w))
            w = y
        return And(conversion_list)

    def convert_rec(self, formula, branch_condition, conversion_list):
        if get_type(formula) == REAL:
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            f = self.variables.new_EUF_alias(self.counter)
            # e = Equals(y, Real(self.counter))
            e = Equals(y, f)
            self.counter += 1
            conversion_list.append(Or(branch_condition, e))
            return y
        elif formula.is_ite():
            return self._process_ite(formula, branch_condition, conversion_list)
        elif formula.is_times():
            return self._process_times(formula, branch_condition, conversion_list)
        elif is_pow(formula):
            return self._process_pow(formula, branch_condition, conversion_list)
        elif len(formula.args()) == 0:
            return formula
        else:
            new_children = (self.convert_rec(arg, branch_condition, conversion_list) for arg in formula.args())
            return get_env().formula_manager.create_node(node_type=formula.node_type(), args=tuple(new_children))

    def _process_ite(self, formula, branch_condition, conversion_list):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Or(branch_condition, Not(phi))
        r_cond = Or(branch_condition, phi)
        left = self.convert_rec(left, l_cond, conversion_list)
        right = self.convert_rec(right, r_cond, conversion_list)

        # print("NOW DOING ITE", formula)

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

    def _process_times(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec(arg, branch_condition, conversion_list) for arg in formula.args())
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
            return Times(const_val, self._prod(others))

    def _process_pow(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec(arg, branch_condition, conversion_list) for arg in formula.args())
        base, exponent = args
        if exponent.is_zero():
            return Real(1)
        else:
            # expand power into product and abstract it with EUF
            n, d = (
                exponent.constant_value().numerator,
                exponent.constant_value().denominator,
            )
            return self._prod([base for _ in range(n // d)])

    def _prod(self, args):
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


class WeightConverterEUF(WeightConverter):
    def __init__(self, variables):
        super().__init__(variables)
        self.conv_aliases = set()
        self.prod_fn = FreshSymbol(typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s")
        self.counter = 1

    def convert(self, weight_func):
        conversion_list = list()
        w, _ = self.convert_rec(weight_func, Bool(False), conversion_list)
        if not w.is_symbol():
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            conversion_list.append(Equals(y, w))
            w = y
        return And(conversion_list)

    def convert_rec(self, formula, branch_condition, conversion_list):
        # print("CONVERT", formula, get_type(formula))
        if formula.is_ite():
            return self._process_ite(formula, branch_condition, conversion_list)
        elif formula.is_times():
            return self._process_times(formula, branch_condition, conversion_list)
        elif is_pow(formula):
            return self._process_pow(formula, branch_condition, conversion_list)
        elif len(formula.args()) == 0:
            return formula, False
        else:
            has_cond = False
            new_children = []
            for arg in formula.args():
                child, cond = self.convert_rec(arg, branch_condition, conversion_list)
                has_cond = has_cond or cond
                new_children.append(child)
            return (
                get_env().formula_manager.create_node(node_type=formula.node_type(), args=tuple(new_children)),
                has_cond,
            )

    def _process_ite(self, formula, branch_condition, conversion_list):
        phi, left, right = formula.args()
        # update branch conditions for children and recursively convert them
        l_cond = Or(branch_condition, Not(phi))
        r_cond = Or(branch_condition, phi)
        left, l_has_cond = self.convert_rec(left, l_cond, conversion_list)
        right, r_has_cond = self.convert_rec(right, r_cond, conversion_list)

        if not l_has_cond:
            left = self.variables.new_weight_alias(len(self.conv_aliases))
            f = self.variables.new_EUF_alias(self.counter)
            e = Equals(left, f)
            self.counter += 1
            conversion_list.append(Or(branch_condition, e))
        if not r_has_cond:
            right = self.variables.new_weight_alias(len(self.conv_aliases))
            f = self.variables.new_EUF_alias(self.counter)
            e = Equals(right, f)
            self.counter += 1
            conversion_list.append(Or(branch_condition, e))

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
        return y, True

    def _process_times(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec(arg, branch_condition, conversion_list) for arg in formula.args())
        const_val = 1
        others = []
        has_cond = False
        for arg, cond in args:
            has_cond = has_cond or cond
            if arg.is_real_constant():
                const_val *= arg.constant_value()
            else:
                others.append(arg)
        const_val = Real(const_val)
        if not others:
            return const_val, has_cond
        else:
            # abstract product between non-constant nodes with EUF
            return Times(const_val, self._prod(others)), has_cond

    def _process_pow(self, formula, branch_condition, conversion_list):
        args = (self.convert_rec(arg, branch_condition, conversion_list) for arg in formula.args())
        (base, _), (exponent, _) = args
        if exponent.is_zero():
            return Real(1), False
        else:
            # expand power into product and abstract it with EUF
            n, d = (
                exponent.constant_value().numerator,
                exponent.constant_value().denominator,
            )
            return self._prod([base for _ in range(n // d)]), False

    def _prod(self, args):
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
