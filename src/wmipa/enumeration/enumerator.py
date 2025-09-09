from typing import TYPE_CHECKING, Protocol, Iterable

from pysmt.fnode import FNode
from pysmt.environment import Environment

if TYPE_CHECKING:
    from wmipa.core.weights import Weights


class Enumerator(Protocol):
    """Protocol for classes that can enumerate partial truth assignments for weighted SMT formulas.

    An Enumerator always contains:
        weights: the weight function (a pysmt term)
        support: the support of the weight function (a pysmt formula)
        env: the pysmt environment

    An Enumerator implements the 'enumerate' method that, given a query SMT formula, return all the truth assignments that are consistent with both support and query. In other terms, Enumerator returns a convex partitioning of the intersection of support and query.
    """

    @property
    def support(self) -> FNode: ...

    @property
    def weights(self) -> "Weights": ...

    @property
    def env(self) -> Environment: ...

    def enumerate(self, query: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """Enumerates (possibly partial) truth assignments for the given formula.

        Since the truth assignments (TA) might be partial,
        the number of unassigned Boolean variables is also returned.

        Note: Enumerate can return any iterable type: list, tuple, generator, iterator, etc.

        Args:
            query: the query as a pysmt formula

        Returns:
            An iterable of tuples <TA, NB> where:
            - TA is a dictionary {pysmt_atom : bool} representing (partial) truth assignment
            - NB is a non-negative integer representing the number of unassigned Boolean variables
        """
        ...
