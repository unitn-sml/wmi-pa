from typing import Collection, Optional

import numpy as np
from scipy.optimize import linprog

from wmipa.core import Polynomial, Polytope


class RejectionIntegrator:
    """This class implements an integrator based on rejection sampling."""

    DEF_N_SAMPLES = int(10e3)

    def __init__(self, n_samples: Optional[int] = None, seed: Optional[int] = None):
        """Default constructor.

        Args:
            n_samples: sample size (default: 10e3)
            seed: the seed number (optional)
        """

        self.n_samples = (
            RejectionIntegrator.DEF_N_SAMPLES if n_samples is None else n_samples
        )
        if seed is not None:
            np.random.seed(seed)

    def integrate(self, polytope: Polytope, integrand: Polynomial) -> float:
        """Computes a convex integral.

        Args:
            polytope: convex integration bounds
            polynomial: the integrand

        Returns:
            The result of the integration as a non-negative scalar value.
        """
        A, b = polytope.to_numpy()

        # compute the enclosing axis-aligned bounding box (lower, upper)
        lowerl, upperl = [], []
        for i in range(polytope.N):
            cost = np.array([1 if j == i else 0 for j in range(polytope.N)])
            res = linprog(cost, A_ub=A, b_ub=b, method="highs-ds", bounds=(None, None))
            lowerl.append(res.x[i])
            res = linprog(-cost, A_ub=A, b_ub=b, method="highs-ds", bounds=(None, None))
            upperl.append(res.x[i])

        lower, upper = np.array(lowerl), np.array(upperl)

        # sample uniformly from the AA-BB and reject the samples outside the polytope
        sample = (
            np.random.random((self.n_samples, polytope.N)) * (upper - lower) + lower
        )
        valid_sample = sample[np.all(sample @ A.T < b, axis=1)]

        if len(valid_sample) > 0:
            # return the Monte Carlo estimate of the integral
            volume = (len(valid_sample) / len(sample)) * np.prod(upper - lower)
            result = float(np.mean(integrand.to_numpy()(valid_sample)) * volume)
        else:
            result = 0.0

        return result

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
        for polytope, integrand in convex_integrals:
            volumes.append(self.integrate(polytope, integrand))

        return np.array(volumes)
