from typing import Protocol, Iterable

import numpy as np

from wmipa.datastructures import Polytope, Polynomial


class Integrator(Protocol):
    """
    Protocol for classes that can integrate polynomials over polytopes.

    Classes implementing this protocol must provide methods for both
    single integration and batch integration operations.
    """

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        """
        Integrate a polynomial over a polytope.

        Args:
            polytope: The polytope domain to integrate over
            polynomial: The polynomial function to integrate

        Returns:
            The numerical result of the integration as a float
        """
        ...

    def integrate_batch(self, convex_integrals: Iterable[tuple[Polytope, Polynomial]]) -> np.ndarray:
        """
        Perform batch integration of multiple polynomial-polytope pairs.

        Args:
            convex_integrals: An iterable of (polytope, polynomial) pairs to integrate

        Returns:
            A numpy array containing the integration results, where each element
            corresponds to the integration of the respective (polytope, polynomial) pair
        """
        ...
