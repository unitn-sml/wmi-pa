from abc import ABC, abstractmethod

import pysmt.operators as op
from pysmt.rewritings import nnf
from pysmt.shortcuts import And, Bool, Not, Or
from pysmt.walkers import IdentityDagWalker, handles, DagWalker

from wmipa.utils import is_atom


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

            # Trick to force the splitting on phi on the current branch represented by branch_condition
            # (here branch_condition is Not(conds)).
            # In the original algorithm, we would have added:
            #   (conds -> (phi v not phi)).
            # This would require a custom MathSAT version to avoid the simplification of the valid clause.
            #
            # Here, instead, we add:
            #   (conds -> exists k.CNF(phi <-> k))
            # which is equivalent to the above approach, but does not get simplified and does not require
            # using a custom MathSAT version.
            # (k is implicitly existentially quantified since we do not enumerate on it)
            k = self.new_label()
            conversion_list.append(Or(branch_condition, Not(k), phi))
            conversion_list.append(Or(branch_condition, k, Not(phi)))
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

            # Here we are not adding the clause
            #   (branch_condition -> (b v not b))
            # since it is subsumed by the CNF clauses of
            #   (branch_condition -> exists b.CNF(b <-> phi))
            self._convert_rec(left, l_cond, conversion_list)
            self._convert_rec(right, r_cond, conversion_list)


class CNFPreprocessor(IdentityDagWalker):
    """
    Convert nested ORs and ANDs into flat lists of ORs and ANDs, and Implies into Or.
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


class LabelCNFizer(DagWalker):
    """Implements the Plaisted&Greenbaum CNF conversion algorithm."""

    def __init__(self, wmi_variables, environment=None):
        super().__init__(environment, invalidate_memoization=True)
        self.mgr = self.env.formula_manager
        self.preprocessor = CNFPreprocessor(env=self.env)
        self.wmi_variables = wmi_variables
        self._introduced_variables = {}

    def _get_key(self, formula, cnf=None, **kwargs):
        return formula

    def _key_var(self, formula):
        if formula in self._introduced_variables:
            res = self._introduced_variables[formula]
        else:
            res = self.wmi_variables.new_cnf_label(len(self._introduced_variables))
            self._introduced_variables[formula] = res
        return res

    def _neg(self, formula):
        if formula.is_not():
            return formula.arg(0)
        else:
            return self.mgr.Not(formula)

    def convert(self, formula):
        """Convert formula into an equisatisfiable CNF.

        Returns a set of clauses: a set of sets of literals.
        """
        formula = self.preprocessor.walk(formula)
        cnf = list()
        tl = self.walk(formula, cnf=cnf)

        if not cnf:
            return frozenset((frozenset(),))
        res = []
        for clause in cnf:
            if len(clause) == 0:
                return {frozenset()}
            simp = []
            for lit in clause:
                if lit is tl or lit.is_true():
                    # Prune clauses that are trivially TRUE
                    # and clauses containing the top level label
                    simp = None
                    break
                elif not lit.is_false() and lit is not self._neg(tl):
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(frozenset(simp))

        return frozenset(res)

    def walk_not(self, formula, args, cnf=None, **kwargs):
        a = args[0]
        if a.is_true():
            return self.mgr.Bool(False)
        elif a.is_false():
            return self.mgr.Bool(True)
        else:
            return self._neg(a)

    def walk_and(self, formula, args, cnf=None, **kwargs):
        if len(args) == 1:
            return args[0]
        k = self._key_var(formula)

        for a in args:
            cnf.append([a, self._neg(k)])

        return k

    def walk_or(self, formula, args, cnf=None, **kwargs):
        if len(args) == 1:
            return args[0]
        k = self._key_var(formula)

        cnf.append([self._neg(k)] + args)

        return k

    def walk_iff(self, formula, args, cnf=None, **kwargs):
        left, right = args
        if left == right:
            return self.mgr.Bool(True)
        k = self._key_var(formula)
        cnf.append([self._neg(k), self._neg(left), right])
        cnf.append([self._neg(k), left, self._neg(right)])
        cnf.append([k, left, right])
        cnf.append([k, self._neg(left), self._neg(right)])

        return k

    @handles(op.SYMBOL)
    @handles(op.CONSTANTS)
    @handles(op.RELATIONS)
    @handles(op.THEORY_OPERATORS)
    def walk_identity(self, formula, cnf=None, **kwargs):
        return formula
