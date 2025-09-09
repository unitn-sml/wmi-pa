from typing import Any, Collection, Generator, Iterable
import pysmt.operators as op
from pysmt.environment import Environment
from pysmt.fnode import FNode
from pysmt.formula import FormulaManager
from pysmt.oracles import AtomsOracle
from pysmt.rewritings import NNFizer
from pysmt.typing import BOOL
from pysmt.walkers import DagWalker, IdentityDagWalker, TreeWalker, handles

from wmipa.core.utils import is_atom, is_clause, is_cnf, is_literal

# TODO: (maybe) move WeightAtomsFinder, WeightsEvaluator inside Weights (making them private)?


class Weights:
    """This class encodes a piecewise weight function.

    Attributes:
        weight_func: the weight function in pysmt format
        env: the pysmt environment
        atoms_finder: TODO: add a bit of documentation for this
        evaluator: internal class for function evaluation
    """

    def __init__(self, weight_func: FNode, env: Environment):
        """Default constructor.

        Args:
            weight_func: the pysmt expression representing the weight function
            env: the pysmt environment
        """
        self.env = env
        self.weight_func = weight_func
        self.atoms_finder = WeightAtomsFinder(env=env)
        self.evaluator = WeightsEvaluator(self)

    def compute_skeleton(self) -> FNode:
        """Computes the "skeleton", a SMT formula that encodes the structure of the weight function.
        Conjoining the skeleton with the support formula can be advantageous when using partial enumeration.

        Returns:
           A pysmt formula that encodes the structure of the weight.
        """
        return WeightConverterSkeleton(env=self.env).convert(self.weight_func)

    def get_atoms(self) -> Collection[FNode]:
        """Returns the atoms contained in the (conditions of the) weight expressions."""
        atoms = self.atoms_finder.get_atoms(self.weight_func)
        return atoms if atoms is not None else frozenset([])

    def weight_from_assignment(self, assignment: dict[FNode, bool]) -> FNode:
        """Evaluates the weight function given a total truth assignment to its conditions.

        Args:
            assignment: the truth assignment as returned by an Enumerator

        Returns:
            A pysmt term that correspond to unconditional weight function obtained by assigning a truth value to the conditions.
        Raises:
            ValueError if the TA is not total.
        """
        return self.evaluator.evaluate(assignment)

    def __str__(self) -> str:
        return (
            "Weight {{"
            "\t{weight}\n"
            "}}".format(
                weight=self.weight_func.serialize(),
            )
        )


class WeightsEvaluator(TreeWalker):
    """This internal class implements the weight evaluation given a truth assignment to its conditions."""

    def __init__(self, weights: Weights):
        super().__init__(weights.env)
        self.mgr: FormulaManager = self.env.formula_manager
        self.simplifier = self.env.simplifier
        self.substituter = self.env.substituter
        self.weight_node: FNode = weights.weight_func

        self.assignment: dict[FNode, FNode] = {}
        self.result: list[FNode] = []  # stack to store the results of the evaluation

    def evaluate(self, assignment: dict[FNode, bool]) -> FNode:
        """Evaluates the weight function given a total TA to its conditions.

        Returns:
            The simplified expression in pysmt format.

        Raises:
            ValueError if the TA is not total.
        """
        self.result.clear()
        self.assignment = {atom: self.mgr.Bool(v) for atom, v in assignment.items()}
        self.walk(self.weight_node)
        assert len(self.result) == 1, f"Expected a single result, got {self.result}"
        return self.result.pop()

    def walk_ite(self, formula: FNode) -> Generator[FNode, None, None]:
        cond, then, _else = formula.args()
        value = self._evaluate_condition(cond)
        yield then if value else _else  # recursion on the branch that is True

    @handles(op.SYMBOL)
    @handles(op.CONSTANTS)
    def walk_leaf(self, formula: FNode) -> None:
        self.result.append(formula)

    @handles(op.IRA_OPERATORS)
    def walk_operator(self, formula: FNode) -> Generator[FNode, None, None]:
        for arg in reversed(formula.args()):
            yield arg  # recurse on children
        new_children = (self.result.pop() for _ in formula.args())
        self.result.append(
            self.mgr.create_node(
                node_type=formula.node_type(), args=tuple(new_children)
            )
        )

    def _evaluate_condition(self, condition: FNode) -> bool:
        val = self.simplifier.simplify(
            self.substituter.substitute(condition, self.assignment)
        )
        if not val.is_bool_constant():
            msg = (
                "Weight condition "
                + self.env.serializer.serialize(condition)
                + "\n\n cannot be evaluated with assignment "
                + "\n".join([str((x, v)) for x, v in self.assignment.items()])
                + "\n\n simplified into "
                + self.env.serializer.serialize(condition)
            )
            raise ValueError(msg)

        return val.constant_value()


class WeightAtomsFinder(AtomsOracle):
    """TODO"""

    def walk_ite(
        self, formula: FNode, args: list[frozenset[FNode]], **kwargs: Any
    ) -> frozenset[FNode]:
        return frozenset(x for a in args if a is not None for x in a)

    @handles(op.IRA_OPERATORS)
    def walk_theory_op(  # pyright: ignore
        self, formula: FNode, args: list[frozenset[FNode]], **kwargs: Any
    ) -> frozenset[FNode]:
        return frozenset(x for a in args if a is not None for x in a)


