"""This module implements the main solver class.

This WMI solver is based upon:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a procedure for computing the integral of polynomials over polytopes (e.g. LattE Integrale)

"""

__version__ = "1.1"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

import networkx as nx
import numpy as np
import pysmt.shortcuts as smt

from wmipa.datastructures import Polynomial, Polytope
from wmipa.enumeration import *
from wmipa.integration import *
from wmipa.weights import Weights


class WMISolver:
    """The class that has the purpose to calculate the Weighted Module Integration of
        a given support, weight function and query.

    Attributes:
        weights (Weights): The representation of the weight function.
        support (FNode): The pysmt formula that contains the support of the formula
        integrator (Integrator): The integrator to use.

    """

    DEF_ENUMERATOR = MathSATEnumerator
    DEF_INTEGRATOR = RejectionIntegrator()

    def __init__(self, support, w=smt.Real(1), enumerator=None, integrator=None):
        self.support = support
        self.weights = Weights(w)

        if enumerator is not None:
            self.enumerator = enumerator
        else:
            self.enumerator = self.DEF_ENUMERATOR(self)

        if integrator is not None:
            self.integrator = integrator
        else:
            self.integrator = self.DEF_INTEGRATOR

    def computeWMI(self, phi, domain, cache=-1):

        convex_integrals = []
        n_unassigned_bools = []
        for truth_assignment, nub in self.enumerator.enumerate(phi):
            convex_integrals.append(
                self._assignment_to_integral(truth_assignment, domain)
            )
            n_unassigned_bools.append(nub)

        factors = [2 ** nb for nb in n_unassigned_bools]
        wmi = np.sum(
            self.integrator.integrate_batch(convex_integrals) * factors, axis=-1
        )

        result = {"wmi": wmi, "npolys": len(convex_integrals)}

        return result

    def _assignment_to_integral(self, truth_assignment, domain):

        uncond_weight = self.weights.weight_from_assignment(truth_assignment)

        # build a dependency graph of the alias substitutions
        # handle non-constant and constant definitions separately
        Gsub = nx.DiGraph()
        constants = {}
        aliases = {}
        inequalities = []
        for atom, truth_value in truth_assignment.items():

            if atom.is_le() or atom.is_lt():
                inequalities.append(atom if truth_value else smt.Not(atom))
            elif atom.is_equals() and truth_value:
                left, right = atom.args()
                if left.is_symbol(smt.REAL):
                    alias, expr = left, right
                elif right.is_symbol(smt.REAL):
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
            elif atom.is_symbol(smt.BOOL):
                pass
            else:
                raise ValueError(f"Unsupported atom in assignment: {atom}")

        # order of substitutions is determined by a topological sort of the digraph
        try:
            order = [node for node in nx.topological_sort(Gsub) if node in aliases]
        except nx.exception.NetworkXUnfeasible:
            raise ValueError("Cyclic aliases definition")

        convex_formula = smt.And(inequalities)
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
                    atom = smt.LT(right, left)
                elif negated_atom.is_lt():
                    atom = smt.LE(right, left)
                else:
                    raise NotImplementedError("Unhandled case")
            else:
                atom = literal

            # Add a bound if the atom is an inequality
            if atom.is_le() or atom.is_lt():
                inequalities.append(atom)
            else:
                raise NotImplementedError("Unhandled case")

        polytope = Polytope(inequalities, domain)

        try:
            integrand = Polynomial(uncond_weight, domain)
        except ValueError:
            # fallback to generic integrand
            raise NotImplementedError()

        return polytope, integrand


if __name__ == "__main__":
    from pysmt.shortcuts import *

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)

    variables = [x, y]

    b1 = LE(Real(0), x)
    b2 = LE(Real(0), y)
    b3 = LE(x, Real(1))
    b4 = LE(y, Real(1))
    bb = And(b1, b2, b3, b4)

    h1 = LE(Plus(x, y), Real(1))
    h2 = LE(x, y)
    h3 = LE(y, x)

    support = And(bb, Or(h1, h2, h3))

    w = Real(1)  # Plus(x, y)

    solver1 = WMISolver(support, w)
    result1 = solver1.computeWMI(Bool(True), variables)
    print("result1", result1)

    solver2 = WMISolver(support, w, integrator=LattEIntegrator())
    result2 = solver2.computeWMI(Bool(True), variables)
    print("result2", result2)
