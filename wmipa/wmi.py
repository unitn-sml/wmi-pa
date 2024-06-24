"""This module implements the Weighted Model Integration calculation.

The calculation leverages:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a software computing exact volume of polynomials (e.g. LattE Integrale)

"""

__version__ = "1.0"
__author__ = "Gabriele Masina, Paolo Morettin, Giuseppe Spallitta"

import mathsat
import numpy as np
from pysmt.shortcuts import And, Bool, Iff, Implies, Not, Real, Solver, serialize, simplify, substitute
from pysmt.typing import BOOL, REAL

from wmipa.integration import LatteIntegrator
from wmipa.integration.integrator import Integrator
from wmipa.log import logger
from wmipa.utils import TermNormalizer, BooleanSimplifier
from wmipa.weights import Weights
from wmipa.wmiexception import WMIParsingException, WMIRuntimeException
from wmipa.wmivariables import WMIVariables


class WMISolver:
    """The class that has the purpose to calculate the Weighted Module Integration of
        a given support, weight function and query.

    Attributes:
        variables (WMIVariables): The list of variables created and used by WMISolver.
        weights (Weights): The representation of the weight function.
        chi (FNode): The pysmt formula that contains the support of the formula
        integrator (Integrator or list(Integrator)): The integrator or the list of integrators to use.
        simplifier (BooleanSimplifier): The class that simplifies the formula.
        normalizer (TermNormalizer): The class that normalizes LRA atoms.

    """

    def __init__(self, chi, w=Real(1), integrator=None):
        """Default constructor.

        Args:
            chi (FNode): The support of the problem.
            w (FNode, optional): The weight function of the problem (default: 1).
            integrator (Integrator or list(Integrator)): integrator or list of integrators to use. If a list of
                integrators is provided, then computeWMI will return a list of results, one for each integrator.
                (default: LatteIntegrator())

        """
        self.variables = WMIVariables()
        self.weights = Weights(w, self.variables)
        self.chi = chi

        self.normalizer = TermNormalizer()
        self.integrator = integrator if integrator is not None else LatteIntegrator()
        self.simplifier = BooleanSimplifier()


    def computeWMI(self, phi, domain, cache=-1):
        """Calculates the WMI on a single query.

        Args:
            phi (FNode): The query on which to calculate the WMI.
            domain (set(FNode)): set of pysmt REAL vars encoding the integration domain
            cache (int, optional): The cache level to use when calculating WMI (default: -1 = no cache).

        Returns:
            real or np.ndarray(real): The result of the computation. If a list of integrators is provided, then the
                result is a np.ndarray(real) containing the results computed by the different integrators.
            int or np.ndarray(real): The number of integrations that have been computed. If a list of integrators is
                provided, then the result is a np.ndarray(int) containing the number of integrations computed by the
                different integrators.

        """
        # domain of integration
        self.domain = domain

        # conjoin query, support and the skeleton of the weight function
        formula = And(phi, self.chi, self.weights.weights_as_formula_sk)

        logger.debug(f"Computing WMI (integration domain: {domain})")

        # sorting the different atoms
        cnf_labels, bool_atoms, lra_atoms = {}, {}, {}
        for atom in formula.get_atoms():
            if atom.is_symbol():
                assert(atom.symbol_type() == BOOL)
                if self.variables.is_cnf_label(atom):
                    cnf_labels.add(atom)
                else:
                    bool_atoms.add(atom)
            elif atom.is_theory_relation():
                lra_atoms.add(atom)
            else:
                raise NotImplementedError()

        # number of booleans not assigned in each problem
        n_bool_not_assigned = []
        problems = []

        if len(bool_atoms) == 0:
            # Enumerate partial TA over theory atoms
            for assignments in self._get_allsat(formula, use_ta=True, atoms=lra_atoms):
                problem = self._create_problem(assignments)
                problems.append(problem)
                n_bool_not_assigned.append(0)

        else:
            for boolean_assignments in self._get_allsat(formula, use_ta=True, atoms=bool_atoms):
                atom_assignments = dict(boolean_assignments)

                # simplify the formula
                fully_simplified, res_formula = self._simplify_formula(
                    formula, boolean_assignments, atom_assignments
                )

                if not fully_simplified:
                    # boolean variables first (discard cnf labels)
                    residual_atoms = list({a for a in res_formula.get_free_variables() if a.symbol_type() == BOOL and a in bool_atoms}) + \
                                     list({a for a in res_formula.get_atoms() if a.is_theory_relation()})

                    # may be both on LRA and boolean atoms
                    residual_models = self._get_allsat(
                        res_formula, use_ta=True, atoms=residual_atoms
                    )
                    for residual_assignments in residual_models:
                        curr_atom_assignments = dict(atom_assignments)
                        curr_atom_assignments.update(residual_assignments)

                        b_not_assigned = bool_atoms - curr_atom_assignments.keys()

                        problem = self._create_problem(curr_atom_assignments)
                        problems.append(problem)
                        n_bool_not_assigned.append(len(b_not_assigned))
                else:
                    b_not_assigned = bool_atoms - boolean_assignments.keys()

                    problem = self._create_problem(atom_assignments)
                    problems.append(problem)
                    n_bool_not_assigned.append(len(b_not_assigned))

        # multiply each volume by 2^(|A| - |mu^A|)
        factors = [2 ** i for i in n_bool_not_assigned]
        volume, n_cached = self._integrate_batch(problems, cache, factors)
        n_integrations = len(problems) - cached
        
        logger.debug(f"Volume: {volume}, n_integrations: {n_integrations}, n_cached: {n_cached}")

        return volume, n_integrations


    def _integrate_batch(self, problems, cache, factors=None):
        """Computes the integral of a batch of problems.

        Args:
            problems (list): The list of problems to integrate.
            cache (int): The cache level to use.
            factors (list, optional): A list of factor each problem should be multiplied by. Defaults to [1] * len(problems).

        """
        if factors is None:
            factors = [1] * len(problems)
        else:
            assert isinstance(factors, list)
            assert len(problems) == len(factors)
        if isinstance(self.integrator, Integrator):
            results, cached = self.integrator.integrate_batch(problems, cache)
        else:
            results, cached = zip(*(i.integrate_batch(problems, cache) for i in self.integrator))
        cached = np.array(cached)
        results = np.array(results)
        volume = np.sum(results * factors, axis=-1)
        return volume, cached



    def _create_problem(self, atom_assignments):
        """Create a tuple containing the problem to integrate.

        It first finds all the aliases in the atom_assignments, then it takes the
            actual weight (based on the assignment).
        Finally, it creates the problem tuple with all the info in it.

        Args:
            atom_assignments (dict): Maps atoms to the corresponding truth value (True, False)

        Returns:
            tuple: The problem on which to calculate the integral formed by
                (atom assignment, actual weight, list of aliases, weight condition assignments)

        """
        aliases = {}
        for atom, value in atom_assignments.items():
            if value is True and atom.is_equals():
                alias, expr = self._parse_alias(atom)
                if self.variables.is_weight_alias(alias):
                    continue

                # check that there are no multiple assignments of the same alias
                if alias not in aliases:
                    aliases[alias] = expr
                else:
                    raise WMIParsingException(WMIParsingException.MULTIPLE_ASSIGNMENT_SAME_ALIAS)

        current_weight, cond_assignments = self.weights.weight_from_assignment(atom_assignments)
        return atom_assignments, current_weight, aliases, cond_assignments

    def _parse_alias(self, equality):
        """Takes an equality and parses it.

        Args:
            equality (FNode): The equality to parse.

        Returns:
            alias (FNode): The name of the alias.
            expr (FNode): The value of the alias.

        Raises:
            WMIParsingException: If the equality is not of the type
                (Symbol = real_formula) or vice-versa.

        """
        assert equality.is_equals(), "Not an equality"
        left, right = equality.args()
        if left.is_symbol() and (left.get_type() == REAL):
            alias, expr = left, right
        elif right.is_symbol() and (right.get_type() == REAL):
            alias, expr = right, left
        else:
            raise WMIParsingException(
                WMIParsingException.MALFORMED_ALIAS_EXPRESSION, equality
            )
        return alias, expr



    def _get_allsat(self, formula, use_ta=False, atoms=None):
        """
        Gets the list of assignments that satisfy the formula.

        Args:
            formula (FNode): The formula to satisfy
            use_ta (bool, optional): Uses partial assignments.
                Defaults to False.
            atoms (list, optional): List of atoms on which to find the assignments.
                Defaults to the boolean atoms of the formula.

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
            } if use_ta else {}

        if atoms is None:
            atoms = {a for a in formula.get_free_variables()
                     if a.symbol_type() == BOOL}

        # The current version of MathSAT returns a truth assignment on some
        # normalized version of the atoms instead of the original ones.
        # However, in order to simply get the value of the weight function
        # given a truth assignment, we need to know the truth assignment on
        # the original atoms.

        for atom in atoms:
            if not atom.is_symbol(BOOL):
                _ = self.normalizer.normalize(atom, remember_alias=True)

        solver = Solver(name="msat", solver_options=msat_options)
        converter = solver.converter
        solver.add_assertion(formula)

        models = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in atoms],
            lambda model: _callback(model, converter, models),
        )

        for model in models:
            # convert list of literals to dict {atoms -> bool}
            assignments = {}
            for lit in model:

                atom = lit.arg(0) if lit.is_not() else lit
                value = not lit.is_not()

                if atom.is_symbol(BOOL):
                    assignments[atom] = value
                else:
                    normalized_atom, negated = self.normalizer.normalize(atom)
                    if negated:
                        value = not value
                    known_aliases = self.normalizer.known_aliases(normalized_atom)
                    for original_atom, negated in known_aliases:
                        assignments[original_atom] = (not value if negated else value)

            yield assignments



    def _simplify_formula(self, formula, subs, atom_assignments):
        """Substitute the subs in the formula and iteratively simplify it.
        atom_assignments is updated with unit-propagated atoms.

        Args:
            formula (FNode): The formula to simplify.
            subs (dict): Dictionary with the substitutions to perform.
            atom_assignments (dict): Dictionary with atoms and assigned value.

        Returns:
            bool: True if the formula is completely simplified.
            FNode: The simplified formula.
        """
        subs = {k: Bool(v) for k, v in subs.items()}
        f_next = formula
        # iteratively simplify F[A<-mu^A], getting (possibly part.) mu^LRA
        while True:
            f_before = f_next
            f_next = self.simplifier.simplify(substitute(f_before, subs))
            lra_assignments, fully_simplified = WMISolver._plra_rec(f_next, True)
            subs = {k: Bool(v) for k, v in lra_assignments.items()}
            atom_assignments.update(lra_assignments)
            if fully_simplified or lra_assignments == {}:
                break

        if not fully_simplified:
            # formula not completely simplified, add conjunction of assigned LRA atoms
            expressions = []
            for k, v in atom_assignments.items():
                if k.is_theory_relation():
                    if v:
                        expressions.append(k)
                    else:
                        expressions.append(Not(k))
            f_next = And([f_next] + expressions)
        return fully_simplified, f_next


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
        elif formula.is_theory_relation() or formula.is_symbol(BOOL):
            return {formula: pos_polarity}, True
        elif formula.is_not():
            return WMISolver._plra_rec(formula.arg(0), not pos_polarity)
        elif formula.is_and() and pos_polarity:
            assignments = {}
            fully_simplified = True
            for a in formula.args():
                assignment, rec_fully_simplified = WMISolver._plra_rec(a, True)
                assignments.update(assignment)
                fully_simplified = rec_fully_simplified and fully_simplified
            return assignments, fully_simplified
        elif formula.is_or() and not pos_polarity:
            assignments = {}
            fully_simplified = True
            for a in formula.args():
                assignment, rec_fully_simplified = WMISolver._plra_rec(a, False)
                assignments.update(assignment)
                fully_simplified = rec_fully_simplified and fully_simplified
            return assignments, fully_simplified
        elif formula.is_implies() and not pos_polarity:
            assignments, fully_simplified_left = WMISolver._plra_rec(formula.arg(0), True)
            assignment_right, fully_simplified_right = WMISolver._plra_rec(formula.arg(1), False)
            assignments.update(assignment_right)
            return assignments, fully_simplified_left and fully_simplified_right
        else:
            return {}, False
