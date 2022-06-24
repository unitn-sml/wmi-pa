# from pysmt.shortcuts import Bool
import math
import sys
from functools import partial

from pysmt.shortcuts import Real
from pywmi.domain import Domain
from pywmi.engines import PyXaddAlgebra, PyXaddEngine, XaddEngine, XsddEngine
from pywmi.engines.algebraic_backend import SympyAlgebra
from pywmi.engines.xsdd import FactorizedXsddEngine as FXSDD
from pywmi.engines.xsdd.vtrees.vtree import balanced

from wmipa.integration.cache_integrator import CacheIntegrator
from wmipa.integration.polytope import Polynomial, Polytope

sys.setrecursionlimit(10**5)


class SymbolicIntegrator(CacheIntegrator):
    def __init__(self, **options):
        super().__init__(**options)

    @staticmethod
    def _integrator():
        return PyXaddEngine
        # return partial(
        #     XsddEngine,
        #     algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
        #     ordered=False,
        # )

        # return partial(
        #     FXSDD,
        #     vtree_strategy=balanced,
        #     algebra=PyXaddAlgebra(symbolic_backend=SympyAlgebra()),
        #     ordered=False,
        # )
        # return XaddEngine

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
        variables = {
            v: (None, None) for v in integrand.variables.union(polytope.variables)
        }
        domain = Domain.make(real_variables=variables)
        # print("Rec limit: ", sys.getrecursionlimit())
        return SymbolicIntegrator._integrator()(
            domain=domain, support=support, weight=weight
        ).compute_volume(add_bounds=False)