class WeightConverterSkeleton(TreeWalker):
    """This internal class implements the conversion of a weight function into a weight skeleton,
    as described in "Enhancing SMT-based Weighted Model Integration by structure awareness"
    (Spallitta et al., 2024).
    """

    def __init__(self, env: Environment):
        super().__init__(env)
        self.mgr = self.env.formula_manager
        self.cond_labels: set[FNode] = set()
        self.cnfizer = PolarityCNFizer(env=self.env)
        self.branch_condition: list[FNode] = []  # clause as a list of FNodes
        self.clauses: list[FNode] = (
            []
        )  # list of clauses, each clause is an Or of FNodes

    def new_cond_label(self) -> FNode:
        b = self.mgr.FreshSymbol(typename=BOOL, template="CNDB%s")
        self.cond_labels.add(b)
        return b

    def convert(self, weight_func: FNode) -> FNode:
        self.clauses.clear()
        self.walk(weight_func)
        return self.mgr.And(self.clauses)

    @handles(op.SYMBOL)
    @handles(op.CONSTANTS)
    def walk_no_conditions(self, formula: FNode) -> None:
        return

    @handles(op.IRA_OPERATORS)
    def walk_operator(self, formula: FNode) -> Generator[FNode, None, None]:
        for arg in formula.args():
            yield arg

    def walk_ite(self, formula: FNode) -> Generator[FNode, None, None]:
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
            self.clauses.append(
                self.mgr.Or(*self.branch_condition, self.mgr.Not(k), phi)
            )
            self.clauses.append(
                self.mgr.Or(*self.branch_condition, k, self.mgr.Not(phi))
            )
            self.branch_condition.append(self.mgr.Not(phi))
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
            self.branch_condition.append(self.mgr.Not(b))
            for clause in self.cnfizer.convert(phi):
                self.clauses.append(self.mgr.Or(*self.branch_condition, *clause))
            yield left  # recursion on the left branch
            self.branch_condition.pop()
            # add (conds & not b) -> CNF(not phi)
            self.branch_condition.append(b)
            for clause in self.cnfizer.convert(self.mgr.Not(phi)):
                self.clauses.append(self.mgr.Or(*self.branch_condition, *clause))
            yield right  # recursion on the right branch
            self.branch_condition.pop()


class CNFPreprocessor(IdentityDagWalker):
    """Converts nested ORs and ANDs into flat lists of ORs and ANDs, and Implies into Or."""

    def __init__(self, env: Environment):
        super().__init__(env)
        self.nnfizer = NNFizer(env)

    def walk(self, formula: FNode, **kwargs: Any) -> FNode:
        formula = self.nnfizer.convert(formula)
        return super().walk(formula, **kwargs)

    def walk_or(self, formula: FNode, args: list[FNode], **kwargs: Any) -> FNode:
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

    def walk_and(self, formula: FNode, args: list[FNode], **kwargs: Any) -> FNode:
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

    CNF = list[list[FNode]]

    def __init__(self, env: Environment):
        super().__init__(env)
        self.mgr = self.env.formula_manager
        self.preprocessor = CNFPreprocessor(env=self.env)
        self._introduced_variables: dict[FNode, FNode] = {}

    def _get_key(self, formula: FNode, **kwargs: Any) -> FNode:
        return formula

    def _key_var(self, formula: FNode) -> FNode:
        if formula in self._introduced_variables:
            res = self._introduced_variables[formula]
        else:
            res = self.mgr.FreshSymbol(typename=BOOL, template="CNFB%s")
            self._introduced_variables[formula] = res
        return res

    def _neg(self, formula: FNode) -> FNode:
        if formula.is_not():
            return formula.arg(0)
        else:
            return self.mgr.Not(formula)

    def convert(self, formula: FNode) -> frozenset[frozenset[FNode]]:
        """Converts formula into an equisatisfiable CNF.
        Returns a set of clauses, i.e. a set of sets of literals.
        """

        def literals_in_clause(clause: FNode) -> Iterable[FNode]:
            if is_literal(clause):
                yield clause
            else:
                yield from clause.args()

        def literals_in_cnf(cnf: FNode) -> Iterable[Iterable[FNode]]:
            if is_clause(cnf):
                yield literals_in_clause(cnf)
            else:
                yield from (literals_in_clause(clause) for clause in cnf.args())

        formula = self.preprocessor.walk(formula)
        if is_cnf(formula):
            return frozenset(map(frozenset, literals_in_cnf(formula)))
        cnf: list[list[FNode]] = list()
        tl: FNode = self.walk(formula, cnf=cnf)

        res = []
        for clause in cnf:
            if len(clause) == 0:
                return frozenset(frozenset())
            simp: list[FNode] = []
            for lit in clause:
                if lit is tl or lit.is_true():
                    # Prune clauses that are trivially TRUE
                    # and clauses containing the top level label
                    simp = []
                    break
                elif not lit.is_false() and lit is not self._neg(tl):
                    # Prune FALSE literals
                    simp.append(lit)
            if simp:
                res.append(frozenset(simp))

        return frozenset(res)

    def walk_not(
        self, formula: FNode, args: list[FNode], cnf: CNF, **kwargs: Any
    ) -> FNode:
        a = args[0]
        if a.is_true():
            return self.mgr.Bool(False)
        elif a.is_false():
            return self.mgr.Bool(True)
        else:
            return self._neg(a)

    def walk_and(
        self, formula: FNode, args: list[FNode], cnf: CNF, **kwargs: Any
    ) -> FNode:
        if len(args) == 1:
            return args[0]
        k = self._key_var(formula)

        for a in args:
            cnf.append([a, self._neg(k)])

        return k

    def walk_or(
        self, formula: FNode, args: list[FNode], cnf: CNF, **kwargs: Any
    ) -> FNode:
        if len(args) == 1:
            return args[0]
        k = self._key_var(formula)

        cnf.append([self._neg(k)] + args)

        return k

    def walk_iff(
        self, formula: FNode, args: list[FNode], cnf: CNF, **kwargs: Any
    ) -> FNode:
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
    def walk_identity(self, formula: FNode, **kwargs: Any) -> FNode:
        return formula
