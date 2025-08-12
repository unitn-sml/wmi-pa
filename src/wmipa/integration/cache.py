from typing import TYPE_CHECKING, Collection, Optional

import numpy as np

from wmipa.datastructures import Polytope, Polynomial

if TYPE_CHECKING:  # avoid circular import
    from wmipa.integration import Integrator


class CacheWrapper:

    def __init__(self, integrator: "Integrator"):
        self.integrator = integrator
        self.cache: dict[int, float] = dict()

    def integrate(self, polytope: Polytope, polynomial: Polynomial) -> float:
        key = CacheWrapper._compute_key(polytope, polynomial)
        if key in self.cache:
            return self.cache[key]
        else:
            return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(
        self, convex_integrals: Collection[tuple[Polytope, Polynomial]]
    ) -> np.ndarray:
        volumes: list[Optional[float]] = [None] * len(convex_integrals)
        miss_indices, miss_batch = [], []
        for i, conv_int in enumerate(convex_integrals):
            key = CacheWrapper._compute_key(*conv_int)
            if key in self.cache:
                volumes[i] = self.cache[key]
            else:
                miss_indices.append(i)
                miss_batch.append(conv_int)

        for j, vol in enumerate(self.integrator.integrate_batch(miss_batch)):
            volumes[miss_indices[j]] = vol

        return np.array(volumes)

    @staticmethod
    def _compute_key(polytope: Polytope, polynomial: Polynomial) -> int:
        return hash(str(polytope) + str(polynomial))
