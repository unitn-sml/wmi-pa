from typing import TYPE_CHECKING, Iterable

from pysmt.environment import Environment
from pysmt.fnode import FNode
from pysmt.formula import FormulaManager

from wmipa.weights import Weights

if TYPE_CHECKING:  # avoid circular import
    from wmipa.solver import WMISolver


class Z3Enumerator:

    def initialize(self, solver: "WMISolver") -> None:
        self.solver = solver

    @property
    def env(self) -> Environment:
        return self.solver.env

    @property
    def mgr(self) -> FormulaManager:
        return self.env.formula_manager

    @property
    def support(self) -> FNode:
        return self.solver.support

    @property
    def weights(self) -> Weights:
        return self.solver.weights

    def enumerate(self, phi: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """Enumerates the convex fragments of (phi & support), using
        Z3 with blocking clauses. Since the truth assignments (TA) are total,
        the number of unassigned Boolean variables is always 0.

        Yields:
        <TA, n>

        where:
        - TA is dict {pysmt_atom : bool}
        - n is int
        """
        # conjoin query and support
        formula = self.mgr.And(phi, self.support)

        # sort the different atoms
        atoms = self.env.ao.get_atoms(formula) | self.weights.get_atoms()

        smt_solver = self.env.factory.Solver(name="z3")
        smt_solver.add_assertion(formula)

        while smt_solver.solve():
            model = {}
            blocking_clause = []
            for a in atoms:
                literal = (
                    a if smt_solver.get_value(a).constant_value() else self.mgr.Not(a)
                )
                model[a] = not literal.is_not()
                blocking_clause.append(literal)

            smt_solver.add_assertion(self.mgr.Not(self.mgr.And(*blocking_clause)))
            yield model, 0
