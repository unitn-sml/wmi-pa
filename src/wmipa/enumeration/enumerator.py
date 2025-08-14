from typing import TYPE_CHECKING, Protocol, Iterable

from pysmt.fnode import FNode
from pysmt.environment import Environment

from wmipa.core.weights import Weights


class Enumerator(Protocol):
    """
    Protocol for classes that can enumerate partial truth assignments for weighted SMT formulas.
    """

    @property
    def support(self) -> FNode: ...

    @property
    def weights(self) -> Weights: ...

    @property
    def env(self) -> Environment: ...

    def enumerate(self, phi: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
        """
        Enumerate partial truth assignments for the given formula.

        Since the truth assignments (TA) might be partial,
        the number of unassigned Boolean variables is also returned.

        Args:
            phi: A formula node to enumerate partial assignments for

        Returns:
            An iterable of tuples <TA, n> where:
            - TA is dict {pysmt_atom : bool} representing (partial) truth assignment
            - n is int representing the number of unassigned Boolean variables

        Note:
            Can return any iterable type: list, tuple, generator, iterator, etc.
        """
        ...
