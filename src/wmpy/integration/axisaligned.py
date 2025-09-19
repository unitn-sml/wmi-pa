from typing import Collection, Optional, TYPE_CHECKING

import numpy as np

from wmpy.core import Polynomial, Polytope
from wmpy.core.inequality import Inequality

if TYPE_CHECKING:
    from wmpy.integration import Integrator


class AxisAlignedWrapper:
    """This class implements an integration wrapper for efficiently handling the following special case:
    - the polytope is axis-aligned
    - the integrand is constant

    possibly computing the integral in linear time.

    The enclosed integrator is called whenever the problem doesn't fall into this subcase.

    TODO: fix inconsistencies with the returned type.
    """

    def __init__(self, integrator: "Integrator"):
        """Default constructor.

        Args:
            integrator: the enclosed integrator instance
        """
        self.integrator = integrator

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        """Computes a convex integral.

        If the integrand is a constant and the integration bounds are all axis-aligned, the integral is computed in linear time.

        Args:
            polytope: convex integration bounds (a Polytope)
            polynomial: integrand (a Polynomial)

        Returns:
            The result of the integration as a non-negative scalar value.
        """
        w = AxisAlignedWrapper._constant_integrand(polynomial)
        if w is not None:
            vol = AxisAlignedWrapper._axis_aligned_volume(polytope)
            if vol is not None:
                return w * vol

        return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        """Computes a batch of integrals.

        Args:
            convex_integrals: a collection of bounds/integrand pairs

        Returns:
            The result of the batch of integrations as a numpy array.
        """
        volumes = []
        for polytope, polynomial in convex_integrals:
            volumes.append(self.integrate(polytope, polynomial))

        return np.array(volumes)

    @staticmethod
    def _constant_integrand(polynomial: Polynomial) -> Optional[float]:
        if polynomial.degree == 0:
            return list(polynomial.monomials.values())[0]
        else:
            return None

    @staticmethod
    def _axis_aligned_volume(polytope: Polytope) -> Optional[float]:

        def parse_bound(inequality: Inequality) -> Optional[tuple[int, list[float]]]:
            monos = inequality.polynomial.monomials
            if len(monos) == 1:
                exp, coeff = next(iter(monos.items()))
                bound = [-np.inf, 0] if coeff > 0 else [0, np.inf]
                return exp.index(1), bound
            elif len(monos) == 2:
                ckey, exp = inequality.polynomial.ordered_keys
                const = monos[ckey]
                coeff = monos[exp]
                bound = (
                    [-np.inf, -const / coeff] if coeff > 0 else [-const / coeff, np.inf]
                )
                return exp.index(1), bound
            else:
                return None

        bounds = [[-np.inf, np.inf] for _ in range(polytope.N)]

        for ineq in polytope.inequalities:
            nvb = parse_bound(ineq)
            if nvb is None:
                return None
            nvar, new_bound = nvb
            old_bound = bounds[nvar]
            bounds[nvar] = [
                max(old_bound[0], new_bound[0]),
                min(old_bound[1], new_bound[1]),
            ]

        barray = np.array(bounds)
        if (barray[:, 0] > -np.inf).all() and (barray[:, 1] < np.inf).all():
            volume = float(np.prod(np.abs(np.subtract(barray[:, 0], barray[:, 1]))))
            return volume
        else:
            return None
