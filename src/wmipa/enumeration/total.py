from typing import TYPE_CHECKING, Iterable, Optional, cast

from pysmt.environment import Environment, get_env
from pysmt.fnode import FNode
from pysmt.formula import FormulaManager

from wmipa.core.weights import Weights


class TotalEnumerator:

    def __init__(
        self,
        support: FNode,
        weight: Optional[FNode] = None,
        env: Optional[Environment] = None,
    ) -> None:
        """
        Constructs a TotalEnumerator instance.
        Args:
            weights (Weights): The representation of the weight function.
            support (FNode): The pysmt formula that contains the support of the formula
            env (Environment) : The pysmt environment
        """
        self.support = support

        if env is not None:
            self.env = env
        else:
            self.env = cast(Environment, get_env())

        self.mgr = self.env.formula_manager

        if weight is None:
            weight = self.mgr.Real(1)  # Default weight is 1

        self.weights = Weights(weight, self.env)

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
