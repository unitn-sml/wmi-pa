from typing import Collection

import networkx as nx

from pysmt.fnode import FNode
from pysmt.typing import REAL, BOOL

from .polynomial import Polynomial
from .polytope import Polytope
from wmipa.enumeration.enumerator import Enumerator


class AssignmentConverter:
    """
    This class is responsible of converting the pysmt assignments
    returned by an enumerator into pairs <Polytope, Polynomial>.
    """

    def __init__(self, enumerator: "Enumerator") -> None:
        self.enumerator = enumerator

    def convert(
        self, truth_assignment: dict[FNode, bool], domain: Collection[FNode]
    ) -> tuple[Polytope, Polynomial]:

        mgr = self.enumerator.env.formula_manager

        uncond_weight = self.enumerator.weights.weight_from_assignment(truth_assignment)

        # build a dependency graph of the alias substitutions
        # handle non-constant and constant definitions separately
        Gsub: nx.DiGraph = nx.DiGraph()
        constants = {}
        aliases: dict[FNode, FNode] = {}
        inequalities = []
        for atom, truth_value in truth_assignment.items():

            if atom.is_le() or atom.is_lt():
                inequalities.append(atom if truth_value else mgr.Not(atom))
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
        except nx.NetworkXUnfeasible:
            raise ValueError("Cyclic aliases definition")

        convex_formula = mgr.And(inequalities)
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
                    atom = mgr.LT(right, left)
                elif negated_atom.is_lt():
                    atom = mgr.LE(right, left)
                else:
                    raise NotImplementedError("Unhandled case")
            else:
                atom = literal

            # Add a bound if the atom is an inequality
            if atom.is_le() or atom.is_lt():
                inequalities.append(atom)
            else:
                raise NotImplementedError("Unhandled case")

        polytope = Polytope(inequalities, domain, env=self.enumerator.env)
        polynomial = Polynomial(uncond_weight, domain, env=self.enumerator.env)

        return polytope, polynomial
