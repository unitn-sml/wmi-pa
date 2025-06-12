
import numpy as np
from scipy.optimize import linprog

class RejectionIntegrator:

    DEF_N_SAMPLES = int(10e3)

    def __init__(self, n_samples=None, seed=None):
        self.n_samples = n_samples or RejectionIntegrator.DEF_N_SAMPLES
        if seed is not None:
            np.random.seed(seed)

    def integrate(self, polytope, integrand):

        #print("\n\n", "integrate")
        #print(polytope)
        #print("---")

        A, b = polytope.to_numpy()

        #print("A", A)
        #print("b", b)

        # compute the enclosing axis-aligned bounding box (lower, upper)
        lower, upper = [], []
        for i in range(polytope.N):
            cost = np.array([1 if j==i else 0 for j in range(polytope.N)])
            res = linprog(cost, A_ub=A, b_ub=b)
            lower.append(res.x[i])
            res = linprog(-cost, A_ub=A, b_ub=b)
            upper.append(res.x[i])

        lower, upper = np.array(lower), np.array(upper)

        #print("L", lower, "U", upper)

        # sample uniformly from the AA-BB and reject the samples outside the polytope
        sample = np.random.random((self.n_samples, polytope.N)) * (upper - lower) + lower
        valid_sample = sample[np.all(sample @ A.T < b, axis=1)]

        if len(valid_sample) > 0:
            # return the Monte Carlo estimate of the integral
            result = np.mean(integrand.to_numpy()(valid_sample)) * (len(valid_sample) / len(sample))
        else:
            result = 0.0

        #print(f"{result} ({len(valid_sample)} samples)")
        return result


    def integrate_batch(self, convex_integrals):
        volumes = []
        for polytope, integrand in convex_integrals:
            volumes.append(self.integrate(polytope, integrand))

        return np.array(volumes)


if __name__ == '__main__':

    from pysmt.shortcuts import *
    from wmipa.datastructures import Polynomial, Polytope

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)

    variables = [x, y]

    h1 = LE(Real(0), x)
    h2 = LE(Real(0), y)
    h3 = LE(Plus(x, y), Real(1))

    w = Minus(Real(1), Plus(x, y))
    w = Plus(x, y)

    polytope = Polytope([h1, h2, h3], variables)    
    integrand = Polynomial(w, variables)
    
    n_samples = 100000

    integrator = RejectionIntegrator()

    print("integral:", integrator.integrate(polytope, integrand))

    

    
