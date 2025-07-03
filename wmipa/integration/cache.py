

class CacheWrapper:

    def __init__(self, integrator):
        self.integrator = integrator
        self.cache = dict()

    def integrate(self, polytope, polynomial):
        key = CacheWrapper._compute_key(polytope, polynomial)
        if key in cache:
            return cache[key]
        else:
            return self.integrator.integrate(polytope, polynomial)

    def integrate_batch(self, convex_integrals):
        volumes = []
        for polytope, polynomial in convex_integrals:
            volumes.append(self.integrate(polytope, polynomial))

        return np.array(volumes)

    @staticmethod
    def _compute_key(polytope, polynomial):
        return hash(str(polytope)+str(polynomial))
