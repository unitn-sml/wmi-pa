import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.oracles import AtomsOracle
from pysmt.rewritings import NNFizer
from pysmt.shortcuts import (
    Bool,
    FreshSymbol,
    Not,
    Or,
    BOOL,
    get_env,
    simplify,
    serialize,
    substitute,
)
from pysmt.walkers import DagWalker, IdentityDagWalker, handles, TreeWalker

from wmipa.utils import is_atom


class Weights:
    """This class handles a FIUC weight function and provides a method that can evaluate
        the weight result given a truth assignment of all the conditions inside the
        weight function.

    Attributes:
        weight_func (FNode): The pysmt formula that represents the weight function.
    """

    def __init__(self, weight_func):
        """Initializes the weight object.

        Args:
            weight_func (FNode): The pysmt formula representing the weight function.
        """
        self.weight_func = weight_func
        self.atoms_finder = WeightAtomsFinder()

    def compute_skeleton(self):
        return WeightConverterSkeleton().convert(self.weight_func)

    def get_atoms(self):
        atoms = self.atoms_finder.get_atoms(self.weight_func)
        return atoms if atoms is not None else frozenset([])

    def weight_from_assignment(self, assignment):
        """Given a truth assignment of the conditions inside the weight function,
            this method evaluates the resulting value based on the assignment.

        Args:
            assignment (dict {FNode : bool}): The dictionary containing all the
                assignments of each condition (e.g: {(x < 3) : True, (y < 5) : False}).

        Returns:
            FNode: The result of the weight function on the given assignment.
        """
        assignment = {atom: Bool(v) for atom, v in assignment.items()}

        return self._evaluate_weight(self.weight_func, assignment)

    def _evaluate_weight(self, node, assignment):
        """Evaluates the value of the given formula applied to the given assignment.

        Args:
            node (FNode): The pysmt formula representing (part of) the weight function.
            assignment (list(bool)): The dictionary containing the truth value of
                each assignment.

        Returns:
            FNode: The result of the formula representing (part of) the weight function
                applied to the given assignment.

        """
        if node.is_ite():
            cond, then, _else = node.args()
            value = self._evaluate_condition(cond, assignment)
            if value:
                return self._evaluate_weight(then, assignment)
            else:
                return self._evaluate_weight(_else, assignment)

        # found a leaf, return it
        elif len(node.args()) == 0:
            return node

        # this condition contains, for example, the Times operator
        else:
            new_children = (
                self._evaluate_weight(child, assignment) for child in node.args()
            )
            return get_env().formula_manager.create_node(
                node_type=node.node_type(), args=tuple(new_children)
            )

    def _evaluate_condition(self, condition, assignment):
        val = simplify(substitute(condition, assignment))
        assert val.is_bool_constant(), (
                "Weight condition "
                + serialize(condition)
                + "\n\n cannot be evaluated with assignment "
                + "\n".join([str((x, v)) for x, v in assignment.items()])
                + "\n\n simplified into "
                + serialize(condition)
        )
        return val.constant_value()

    def __str__(self):
        return ("Weight {" "\t{weight}\n" "}").format(
            weight=serialize(self.weight_func),
        )


class WeightAtomsFinder(AtomsOracle):

    def walk_ite(self, formula, args, **kwargs):
        return frozenset(x for a in args if a is not None for x in a)

    @handles(op.IRA_OPERATORS)
    def walk_theory_op(self, formula, args, **kwargs):
        return frozenset(x for a in args if a is not None for x in a)


class WeightConverterSkeleton(TreeWalker):
    """Implements the conversion of a weight function into a weight skeleton,
    as described in "Enhancing SMT-based Weighted Model Integration by structure awareness"
    (Spallitta et al., 2024).
    """

    def __init__(self, env=None):
        super().__init__(env)
        self.mgr = self.env.formula_manager
        self.cond_labels = set()
        self.cnfizer = PolarityCNFizer(env=self.env)
        self.branch_condition: list[FNode] = []  # clause as a list of FNodes
        self.clauses: list[FNode] = []  # list of clauses, each clause is an Or of FNodes

    def new_cond_label(self):
        b = FreshSymbol(typename=BOOL, template="CNDB%s")
        self.cond_labels.add(b)
        return b

    def convert(self, weight_func: FNode) -> FNode:
        self.clauses.clear()
        self.walk(weight_func)
        return self.mgr.And(self.clauses)

    @handles(op.SYMBOL)
    @handles(op.CONSTANTS)
    def walk_no_conditions(self, formula: FNode):
        return

    @handles(op.IRA_OPERATORS)
    def walk_operator(self, formula: FNode):
        for arg in formula.args():
            yield arg

    def walk_ite(self, formula: FNode):
        phi: FNode
        left: FNode
        right: FNode
        phi, left, right = formula.args()
        if is_atom(phi):
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
            k = self.new_cond_label()
            self.clauses.append(Or(*self.branch_condition, Not(k), phi))
            self.clauses.append(Or(*self.branch_condition, k, Not(phi)))
            self.branch_condition.append(Not(phi))
            yield left  # recursion on the left branch
            self.branch_condition.pop()
            self.branch_condition.append(phi)
            yield right  # recursion on the right branch
            self.branch_condition.pop()
        else:
            b = self.new_cond_label()
            # Here we are not adding the clause
            #   (branch_condition -> (b v not b))
            # since it is subsumed by the CNF clauses of
            #   (branch_condition -> exists b.CNF(b <-> phi))

            # add (conds & b) -> CNF(phi)
            self.branch_condition.append(Not(b))
            for clause in self.cnfizer.convert(phi):
                self.clauses.append(Or(*self.branch_condition, *clause))
            yield left  # recursion on the left branch
            self.branch_condition.pop()
            # add (conds & not b) -> CNF(not phi)
            self.branch_condition.append(b)
            for clause in self.cnfizer.convert(Not(phi)):
                self.clauses.append(Or(*self.branch_condition, *clause))
            yield right  # recursion on the right branch
            self.branch_condition.pop()


class CNFPreprocessor(IdentityDagWalker):
    """
    Convert nested ORs and ANDs into flat lists of ORs and ANDs, and Implies into Or.
    """

    def __init__(self, env=None):
        super().__init__(env)
        self.nnfizer = NNFizer(env)

    def walk(self, formula, **kwargs):
        formula = self.nnfizer.convert(formula)
        return super().walk(formula, **kwargs)

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


class PolarityCNFizer(DagWalker):
    """Implements the Plaisted&Greenbaum CNF conversion algorithm."""

    def __init__(self, env=None):
        super().__init__(env)
        self.mgr = self.env.formula_manager
        self.preprocessor = CNFPreprocessor(env=self.env)
        # self.cnf_labels = set()
        self._introduced_variables = {}

    def _get_key(self, formula, cnf=None, **kwargs):
        return formula

    def _key_var(self, formula):
        if formula in self._introduced_variables:
            res = self._introduced_variables[formula]
        else:
            res = FreshSymbol(typename=BOOL, template="CNFB%s")
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
