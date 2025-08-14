__version__ = "1.1"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

from typing import Collection, Optional

import numpy as np

from pysmt.fnode import FNode

from wmipa.core import AssignmentConverter
from wmipa.enumeration import Enumerator, TotalEnumerator
from wmipa.integration import Integrator, RejectionIntegrator


class AllSMTSolver:
    """The class that has the purpose to calculate the WMI via
    exhaustive enumeration.

    This WMI solver is based upon:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a procedure for computing the integral of polynomials over polytopes (e.g. LattE Integrale)

    Attributes:
        enumerator (Enumerator): The enumerator to use.
        integrator (Integrator): The integrator to use.

    """

    DEF_ENUMERATOR = TotalEnumerator
    DEF_INTEGRATOR = RejectionIntegrator

    def __init__(
        self,
        enumerator: Enumerator,
        integrator: Optional[Integrator] = None,
    ):

        if enumerator is not None:
            self.enumerator = enumerator
        else:
            self.enumerator = self.DEF_ENUMERATOR()

        if integrator is not None:
            self.integrator = integrator
        else:
            self.integrator = self.DEF_INTEGRATOR()

        self.converter = AssignmentConverter(self.enumerator)

    def compute(
        self, phi: FNode, domain: Collection[FNode], cache: int = -1
    ) -> dict[str, np.ndarray]:

        convex_integrals = []
        n_unassigned_bools = []
        for truth_assignment, nub in self.enumerator.enumerate(phi):
            convex_integrals.append(
                self.converter.convert(truth_assignment, domain)
            )
            n_unassigned_bools.append(nub)

        factors = [2**nb for nb in n_unassigned_bools]
        wmi = np.dot(self.integrator.integrate_batch(convex_integrals), factors)

        result = {"wmi": wmi, "npolys": len(convex_integrals)}

        return result
