# import pysmt.operators as op
# from pysmt.walkers.generic import handles
import pysmt.walkers
from pysmt.shortcuts import *


class WeightConverter(pysmt.walkers.IdentityDagWalker):
    def __init__(self, variables, *args):
        super().__init__(*args)
        self.variables = variables
        self.conv_labels = set()
        self.prod_fn = FreshSymbol(typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s")

    def convert(self, weight_func):
        conversion_list = list()
        w = self.walk(
            weight_func, conversion_list=conversion_list)
        if not w.is_symbol():
            y = self.variables.new_weight_label(len(self.conv_labels))
            conversion_list.append(Equals(y, w))
            w = y 

        return And(conversion_list)

    def _process_stack(self, **kwargs):
        """Empties the stack by processing every node in it.

        Processing is performed in two steps.
        1- A node is expanded and all its children are push to the stack
        2- Once all children have been processed, the result for the node
           is computed and memoized.
        """
        while self.stack:
            # pop three items
            (was_expanded, formula, branch_condition) = self.stack.pop()
            if was_expanded:
                self._compute_node_result(
                    formula, branch_condition=branch_condition, **kwargs)
            else:
                self._push_with_children_to_stack(
                    formula, branch_condition, **kwargs)

    def _push_with_children_to_stack(self, formula, branch_condition, **kwargs):
        """Push children on the stack.
        The children are given the branch condition of the parent, that is the negated
        conjunction of the Ite branches taken.
        """
        if formula.is_ite():
            # Need to process it also in pre-order to pass branch condition to children
            phi, left, right = self._get_children(formula)
            self.stack.append((True, formula, branch_condition))
            self.stack.append((True, phi, branch_condition))
            self.memoization[phi] = phi

            l_cond = Not(phi)
            r_cond = phi
            if branch_condition is not None:
                l_cond = Or(branch_condition, l_cond)
                r_cond = Or(branch_condition, r_cond)
            # not need to visit phi
            l_key = self._get_key(left, branch_condition=l_cond, **kwargs)
            r_key = self._get_key(right, branch_condition=r_cond, **kwargs)

            if l_key not in self.memoization:
                self.stack.append((False, left, l_cond))
            if r_key not in self.memoization:
                self.stack.append((False, right, r_cond))
        else:
            # normal processing, just push also the branch_condition
            self.stack.append((True, formula, branch_condition))
            for s in self._get_children(formula):
                # Add only if not memoized already
                key = self._get_key(s, **kwargs)
                if key not in self.memoization:
                    self.stack.append((False, s, branch_condition))

    def iter_walk(self, formula, **kwargs):
        """Performs an iterative walk of the DAG"""
        self.stack.append((False, formula, None))
        self._process_stack(**kwargs)
        res_key = self._get_key(formula, **kwargs)
        return self.memoization[res_key]

    def walk_ite(self, formula, args, branch_condition=None, conversion_list=None):
        phi, left, right = args
        y = self.variables.new_weight_label(len(self.conv_labels))
        self.conv_labels.add(y)
        ops = [] if branch_condition is None else [branch_condition]
        conversion_list.append(Or(Or(*ops, phi), Equals(y, right)))
        conversion_list.append(Or(Or(*ops, Not(phi)), Equals(y, left)))
        return y

    def walk_times(self, formula, args, **kwargs):
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
            return Times(const_val, self.prod_euf(others))

    def walk_pow(self, formula, args, **kwargs):
        base, exponent = args
        if exponent.is_zero():
            return Real(1)
        else:
            n, d = exponent.constant_value().numerator, exponent.constant_value().denominator
            # print(n, d, n//d)
            return self.prod_euf([base for _ in range(n // d)])

    def _get_key(self, formula, **kwargs):
        return formula

    def prod_euf(self, args):
        assert isinstance(args, list)
        if len(args) == 1:
            return args.pop()
        curr = args.pop()
        while args:
            curr = self.prod_fn(args.pop(), curr)
        return curr


