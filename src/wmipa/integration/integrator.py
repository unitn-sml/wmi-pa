from typing import Protocol, Collection

import numpy as np

from wmipa.core import Polytope, Polynomial


class Integrator(Protocol):
    """
    Protocol for classes that can integrate polynomials over polytopes.

    Classes implementing this protocol must provide methods for both
    single integration and batch integration operations.
    """

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        """Computes a convex integral.

        Args:
            polytope: convex integration bounds
            polynomial: the integrand

        Returns:
            The result of the integration as a non-negative scalar value.
        """
        ...

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        """Computes a batch of integrals.

        Args:
            convex_integrals: a collection of bounds/integrand pairs

        Returns:
            The result of the batch of integrations as a numpy array.
        """
        ...
