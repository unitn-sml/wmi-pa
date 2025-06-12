"""This module implements the main solver class.

This WMI solver is based upon:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a procedure for computing the integral of polynomials over polytopes (e.g. LattE Integrale)

"""

__version__ = "1.1"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

import mathsat
import networkx as nx
import numpy as np
import pysmt.shortcuts as smt

from wmipa.datastructures import Polynomial, Polytope
from wmipa.integration import *
from wmipa.utils import TermNormalizer, BooleanSimplifier
from wmipa.weights import Weights


class WMISolver:
    """The class that has the purpose to calculate the Weighted Module Integration of
        a given support, weight function and query.

    Attributes:
        weights (Weights): The representation of the weight function.
        chi (FNode): The pysmt formula that contains the support of the formula
        integrator (Integrator or list(Integrator)): The integrator or the list of integrators to use.
        simplifier (BooleanSimplifier): The class that simplifies the formula.
        normalizer (TermNormalizer): The class that normalizes LRA atoms.

    """

    def __init__(self, chi, w=smt.Real(1), integrator=None):
        self.chi = chi
        self.weights = Weights(w)
        self.weights_skeleton = self.weights.compute_skeleton()
        self.integrator = integrator if integrator is not None else RejectionIntegrator()
        self.normalizer = TermNormalizer()
        self.simplifier = BooleanSimplifier()


    def computeWMI(self, phi, domain, cache=-1):

        convex_integrals = []
        n_unassigned_bools = []
        for truth_assignment, nub in self.enumerate(phi):
            convex_integrals.append(self._assignment_to_integral(truth_assignment, domain))
            n_unassigned_bools.append(nub)

        # multiply each volume by 2^(|A| - |mu^A|)
        factors = [2 ** nb for nb in n_unassigned_bools]
        volume = self._integrate_batch(convex_integrals, factors)
        n_integrations = len(convex_integrals)

        return volume, n_integrations


    def enumerate(self, phi):

        """Enumerates the convex fragments of (phi & support), using
        MathSAT's partial enumeration and structurally aware WMI
        enumeration.

        Yields:
        <truth_assignment, # of unassigned Boolean variables>

        where truth_assignment is a dict {pysmt_atom : bool}

        """

        # conjoin query and support
        formula = smt.And(phi, self.chi)

        # sort the different atoms
        atoms = smt.get_atoms(formula) | self.weights.get_atoms()
        bool_atoms, lra_atoms = set(), set()
        for a in atoms:
            if a.is_symbol(smt.BOOL): bool_atoms.add(a)
            elif a.is_theory_relation(): lra_atoms.add(a)
            else: raise ValueError(f"Unhandled atom type: {a}")

        # conjoin the skeleton of the weight function
        formula = smt.And(formula, self.weights_skeleton)

        if len(bool_atoms) == 0:
            # no Boolean atoms -> enumerate *partial* TAs over LRA atoms only
            for ta_lra in self._get_allsat(formula, lra_atoms):
                yield ta_lra, 0

        else:
            # enumerate *partial* TAs over Boolean atoms first
            for ta_bool in self._get_allsat(formula, bool_atoms):

                # dict containing all necessary truth values
                ta = dict(ta_bool)

                # try to simplify the formula using the partial TA
                is_convex, simplified_formula = self._simplify_formula(
                    formula, ta_bool, ta
                )

                if is_convex:
                    # simplified formula is a conjuction of atoms (we're done)
                    yield ta, len(bool_atoms - ta_bool.keys())

                else:
                    # simplified formula is non-covex, requiring another enumeration pass
                    residual_atoms = list({a for a in simplified_formula.get_free_variables()
                                           if a.symbol_type() == smt.BOOL and a in bool_atoms})
                    residual_atoms.extend(list({a for a in simplified_formula.get_atoms()
                                                if a.is_theory_relation()}))

                    # may be both on LRA and boolean atoms
                    for ta_residual in self._get_allsat(simplified_formula, residual_atoms):
                        curr_ta = dict(ta)
                        curr_ta.update(ta_residual)
                        yield curr_ta, len(bool_atoms - curr_ta.keys())

    def _integrate_batch(self, convex_integrals, factors):
        results = self.integrator.integrate_batch(convex_integrals)
        volume = np.sum(results * factors, axis=-1)
        return volume


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
                left, right = equality.args()
                if left.is_symbol(smt.REAL):
                    alias, expr = left, right
                elif right.is_symbol(smt.REAL):
                    alias, expr = right, left
                else:
                    raise ValueError("Malformed alias {equality}")

                if alias in aliases:
                    msg = f"Multiple aliases {alias}:\n1) {expr}\n2) {aliases[alias]}"
                    raise ValueError(msg)

                aliases[alias] = expr
                for var in expr.get_free_variables():
                    Gsub.add_edge(alias, var)

                if len(expr.get_free_variables()) == 0: # constant handled separately
                    constants.update({alias: expr})

        # order of substitutions is determined by a topological sort of the digraph
        try:
            order = [node for node in nx.topological_sort(Gsub) if node in aliases]
        except nx.exception.NetworkXUnfeasible:
            raise ValueError("Cyclic aliases definition")

        convex_formula = smt.And(*inequalities)
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



    def _get_allsat(self, formula, atoms, force_total=False):

        """
        Gets the list of assignments that satisfy the formula.

        Args:
            formula (FNode): The formula to satisfy
            atoms (list): List of atoms on which to find the assignments.
            force_total (bool, optional): Forces total truth assignements.
                Defaults to False.

        Yields:
            list: assignments on the atoms
        """

        def _callback(model, converter, result):
            result.append([converter.back(v) for v in model])
            return 1

        msat_options = {
                "dpll.allsat_minimize_model": "true",
                "dpll.allsat_allow_duplicates": "false",
                "preprocessor.toplevel_propagation": "false",
                "preprocessor.simplification": "0",
            } if not force_total else {}

        # The current version of MathSAT returns a truth assignment on some
        # normalized version of the atoms instead of the original ones.
        # However, in order to simply get the value of the weight function
        # given a truth assignment, we need to know the truth assignment on
        # the original atoms.
        for atom in atoms:
            if not atom.is_symbol(smt.BOOL):
                _ = self.normalizer.normalize(atom, remember_alias=True)

        solver = smt.Solver(name="msat", solver_options=msat_options)
        converter = solver.converter
        solver.add_assertion(formula)

        # the MathSAT call returns models as conjunction of literals
        models = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in atoms],
            lambda model: _callback(model, converter, models),
        )

        # convert each conjunction of literals to a dict {atoms : bool}
        for model in models:
            assignments = {}
            for lit in model:
                atom = lit.arg(0) if lit.is_not() else lit
                value = not lit.is_not()

                if atom.is_symbol(smt.BOOL):
                    assignments[atom] = value
                else:
                    # retrieve the original (unnormalized) atom
                    normalized_atom, negated = self.normalizer.normalize(atom)
                    if negated:
                        value = not value
                    known_aliases = self.normalizer.known_aliases(normalized_atom)
                    for original_atom, negated in known_aliases:
                        assignments[original_atom] = (not value if negated else value)

            yield assignments

    def _simplify_formula(self, formula, subs, truth_assignment):
        """Substitute the subs in the formula and iteratively simplify it.
        truth_assignment is updated with unit-propagated atoms.

        Args:
            formula (FNode): The formula to simplify.
            subs (dict): Dictionary with the substitutions to perform.
            truth_assignment (dict): Dictionary with atoms and assigned value.

        Returns:
            bool: True if the formula is completely simplified.
            FNode: The simplified formula.
        """
        subs = {k: smt.Bool(v) for k, v in subs.items()}
        f_next = formula
        # iteratively simplify F[A<-mu^A], getting (possibly part.) mu^LRA
        while True:
            f_before = f_next
            f_next = self.simplifier.simplify(f_before.substitute(subs))
            lra_assignments, is_convex = WMISolver._plra_rec(f_next, True)
            subs = {k: smt.Bool(v) for k, v in lra_assignments.items()}
            truth_assignment.update(lra_assignments)
            if is_convex or lra_assignments == {}:
                break

        if not is_convex:
            # formula not completely simplified, add conjunction of assigned LRA atoms
            expressions = []
            for k, v in truth_assignment.items():
                if k.is_theory_relation():
                    if v:
                        expressions.append(k)
                    else:
                        expressions.append(smt.Not(k))
            f_next = smt.And([f_next] + expressions)
        return is_convex, f_next


    @staticmethod
    def _plra_rec(formula, pos_polarity):
        """This method extract all sub formulas in the formula and returns them as a dictionary.

        Args:
            formula (FNode): The formula to parse.
            pos_polarity (bool): The polarity of the formula.

        Returns:
            dict: the list of FNode in the formula with the corresponding truth value.
            bool: boolean that indicates if there are no more truth assignment to
                extract.

        """
        if formula.is_bool_constant():
            return {}, True
        elif formula.is_theory_relation() or formula.is_symbol(smt.BOOL):
            return {formula: pos_polarity}, True
        elif formula.is_not():
            return WMISolver._plra_rec(formula.arg(0), not pos_polarity)
        elif formula.is_and() and pos_polarity:
            assignments = {}
            is_convex = True
            for a in formula.args():
                assignment, rec_is_convex = WMISolver._plra_rec(a, True)
                assignments.update(assignment)
                is_convex = rec_is_convex and is_convex
            return assignments, is_convex
        elif formula.is_or() and not pos_polarity:
            assignments = {}
            is_convex = True
            for a in formula.args():
                assignment, rec_is_convex = WMISolver._plra_rec(a, False)
                assignments.update(assignment)
                is_convex = rec_is_convex and is_convex
            return assignments, is_convex
        elif formula.is_implies() and not pos_polarity:
            assignments, is_convex_left = WMISolver._plra_rec(formula.arg(0), True)
            assignment_right, is_convex_right = WMISolver._plra_rec(formula.arg(1), False)
            assignments.update(assignment_right)
            return assignments, is_convex_left and is_convex_right
        else:
            return {}, False


if __name__ == '__main__':

    from pysmt.shortcuts import *

if __name__ == '__main__':

    from pysmt.shortcuts import *
    from wmipa.datastructures import Polynomial, Polytope

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)

    variables = [x, y]

    h1 = LE(Real(0), x)
    h2 = LE(Real(0), y)
    h3 = LE(Plus(Times(Real(2), x), y), Real(1))
    h4 = LE(Plus(Times(Real(2), y), x), Real(1))

    chi = And(h1, h2, Or(h3, h4))
    w = Real(1) #Plus(x, y)    

    solver = WMISolver(chi, w)

    result = solver.computeWMI(Bool(True), variables)
    print("result", result)

    

    

