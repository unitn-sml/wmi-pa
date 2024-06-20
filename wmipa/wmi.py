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
from wmipa.utils import get_boolean_variables, get_lra_atoms, get_real_variables, TermNormalizer, BooleanSimplifier
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

    def __init__(self, chi, weight=Real(1), integrator=None):
        """Default constructor.

        Args:
            chi (FNode): The support of the problem.
            weight (FNode, optional): The weight function of the problem (default: 1).
            integrator (Integrator or list(Integrator)): integrator or list of integrators to use. If a list of
                integrators is provided, then computeWMI will return a list of results, one for each integrator.
                (default: LatteIntegrator())

        """
        self.variables = WMIVariables()
        self.normalizer = TermNormalizer()
        self.weights = Weights(weight, self.variables)
        self.chi = chi

        if integrator is None:
            integrator = LatteIntegrator()
        if not isinstance(integrator, Integrator) and not (
                isinstance(integrator, list) and all(isinstance(i, Integrator) for i in integrator)):
            raise TypeError("integrator must be an Integrator or a list of Integrator")
        self.integrator = integrator

        self.simplifier = BooleanSimplifier()


    def computeWMI(self, phi, **options):
        """Calculates the WMI on a single query.

        Args:
            phi (FNode): The query on which to calculate the WMI.
            **options:
                - domA: set of pysmt vars encoding the Boolean integration domain
                    (optional)
                - domX: set of pysmt vars encoding the real integration domain
                    (optional)
                - cache: The cache level to use when calculating WMI (default: -1). See wmipa.integration.CacheIntegrator`
                    for more details.

        Returns:
            real or np.ndarray(real): The result of the computation. If a list of integrators is provided, then the
                result is a np.ndarray(real) containing the results computed by the different integrators.
            int or np.ndarray(real): The number of integrations that have been computed. If a list of integrators is
                provided, then the result is a np.ndarray(int) containing the number of integrations computed by the
                different integrators.

        """
        domA = options.get("domA")
        domX = options.get("domX")
        cache = options.get("cache", -1)

        formula = And(phi, self.chi)

        # Add the skeleton encoding to the support
        formula = And(formula, self.weights.weights_as_formula_sk)

        logger.debug("Computing WMI")
        x = {x for x in get_real_variables(formula) if not self.variables.is_weight_alias(x)}
        A = {x for x in get_boolean_variables(formula) if
             not self.variables.is_label(x) and not self.variables.is_cnf_label(x)}

        # Currently, domX has to be the set of real variables in the
        # formula, whereas domA can be a superset of the boolean
        # variables A. The resulting volume is multiplied by 2^|domA - A|.
        factor = 1
        logger.debug("A: {}, domA: {}".format(A, domA))
        if domA is not None:
            if len(A - domA) > 0:
                logger.error("Domain of integration mismatch: A - domA = {}".format(A - domA))
                raise WMIRuntimeException(WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH, A - domA)
            else:
                factor = 2 ** len(domA - A)

        logger.debug("factor: {}".format(factor))
        if domX is not None and domX != x:
            logger.error("Domain of integration mismatch")
            raise WMIRuntimeException(WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH, x - domX)

        volume, n_integrations, n_cached = self._compute_WMI_SAE4WMI(formula, self.weights, cache)

        volume = volume * factor
        logger.debug("Volume: {}, n_integrations: {}, n_cached: {}".format(volume, n_integrations, n_cached))

        return volume, n_integrations


    @staticmethod
    def _callback(model, converter, result):
        """Callback method useful when performing AllSAT on a formula.

        This method takes the model, converts it into a more suitable form and finally
            adds it into the given results list.

        Args:
            model (list): The model created by the solver.
            converter: The class that converts the model.
            result (list): The list where to append the converted model.

        Returns:
            int: 1 (This method requires to return an integer)

        """
        py_model = [converter.back(v) for v in model]
        result.append(py_model)
        return 1


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



    def _create_problem(self, atom_assignments, weights, on_labels=True):
        """Create a tuple containing the problem to integrate.

        It first finds all the aliases in the atom_assignments, then it takes the
            actual weight (based on the assignment).
        Finally, it creates the problem tuple with all the info in it.

        Args:
            atom_assignments (dict): Maps atoms to the corresponding truth value (True, False)
            weights (Weight): The weight function of the problem.
            on_labels (bool): If True assignment is expected to be over labels of weight condition otherwise it is
                expected to be over unlabelled conditions

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

        current_weight, cond_assignments = weights.weight_from_assignment(
            atom_assignments, on_labels=on_labels
        )
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



    def _get_allsat(self, formula, use_ta=False, atoms=None, options=None):
        """
        Gets the list of assignments that satisfy the formula.

        Args:
            formula (FNode): The formula to satisfy
            use_ta (bool, optional): If true the assignments can be partial.
                Defaults to False.
            atoms (list, optional): List of atoms on which to find the assignments.
                Defaults to the boolean atoms of the formula.

        Yields:
            list: assignments on the atoms
        """
        if options is None:
            options = {}
        if use_ta:
            solver_options = {
                "dpll.allsat_minimize_model": "true",
                "dpll.allsat_allow_duplicates": "false",
                "preprocessor.toplevel_propagation": "false",
                "preprocessor.simplification": "0",
            }
        else:
            solver_options = {}

        solver_options.update(options)
        if atoms is None:
            atoms = get_boolean_variables(formula)

        # The current version of MathSAT returns a truth assignment on some normalized version of the atoms instead of
        # the original ones. However, in order to simply get the value of the weight function given a truth assignment,
        # we need to know the truth assignment on the original atoms.
        for atom in atoms:
            if not atom.is_symbol(BOOL):
                _ = self.normalizer.normalize(atom, remember_alias=True)

        solver = Solver(name="msat", solver_options=solver_options)
        converter = solver.converter
        solver.add_assertion(formula)

        models = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in atoms],
            lambda model: WMISolver._callback(model, converter, models),
        )

        for model in models:
            assignments = {}
            for atom, value in WMISolver._get_assignments(model).items():
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
            lra_assignments, over = WMISolver._parse_lra_formula(f_next)
            subs = {k: Bool(v) for k, v in lra_assignments.items()}
            atom_assignments.update(lra_assignments)
            if over or lra_assignments == {}:
                break

        if not over:
            # formula not completely simplified, add conjunction of assigned LRA atoms
            expressions = []
            for k, v in atom_assignments.items():
                if k.is_theory_relation():
                    if v:
                        expressions.append(k)
                    else:
                        expressions.append(Not(k))
            f_next = And([f_next] + expressions)
        return over, f_next


    def _compute_WMI_SAE4WMI(self, formula, weights, cache):
        """Computes WMI using the Predicate Abstraction (PA) algorithm using Structure
            Awareness and Skeleton.

        Args:
            formula (FNode): The formula on which to compute WMI.
            weights (Weight): The corresponding weight.
            cache (int): The cache level to use.

        Returns:
            real or np.ndarray(real): The final volume of the integral computed by summing up all the integrals' results.
                If a list of integrators is provided, then a numpy array of results is returned, one for each integrator.
            int or np.ndarray(int): The number of problems that have been computed. If a list of integrators is provided,
                then a numpy array of results is returned, one for each integrator.
            int or np.ndarray(int): The number of problems that have been retrieved from the cache. If a list of integrators
                is provided, then a numpy array of results is returned, one for each integrator.

        """
        problems = []

        cnf_labels = {b for b in get_boolean_variables(formula) if
                      self.variables.is_cnf_label(b) or self.variables.is_cond_label(b)}
        boolean_variables = get_boolean_variables(formula) - cnf_labels
        lra_atoms = get_lra_atoms(formula)

        # number of booleans not assigned in each problem
        n_bool_not_assigned = []

        if len(boolean_variables) == 0:
            # Enumerate partial TA over theory atoms
            for assignments in self._get_allsat(formula, use_ta=True, atoms=lra_atoms):
                problem = self._create_problem(assignments, weights, on_labels=False)
                problems.append(problem)
                n_bool_not_assigned.append(0)

        else:
            boolean_models = self._get_allsat(
                formula, use_ta=True, atoms=boolean_variables,
            )

            for boolean_assignments in boolean_models:
                atom_assignments = dict(boolean_assignments)

                # simplify the formula
                over, res_formula = self._simplify_formula(
                    formula, boolean_assignments, atom_assignments
                )

                if not over:
                    # boolean variables first (discard cnf labels)
                    residual_atoms = list(get_boolean_variables(res_formula).intersection(boolean_variables)) + \
                                     list(get_lra_atoms(res_formula))

                    # may be both on LRA and boolean atoms
                    residual_models = self._get_allsat(
                        res_formula, use_ta=True, atoms=residual_atoms
                    )
                    for residual_assignments in residual_models:
                        curr_atom_assignments = dict(atom_assignments)
                        curr_atom_assignments.update(residual_assignments)

                        b_not_assigned = boolean_variables - curr_atom_assignments.keys()

                        problem = self._create_problem(
                            curr_atom_assignments, weights, on_labels=False
                        )
                        problems.append(problem)
                        n_bool_not_assigned.append(len(b_not_assigned))
                else:
                    b_not_assigned = boolean_variables - boolean_assignments.keys()

                    problem = self._create_problem(
                        atom_assignments, weights, on_labels=False
                    )
                    problems.append(problem)
                    n_bool_not_assigned.append(len(b_not_assigned))

        # multiply each volume by 2^(|A| - |mu^A|)
        factors = [2 ** i for i in n_bool_not_assigned]
        volume, cached = self._integrate_batch(problems, cache, factors)
        return volume, len(problems) - cached, cached

    def label_formula(self, formula, atoms_to_label):
        """Labels every atom in the input with a new fresh WMI variable.

        Args:
            formula (FNode): The formula containing the atoms.
            atoms_to_label (list): The list of atoms to assign a new label.

        Returns:
            labelled_formula (FNode): The formula with the labels in it and their
                respective atoms.
            pa_vars (set): The list of all the atoms_to_label (as labels).
            labels (dict): The list of the labels and correspondent atom assigned to it.

        """
        expressions = []
        labels = {}
        pa_vars = set()
        j = 0
        for a in atoms_to_label:
            if a.is_theory_relation():
                label_a = self.variables.new_wmi_label(j)
                j += 1
                expressions.append(Iff(label_a, a))
                labels[label_a] = a
                pa_vars.add(label_a)
            else:
                pa_vars.add(a)

        labelled_formula = And([formula] + expressions)

        return labelled_formula, pa_vars, labels

    @staticmethod
    def _get_assignments(literals):
        """Retrieve the assignments (formula: truth value) from a list of literals
            (positive or negative).

        Args:
            literals (list): The list of the literals.

        Returns:
            assignments (dict): The list of atoms and corresponding truth value.

        """
        assignments = {}
        for literal in literals:
            if literal.is_not():
                value = False
                atom = literal.arg(0)
            else:
                value = True
                atom = literal
            assert atom.is_theory_relation or (atom.is_symbol() and atom.get_type() == BOOL)
            assignments[atom] = value

        return assignments

    @staticmethod
    def _parse_lra_formula(formula):
        """Wrapper for _plra_rec.

        Args:
            formula (FNode): The formula to parse.

        Returns:
            dict: the list of FNode in the formula with the corresponding truth value.
            bool: boolean that indicates if there are no more truth assignment to
                extract.

        """
        return WMISolver._plra_rec(formula, True)

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
            over = True
            for a in formula.args():
                assignment, rec_over = WMISolver._plra_rec(a, True)
                assignments.update(assignment)
                over = rec_over and over
            return assignments, over
        elif formula.is_or() and not pos_polarity:
            assignments = {}
            over = True
            for a in formula.args():
                assignment, rec_over = WMISolver._plra_rec(a, False)
                assignments.update(assignment)
                over = rec_over and over
            return assignments, over
        elif formula.is_implies() and not pos_polarity:
            assignments, over_left = WMISolver._plra_rec(formula.arg(0), True)
            assignment_right, over_right = WMISolver._plra_rec(formula.arg(1), False)
            assignments.update(assignment_right)
            return assignments, over_left and over_right
        else:
            return {}, False
