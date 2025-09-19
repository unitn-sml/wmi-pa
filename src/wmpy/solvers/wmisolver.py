__version__ = "1.1"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

from typing import Collection, Optional

import numpy as np

from pysmt.fnode import FNode

from wmpy.core import AssignmentConverter
from wmpy.enumeration import Enumerator, TotalEnumerator
from wmpy.integration import Integrator, RejectionIntegrator


class WMISolver:
    """The class implements a WMI solver based on exhaustive enumeration.

    The weighted model integral is solved sequentially:
    1) enumerator first computes the set of satisfiable truth assignments (TAs);
    2) the TAs are converted into convex integration problems and jointly passed to the integrator of choice.

    The weight and its support are contained inside the enumerator, with the AssignmentConverter being in charge of converting TAs into <Polytope, Polynomial> pairs.

    """

    DEF_ENUMERATOR = TotalEnumerator
    DEF_INTEGRATOR = RejectionIntegrator

    def __init__(
        self,
        enumerator: Enumerator,
        integrator: Optional[Integrator] = None,
    ):
        """Default constructor.

        Args:
            enumerator: the enumerator to use (default: TotalEnumerator)
            integrator: the integrator to use (default: RejectionIntegrator)
        """
        self.enumerator = enumerator

        if integrator is not None:
            self.integrator = integrator
        else:
            self.integrator = self.DEF_INTEGRATOR()

        self.converter = AssignmentConverter(self.enumerator)

    def compute(self, query: FNode, domain: Collection[FNode]) -> dict[str, np.ndarray]:
        """Computes the weighted model integral of a given query formula.

        Args:
            query: the query as a pysmt formula
            domain: the continuous integration domain (a list of pysmt real variables)


        Returns:
            A dictionary containing the following entries:
            "wmi": the weighted model integral as a non-negative scalar value
            "npolys": the number of convex fragments enumerated
        """
        convex_integrals = []
        n_unassigned_bools = []
        for truth_assignment, nub in self.enumerator.enumerate(query):
            convex_integrals.append(self.converter.convert(truth_assignment, domain))
            n_unassigned_bools.append(nub)

        factors = [2**nb for nb in n_unassigned_bools]
        wmi = np.dot(self.integrator.integrate_batch(convex_integrals), factors)

        result = {"wmi": wmi, "npolys": len(convex_integrals)}

        return result
