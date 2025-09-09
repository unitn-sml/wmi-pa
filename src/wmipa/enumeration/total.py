from typing import Iterable, Optional, cast

from pysmt.environment import Environment, get_env
from pysmt.fnode import FNode

from wmipa.core.weights import Weights


class TotalEnumerator:
    """This class implements a baseline total enumerator using the Z3 SMT solver."""

    def __init__(
        self,
        support: FNode,
        weight: Optional[FNode] = None,
        env: Optional[Environment] = None,
    ) -> None:
        """Default constructor.

        Args:
            weights: the weight function as a pysmt term
            support: the support of the weight function (a pysmt formula)
            env: the pysmt environment (optional)
        """
        self.support = support

        if env is not None:
            self.env = env
        else:
            self.env = cast(Environment, get_env())

        if weight is None:
            weight = self.env.formula_manager.Real(1)  # Default weight is 1

        self.weights = Weights(weight, self.env)

    def enumerate(self, query: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """Enumerates (possibly partial) truth assignments for the given formula.

        Since the truth assignments (TA) are always total,
        the number of unassigned Boolean variables is always 0.

        Args:
            query: the query (a pysmt formula)

        Returns:
            An iterable of tuples <TA, 0> where:
            - TA is a dictionary {pysmt_atom : bool} representing (partial) truth assignment
        """
        mgr = self.env.formula_manager

        # conjoin query and support
        formula = mgr.And(query, self.support)

        # sort the different atoms
        atoms = self.env.ao.get_atoms(formula) | self.weights.get_atoms()

        with self.env.factory.Solver(name="z3") as smt_solver:
            smt_solver.add_assertion(formula)

            while smt_solver.solve():
                model = {}
                blocking_clause = []
                for a in atoms:
                    literal = (
                        a if smt_solver.get_value(a).constant_value() else mgr.Not(a)
                    )
                    model[a] = not literal.is_not()
                    blocking_clause.append(literal)

                smt_solver.add_assertion(mgr.Not(mgr.And(*blocking_clause)))
                yield model, 0
