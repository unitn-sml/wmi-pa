from abc import ABC, abstractmethod
from functools import reduce

from pysmt.rewritings import CNFizer, nnf
from pysmt.shortcuts import (
    And,
    Bool,
    Equals,
    FreshSymbol,
    FunctionType,
    Not,
    Or,
    Real,
    Times,
    get_env, )
from pysmt.simplifier import Simplifier
from pysmt.typing import REAL
from pysmt.walkers import IdentityDagWalker

from wmipa.utils import is_atom, is_pow, is_exp


class WeightConverter(ABC):
    def __init__(self, variables):
        self.variables = variables

    @abstractmethod
    def convert(self, weight_func):
        """Convert the weight function into a LRA formula

        Args:
            weight_func (FNode): The weight function

        Returns:
            FNode: The formula representing the weight function
        """
        pass


class WeightConverterEUF(WeightConverter):
    def __init__(self, variables):
        super().__init__(variables)
        self.conv_aliases = set()
        self.prod_fn = FreshSymbol(
            typename=FunctionType(REAL, (REAL, REAL)), template="PROD%s"
        )
        self.pow_fn = FreshSymbol(
            typename=FunctionType(REAL, (REAL, REAL)), template="POW%s"
        )
        self.exp_fn = FreshSymbol(
            typename=FunctionType(REAL, (REAL,)), template="EXP%s"
        )
        self.counter = 1

    def convert(self, weight_func):
        conversion_list = list()
        w, _ = self.convert_rec(weight_func, Bool(False), conversion_list)
        if not w.is_symbol():
            y = self.variables.new_weight_alias(len(self.conv_aliases))
            conversion_list.append(Equals(y, w))

        return And(conversion_list)

    def convert_rec(self, formula, branch_condition, conversion_list):

        if formula.is_ite():
            return self._process_ite(formula, branch_condition, conversion_list)
        elif formula.is_times():
            return self._process_times(formula, branch_condition, conversion_list)
        elif is_pow(formula):
            return self._process_pow(formula, branch_condition, conversion_list)
        elif is_exp(formula):
            return self._process_exp(formula, branch_condition, conversion_list)
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
                get_env().formula_manager.create_node(
                    node_type=formula.node_type(), args=tuple(new_children)
                ),
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
            f = self.variables.new_weight_alias(self.counter)
            e = Equals(left, f)
            self.counter += 1
            conversion_list.append(Or(branch_condition, e))
        if not r_has_cond:
            right = self.variables.new_weight_alias(len(self.conv_aliases))
            f = self.variables.new_weight_alias(self.counter)
            e = Equals(right, f)
            self.counter += 1
            conversion_list.append(Or(branch_condition, e))

        # add     (branch_conditions) -> (y = left) AND
        #     (not branch_conditions) -> (y = right)
        y = self.variables.new_weight_alias(len(self.conv_aliases))
        self.conv_aliases.add(y)
        el = Equals(y, left)
        er = Equals(y, right)
        conversion_list.append(Or(Or(branch_condition, Not(phi)), el))
        conversion_list.append(Or(Or(branch_condition, phi), er))
        # add      (branch_condition) -> not (y = left) OR not (y = right)
        # to force the enumeration of relevant branch conditions
        conversion_list.append(Or(branch_condition, Not(el), Not(er)))
        return y, True

    def _process_times(self, formula, branch_condition, conversion_list):
        args = (
            self.convert_rec(arg, branch_condition, conversion_list)
            for arg in formula.args()
        )
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
            return Times(const_val, reduce(self.prod_fn, others)), has_cond

    def _process_pow(self, formula, branch_condition, conversion_list):
        (base, b_has_cond) = self.convert_rec(formula.arg(0), branch_condition, conversion_list)
        (exponent, e_has_cond) = self.convert_rec(formula.arg(1), branch_condition, conversion_list)

        has_cond = b_has_cond or e_has_cond
        if exponent.is_zero():
            return Real(1), has_cond
        else:
            return self.pow_fn(base, exponent), has_cond

    def _process_exp(self, formula, branch_condition, conversion_list):
        exponent, has_cond = self.convert_rec(formula.arg(0), branch_condition, conversion_list)
        if exponent.is_zero():
            return Real(1), has_cond
        else:
            # expand power into product and abstract it with EUF
            return self.exp_fn(exponent), has_cond


