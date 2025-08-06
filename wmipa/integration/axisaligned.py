from typing import Collection, Optional, TYPE_CHECKING

import numpy as np

from wmipa.datastructures import Inequality, Polynomial, Polytope

if TYPE_CHECKING:
    from wmipa.integration import Integrator


class AxisAlignedWrapper:
    """
    Before calling a general self.integrator, checks if:
    - the polytope is axis-aligned
    - the integrand is constant

    possibly computing the integral in linear time.

    """

    def __init__(self, integrator: "Integrator"):
        self.integrator = integrator

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        w = AxisAlignedWrapper._constant_integrand(polynomial)
        if w is not None:
            vol = AxisAlignedWrapper._axis_aligned_volume(polytope)
            if vol is not None:
                return w * vol

        return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
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
                bound = [0, np.inf] if coeff > 0 else [-np.inf, 0]
                return exp.index(1), bound
            elif len(monos) == 2:
                ckey, exp = inequality.polynomial.ordered_keys
                const = monos[ckey]
                coeff = monos[exp]
                bound = (
                    [-const / coeff, np.inf] if coeff > 0 else [-np.inf, const / coeff]
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
        if barray < np.inf:
            volume = float(np.sum(np.abs(np.subtract(barray[:, 0], barray[:, 1]))))
            return volume
        else:
            return None
