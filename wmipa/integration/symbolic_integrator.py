# from pysmt.shortcuts import Bool
from pywmi.domain import Domain
from pywmi.engines import PyXaddEngine

from wmipa.integration.cache_integrator import CacheIntegrator
from wmipa.integration.polytope import Polynomial, Polytope

# from pywmi.engines.algebraic_backend import SympyAlgebra
# from pywmi.engines.xsdd import FactorizedXsddEngine as FXSDD
# from pywmi.engines.xsdd.vtrees.vtree import balanced


class SymbolicIntegrator(CacheIntegrator):
    def __init__(self, **options):
        super().__init__(**options)
        self.integrator = PyXaddEngine

    def _integrate_problem(self, integrand: Polynomial, polytope: Polytope):
        """Computes the integral of `integrand` over `polytope` using symbolic
            integration methods

        Args:
            integrand (Polynomial): The integrand of the integration.
            polytope (Polytope): The polytope of the integration.

        Returns:
            real: The integration result.

        """
        support = polytope.to_pysmt()
        weight = integrand.to_pysmt()
        variables = {v: None for v in integrand.variables.union(polytope.variables)}
        domain = Domain.make(real_variables=variables)
        return self.integrator(
            domain=domain, support=support, weight=weight
        ).compute_volume(add_bounds=False)
