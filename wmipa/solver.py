"""This module implements the main solver class.

This WMI solver is based upon:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a procedure for computing the integral of polynomials over polytopes (e.g. LattE Integrale)

"""

__version__ = "1.1"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

from typing import Collection, cast

import networkx as nx
import numpy as np
from pysmt.environment import Environment, get_env
from pysmt.fnode import FNode
from pysmt.typing import REAL, BOOL

from wmipa.datastructures import Polynomial, Polytope
from wmipa.enumeration import Enumerator, MathSATEnumerator
from wmipa.integration import Integrator, RejectionIntegrator
from wmipa.weights import Weights


class WMISolver:
    """The class that has the purpose to calculate the Weighted Module Integration of
        a given support, weight function, and query.

    Attributes:
        weights (Weights): The representation of the weight function.
        support (FNode): The pysmt formula that contains the support of the formula
        integrator (Integrator): The integrator to use.
    """

    DEF_ENUMERATOR = MathSATEnumerator
    DEF_INTEGRATOR = RejectionIntegrator()

    def __init__(self, support, w=smt.Real(1), enumerator=None, integrator=None):
        self.support = support

        if env is not None:
            self.env = env
        else:
            self.env = cast(Environment, get_env())

        self.mgr = self.env.formula_manager

        if weight is None:
            weight = self.mgr.Real(1)  # Default weight is 1

        self.weights = Weights(weight, self.env)

        if enumerator is not None:
            self.enumerator = enumerator
        else:
            self.enumerator = self.DEF_ENUMERATOR(self)

        if integrator is not None:
            self.integrator = integrator
        else:
            self.integrator = self.DEF_INTEGRATOR

    def computeWMI(
        self, phi: FNode, domain: Collection[FNode], cache: int = -1
    ) -> dict[str, np.ndarray]:

        convex_integrals = []
        n_unassigned_bools = []
        for truth_assignment, nub in self.enumerator.enumerate(phi):
            convex_integrals.append(
                self._assignment_to_integral(truth_assignment, domain)
            )
            n_unassigned_bools.append(nub)

        factors = [2**nb for nb in n_unassigned_bools]
        wmi = np.sum(
            self.integrator.integrate_batch(convex_integrals) * factors, axis=-1
        )

        result = {"wmi": wmi, "npolys": len(convex_integrals)}

        return result

    def _assignment_to_integral(
        self, truth_assignment: dict[FNode, bool], domain: Collection[FNode]
    ) -> tuple[Polytope, Polynomial]:

        uncond_weight = self.weights.weight_from_assignment(truth_assignment)

        # build a dependency graph of the alias substitutions
        # handle non-constant and constant definitions separately
        Gsub = nx.DiGraph()
        constants = {}
        aliases = {}
        inequalities = []
        for atom, truth_value in truth_assignment.items():

            if atom.is_le() or atom.is_lt():
                inequalities.append(atom if truth_value else self.mgr.Not(atom))
            elif atom.is_equals() and truth_value:
                left, right = atom.args()

                if left.is_symbol(REAL):
                    alias, expr = left, right
                elif right.is_symbol(REAL):
                    alias, expr = right, left
                else:
                    raise ValueError(f"Malformed alias {atom}")

                if alias in aliases:
                    msg = f"Multiple aliases {alias}:\n1) {expr}\n2) {aliases[alias]}"
                    raise ValueError(msg)

                aliases[alias] = expr
                for var in expr.get_free_variables():
                    Gsub.add_edge(alias, var)

                if len(expr.get_free_variables()) == 0:  # constant handled separately
                    constants.update({alias: expr})
            elif atom.is_symbol(BOOL):
                pass
            else:
                raise ValueError(f"Unsupported atom in assignment: {atom}")

        # order of substitutions is determined by a topological sort of the digraph
        try:
            order = [node for node in nx.topological_sort(Gsub) if node in aliases]
        except nx.exception.NetworkXUnfeasible:
            raise ValueError("Cyclic aliases definition")

        convex_formula = self.mgr.And(inequalities)
        for alias in order:
            convex_formula = convex_formula.substitute({alias: aliases[alias]})
            uncond_weight = uncond_weight.substitute({alias: aliases[alias]})

        # substitute all constants
        uncond_weight = uncond_weight.substitute(constants)
        convex_formula = convex_formula.substitute(constants)

        inequalities = []
        for literal in convex_formula.args():

            if literal.is_not():
                negated_atom = literal.args()[0]
                left, right = negated_atom.args()
                if negated_atom.is_le():
                    atom = self.mgr.LT(right, left)
                elif negated_atom.is_lt():
                    atom = self.mgr.LE(right, left)
                else:
                    raise NotImplementedError("Unhandled case")
            else:
                atom = literal

            # Add a bound if the atom is an inequality
            if atom.is_le() or atom.is_lt():
                inequalities.append(atom)
            else:
                raise NotImplementedError("Unhandled case")

        polytope = Polytope(inequalities, domain, env=self.env)

        try:
            integrand = Polynomial(uncond_weight, domain, env=self.env)
        except ValueError:
            # fallback to generic integrand
            raise NotImplementedError()

        return polytope, integrand


if __name__ == "__main__":
    import pysmt.shortcuts as smt
    from wmipa.integration import LattEIntegrator

    x = smt.Symbol("x", REAL)
    y = smt.Symbol("y", REAL)

    variables = [x, y]

    b1 = smt.LE(smt.Real(0), x)
    b2 = smt.LE(smt.Real(0), y)
    b3 = smt.LE(x, smt.Real(1))
    b4 = smt.LE(y, smt.Real(1))
    bb = smt.And(b1, b2, b3, b4)

    h1 = smt.LE(smt.Plus(x, y), smt.Real(1))
    h2 = smt.LE(x, y)
    h3 = smt.LE(y, x)

    s = smt.And(bb, smt.Or(h1, h2, h3))

    w = smt.Real(1)  # Plus(x, y)

    solver1 = WMISolver(s, w)
    result1 = solver1.computeWMI(smt.Bool(True), variables)
    print("result1", result1)

    solver2 = WMISolver(s, w, integrator=LattEIntegrator())
    result2 = solver2.computeWMI(smt.Bool(True), variables)
    print("result2", result2)
