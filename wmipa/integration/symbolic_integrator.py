# from pysmt.shortcuts import Bool
import sys

from wmipa.wmiexception import WMIIntegrationException

from wmipa.integration.cache_integrator import CacheIntegrator
from wmipa.integration.expression import Expression
from wmipa.integration.polytope import Polynomial, Polytope

sys.setrecursionlimit(10 ** 5)

_PYXADD_INSTALLED = False
Domain = None
PyXaddEngine = None


class SymbolicIntegrator(CacheIntegrator):
    """This class handles the integration of polynomial functions over (convex) polytopes.
    """

    def __init__(self, **options):
        super().__init__(**options)
        # trick to avoid circular import, maybe there is a better way
        global _PYXADD_INSTALLED
        if not _PYXADD_INSTALLED:
            global Domain, PyXaddEngine
            try:
                from pywmi.domain import Domain
                from pywmi.engines import PyXaddEngine

                _PYXADD_INSTALLED = True
            except ImportError:
                raise WMIIntegrationException(WMIIntegrationException.INTEGRATOR_NOT_INSTALLED, "Symbolic (PyXadd)")

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

    @classmethod
    def _make_problem(cls, weight, bounds, aliases):
        """Makes the problem to be solved by a symbolic solver.

        Args:
            weight (FNode): The weight function.
            bounds (list): The polytope.
            aliases (dict): The aliases of the variables.
        Returns:
            integrand (Expression): The integrand.
            polytope (Polytope): The polytope.
        """
        integrand = Expression(weight, aliases)
        polytope = Polytope(bounds, aliases)

        return integrand, polytope

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
        return SymbolicIntegrator._integrator()(
            domain=domain, support=support, weight=weight
        ).compute_volume(add_bounds=False)

    def to_json(self):
        return {"name": "symbolic", "n_threads": self.n_threads}

    def to_short_str(self):
        return "symbolic"