class WeightConverterSkeleton(WeightConverter):
    def __init__(self, variables):
        super().__init__(variables)
        self.cnf_labels = set()
        self.cnfizer = LabelCNFizer(self.variables)

    def new_label(self):
        B = self.variables.new_cond_label(len(self.cnf_labels))
        self.cnf_labels.add(B)
        return B

    def convert(self, weight_func):
        conversion_list = list()
        self._convert_rec(weight_func, Bool(False), conversion_list)
        return And(conversion_list)

    def _convert_rec(self, formula, branch_condition, conversion_list):
        if formula.is_ite():
            return self._process_ite(formula, branch_condition, conversion_list)
        elif formula.is_theory_op():
            for arg in formula.args():
                self._convert_rec(arg, branch_condition, conversion_list)

    def _process_ite(self, formula, branch_condition, conversion_list):
        phi, left, right = formula.args()
        if is_atom(phi):
            if branch_condition is not None:
                l_cond = Or(branch_condition, Not(phi))
                r_cond = Or(branch_condition, phi)
            else:
                l_cond = Not(phi)
                r_cond = phi
            conversion_list.append(Or(branch_condition, phi, Not(phi)))
            self._convert_rec(left, l_cond, conversion_list)
            self._convert_rec(right, r_cond, conversion_list)
        else:
            b = self.new_label()
            if branch_condition is not None:
                l_cond = Or(branch_condition, Not(b))
                r_cond = Or(branch_condition, b)
            else:
                l_cond = Not(b)
                r_cond = b
            for clause in self.cnfizer.convert(nnf(phi)):
                conversion_list.append(Or(l_cond, *clause))

            for clause in self.cnfizer.convert(nnf(Not(phi))):
                conversion_list.append(Or(r_cond, *clause))

            conversion_list.append(Or(branch_condition, b, Not(b)))

            self._convert_rec(left, l_cond, conversion_list)
            self._convert_rec(right, r_cond, conversion_list)


class CNFPreprocessor(IdentityDagWalker):
    """
    Convert nested ORs and ANDs into flat lists of ORs and ANDs.
    """

    def walk_or(self, formula, args, **kwargs):
        children = []
        for arg in args:
            if arg.is_true():
                return self.mgr.Bool(True)
            elif arg.is_false():
                continue
            elif arg.is_or():
                children.extend(arg.args())
            elif arg.is_not() and arg.arg(0).is_and():
                children.extend(map(self.mgr.Not, arg.arg(0).args()))
            else:
                children.append(arg)
        return self.mgr.Or(children)

    def walk_and(self, formula, args, **kwargs):
        children = []
        for arg in args:
            if arg.is_false():
                return self.mgr.Bool(False)
            elif arg.is_true():
                continue
            elif arg.is_and():
                children.extend(arg.args())
            elif arg.is_not() and arg.arg(0).is_or():
                children.extend(map(self.mgr.Not, arg.arg(0).args()))
            else:
                children.append(arg)
        return self.mgr.And(children)

    def walk_implies(self, formula, args, **kwargs):
        left, right = formula.args()
        left_a, right_a = args
        return self.walk_or(self.mgr.Or(self.mgr.Not(left), right), (self.mgr.Not(left_a), right_a), **kwargs)


class LabelCNFizer(CNFizer):
    def walk_quantifier(self, formula, args, **kwargs):
        pass

    def __init__(self, wmi_variables, environment=None):
        super().__init__(environment)
        self.preprocessor = CNFPreprocessor(env=environment)
        self.wmi_variables = wmi_variables

    def _key_var(self, formula):
        if formula in self._introduced_variables:
            res = self._introduced_variables[formula]
        else:
            res = self.wmi_variables.new_cnf_label(len(self._introduced_variables))
            self._introduced_variables[formula] = res
        return res

    def convert(self, formula):
        """Convert formula into an equisatisfiable CNF.

        Returns a set of clauses: a set of sets of literals.
        """

        formula = self.preprocessor.walk(formula)
        tl, _cnf = self.walk(formula)

        if not _cnf:
            return [frozenset([tl])]
        res = []
        for clause in _cnf:
            if len(clause) == 0:
                return CNFizer.FALSE_CNF
            simp = []
            for lit in clause:
                if lit is tl or lit.is_true():
                    # Prune clauses that are trivially TRUE
                    # and clauses containing the top level label
                    simp = None
                    break
                elif not lit.is_false() and lit is not Not(tl):
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(frozenset(simp))

        return frozenset(res)

    def walk_not(self, formula, args, **kwargs):
        a, _cnf = args[0]
        if a.is_true():
            return self.mgr.Bool(False), CNFizer.TRUE_CNF
        elif a.is_false():
            return self.mgr.Bool(True), CNFizer.TRUE_CNF
        else:
            return Not(a), _cnf

    def walk_and(self, formula, args, **kwargs):
        if len(args) == 1:
            return args[0]

        k = self._key_var(formula)

        _cnf = []
        for a, c in args:
            _cnf.append(frozenset([a, self.mgr.Not(k)]))
            for clause in c:
                _cnf.append(clause)

        return k, frozenset(_cnf)

    def walk_or(self, formula, args, **kwargs):
        if len(args) == 1:
            return args[0]
        k = self._key_var(formula)

        _cnf = [frozenset([self.mgr.Not(k)] + [a for a, _ in args])]
        for a, c in args:
            for clause in c:
                _cnf.append(clause)

        return k, frozenset(_cnf)


class SkeletonSimplifier(Simplifier):
    """Simplifier that does not simplify formulas like Or(phi, Not(phi))"""

    def walk_or(self, formula, args, **kwargs):
        if len(args) == 2 and args[0] == args[1]:
            return args[0]

        new_args = set()
        for a in args:
            if a.is_false():
                continue
            if a.is_true():
                return self.manager.TRUE()
            if a.is_or():
                for s in a.args():
                    new_args.add(s)
            else:
                new_args.add(a)

        if len(new_args) == 0:
            return self.manager.FALSE()
        elif len(new_args) == 1:
            return next(iter(new_args))
        else:
            return self.manager.Or(new_args)
