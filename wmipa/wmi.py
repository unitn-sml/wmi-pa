"""This module implements the Weighted Model Integration calculation.

The calculation leverages:
    - a Satisfiability Modulo Theories solver supporting All-SMT (e.g. MathSAT)
    - a software computing exact volume of polynomials (e.g. LattE Integrale)

Currently, three algorithms are supported:
    "BC" -- The baseline Block-Clause method.
    "AllSMT" -- Improves BC by leveraging the AllSAT feature of the SMT Solver.
    "PA" -- WMI with Predicate Abstraction, may reduce drastically the number of
        integrals computed.

"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

import mathsat
from pysmt.shortcuts import Real, Bool, And, Iff, Not, Solver, simplify, substitute, serialize
from pysmt.typing import BOOL, REAL
from math import fsum

from wmipa.latte_integrator import Latte_Integrator
from wmipa.weights import Weights
from wmipa import logger
from wmipa.utils import get_boolean_variables, get_real_variables
from wmipa.wmiexception import WMIRuntimeException, WMIParsingException
from wmipa.wmivariables import WMIVariables

class WMI:
    """The class that has the purpose to calculate the Weighted Module Integration of
        a given support, weight function and query.
    
    Attributes:
        variables (WMIVariables): The list of variables created and used by WMI.
        weights (Weights): The representation of the weight function.
        chi (FNode): The pysmt formula that contains the support of the formula
        integrator (Integrator): The integrator to use.
    
    """

    # WMI methods
    MODE_BC = "BC"
    MODE_ALLSMT = "AllSMT"
    MODE_PA = "PA"
    MODES = [MODE_BC, MODE_ALLSMT, MODE_PA]

    def __init__(self, chi, weight=Real(1), **options):
        """Default constructor.

        Args:
            chi (FNode): The support of the problem.
            weight (FNode, optional): The weight of the problem (default: 1).
            **options:
                - n_threads: The number of threads to use when computing WMI.
        
        """
        self.variables = WMIVariables()
        self.weights = Weights(weight, self.variables)
        self.chi = And(chi, self.weights.labelling)
        
        n_threads = options.get("n_threads")
        self.integrator = Latte_Integrator(n_threads = n_threads)
        
    def computeMI_batch(self, phis, **options):
        """Calculates the MI on a batch of queries.
        
        Args:
            phis (list(FNode)): The list of all the queries on which to calculate the MI.
            **options:
                - domA: set of pysmt vars encoding the Boolean integration domain (optional)
                - domX: set of pysmt vars encoding the real integration domain (optional)
                - mode: The mode to use when calculating MI.
                
        Returns:
            list(real): The list containing the result of each computation.
            list(int): The list containing the number of integrations for each computation that have been computed.
            
        """
        # save the old weight
        old_weights = self.weights
        old_variables = self.variables
        
        # calculate wmi with constant weight
        new_variables = WMIVariables()
        new_weights = Weights(Real(1), new_variables)
        self.weights = new_weights
        self.variables = new_variables
        
        volumes, integrations = self.computeWMI_batch(phis, **options)
        
        # restore old weight
        self.weights = old_weights
        self.variables = old_variables
        return volumes, integrations
              
    def computeWMI_batch(self, phis, **options):
        """Calculates the WMI on a batch of queries.
        
        Args:
            phis (list(FNode)): The list of all the queries on which to calculate the WMI.
            **options:
                - domA: set of pysmt vars encoding the Boolean integration domain (optional)
                - domX: set of pysmt vars encoding the real integration domain (optional)
                - mode: The mode to use when calculating WMI.
                
        Returns:
            list(real): The list containing the result of each computation.
            list(int): The list containing the number of integrations for each computation that have been computed.
            
        """
        volumes = []
        integrations = []
        
        for phi in phis:
            volume, n_integrations = self.computeWMI(phi, **options)
            volumes.append(volume)
            integrations.append(n_integrations)
            
        return volumes, integrations
        
    def computeMI(self, phi, **options):
        """Calculates the MI on a single query.
        
        Args:
            phi (FNode): The query on which to calculate the MI.
            **options:
                - domA: set of pysmt vars encoding the Boolean integration domain (optional)
                - domX: set of pysmt vars encoding the real integration domain (optional)
                - mode: The mode to use when calculating MI.
                
        Returns:
            real: The result of the computation.
            int: The number of integrations that have been computed.
            
        """
        # save old weight
        old_weights = self.weights
        old_variables = self.variables
        
        # calculate wmi with constant weight
        new_variables = WMIVariables()
        new_weights = Weights(Real(1), new_variables)
        self.weights = new_weights
        self.variables = new_variables
        
        volume, n_integrations = self.computeWMI(phi, **options)
        
        # restore old weight
        self.weights = old_weights
        self.variables = old_variables
        return volume, n_integrations

    def computeWMI(self, phi, **options):
        """Calculates the WMI on a single query.
        
        Args:
            phi (FNode): The query on which to calculate the WMI.
            **options:
                - domA: set of pysmt vars encoding the Boolean integration domain (optional)
                - domX: set of pysmt vars encoding the real integration domain (optional)
                - mode: The mode to use when calculating WMI.
                
        Returns:
            real: The result of the computation.
            int: The number of integrations that have been computed.
            
        """
        domA = options.get("domA")
        domX = options.get("domX")
        mode = options.get("mode")
        cache = options.get("cache")
        if mode is None:
            mode = WMI.MODE_PA
        if mode not in WMI.MODES:
            err = "{}, use one: {}".format(mode, ", ".join(WMI.MODES))
            logger.error(err)
            raise WMIRuntimeException(WMIRuntimeException.INVALID_MODE, err)
        if cache is None:
            cache = False
        self.cache = cache
        
        # Add the phi to the support
        formula = And(phi, self.chi)
        
        logger.debug("Computing WMI with mode: {}".format(mode))
        A = {x for x in get_boolean_variables(formula) if not self.variables.is_label(x)}
        x = get_real_variables(formula)
        
        # Currently, domX has to be the set of real variables in the
        # formula, whereas domA can be a superset of the boolean
        # variables A. The resulting volume is multiplied by 2^|domA - A|.
        factor = 1
        logger.debug("A: {}, domA: {}".format(A, domA))
        if domA != None:
            if len(A - domA) > 0:
                logger.error("Domain of integration mismatch: A - domA = {}".format(A - domA))
                raise WMIRuntimeException(WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH, A-domA)
            else:
                factor = 2**len(domA - A)

        logger.debug("factor: {}".format(factor))
        if domX != None and domX != x:
            logger.error("Domain of integration mismatch")
            raise WMIRuntimeException(WMIRuntimeException.DOMAIN_OF_INTEGRATION_MISMATCH, x-domX)

        compute_with_mode = {WMI.MODE_BC : self._compute_WMI_BC,
                             WMI.MODE_ALLSMT : self._compute_WMI_AllSMT,
                             WMI.MODE_PA : self._compute_WMI_PA}
                             
        volume, n_integrations, n_cached = compute_with_mode[mode](formula, self.weights)
            
        volume = volume * factor
        logger.debug("Volume: {}, n_integrations: {}, n_cached: {}".format(volume, n_integrations, n_cached))
            
        return volume, n_integrations

    @staticmethod
    def check_consistency(formula):
        """Checks if the formula has at least a total truth assignment
            which is both theory-consistent and it propositionally satisfies it.

        Args:
            formula (FNode): The pysmt formula to examine.
        
        Returns:
            bool: True if the formula satisfies the requirements, False otherwise.

        """
        for _ in WMI._model_iterator_base(formula):
            return True
        
        return False

    @staticmethod
    def _model_iterator_base(formula):
        """Finds all the total truth assignments that satisfy the given formula.
        
        Args:
            formula (FNode): The pysmt formula to examine.
            
        Yields:
            model: The model representing the next total truth assignment that satisfies the formula.
        
        """
        solver = Solver(name="msat")
        solver.add_assertion(formula)
        while solver.solve():
            model = solver.get_model()
            yield model
            atom_assignments = {a : model.get_value(a)
                                   for a in formula.get_atoms()}
                                   
            # Constrain the solver to find a different assignment
            solver.add_assertion(
                Not(And([Iff(var,val)
                         for var,val in atom_assignments.items()])))

    @staticmethod
    def _callback(model, converter, result):
        """Callback method usefull when performing AllSAT on a formula.
        
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

    def _compute_TTAs(self, formula):
        """Computes the total truth assignments of the given formula.
        
        This method first labels the formula and then uses the funtionality of mathsat called AllSAT to
            retrieve all the total truth assignments.
        
        Args:
            formula (FNode): The pysmt formula to examine.
        
        Returns:
            list: The list of all the total truth assignments.
            dict: The dictionary containing all the correspondence between the labels and their true value.
            
        """
        labels = {}
        expressions = []
        allsat_variables = set()
        
        # Label LRA atoms with fresh boolean variables
        labelled_formula, pa_vars, labels = self.label_formula(formula, formula.get_atoms())
        
        # Perform AllSMT on the labelled formula
        solver = Solver(name="msat")
        converter = solver.converter
        solver.add_assertion(labelled_formula)
        models = []
        mathsat.msat_all_sat(solver.msat_env(),
                        [converter.convert(v) for v in pa_vars],
                        lambda model : WMI._callback(model, converter, models))
        return models, labels

    def _compute_WMI_AllSMT(self, formula, weights):
        """Computes WMI using the AllSMT algorithm.
        
        This method retrieves all the total truth assignments of the given formula,
            it then calculates the weight for the assignments and finally asks the
            integrator to compute the integral of the problem.
            
        Args:
            formula (FNode): The pysmt formula on which to compute the WMI.
            weights (FNode): The pysmt formula representing the weight function.
            
        Returns:
            real: The final volume of the integral computed by summing up all the integrals' results.
            int: The number of problems that have been computed.
        
        """
        models, labels = self._compute_TTAs(formula)
        problems = []
        for index, model in enumerate(models):
            # retrieve truth assignments for the original atoms of the formula
            atom_assignments = {}
            for atom, value in WMI._get_assignments(model).items():
                if atom in labels:
                    atom = labels[atom]
                atom_assignments[atom] = value
            problem = self._create_problem(atom_assignments, weights)
            problems.append(problem)

        results, cached = self.integrator.integrate_batch(problems, self.cache)
        volume = fsum(results)
        return volume, len(problems)-cached, cached
    
    def _create_problem(self, atom_assignments, weights):
        """Create a tuple containing the problem to integrate.
        
        It first finds all the aliases in the atom_assignments and then it takes the actual weight (based on the assignment).
        Finally it creates the problem tuple with all the info in it.
        
        Args:
            atom_assignments (dict): The list of assignments and relative value (True, False)
            weights (Weight): The weight of the problem.
            
        Returns:
            tuple: The problem on which to calculate the integral formed by {atom assignment, actual weight, list of aliases}.
        
        """
        aliases = {}
        for atom, value in atom_assignments.items():
            if value is True and atom.is_equals():
                alias, expr = self._parse_alias(atom)
                
                # check that there are no multiple assignments of the same alias
                if not alias in aliases:
                    aliases[alias] = expr
                else:
                    msg = "Multiple assignments to the same alias"
                    raise WMIParsingException(WMIParsingException.MULTIPLE_ASSIGNMENT_SAME_ALIAS)
        
        current_weight, cond_assignments = weights.weight_from_assignment(atom_assignments)
        return (atom_assignments, current_weight, aliases, cond_assignments)
        
    def _parse_alias(self, equality):
        """Takes an equality and parses it.
        
        Args:
            equality (FNode): The equality to parse.
        
        Returns:
            alias (FNode): The name of the alias.
            expr (FNode): The value of the alias.
            
        Raises:
            WMIParsingException: If the equality is not of the type (Symbol = real_formula) or viceversa.
            
        """
        assert(equality.is_equals()), "Not an equality"
        left, right = equality.args()
        if left.is_symbol() and (left.get_type() == REAL):
            alias, expr = left, right
        elif right.is_symbol() and (right.get_type() == REAL):
            alias, expr = right, left
        else:
            raise WMIParsingException (WMIParsingException.MALFORMED_ALIAS_EXPRESSION, equality)
        return alias, expr
    
    def _compute_WMI_BC(self, formula, weights):
        """Computes WMI using the Block Clause algorithm.
        
        This method retrieves all the total truth assignments of the given formula one by one
            thanks to the Block Clause algorithm. This particular algorithm finds a model that
            satisfy the formula, it then add the negation of this model to the formula itself
            in order to constrain the solver to fine another model that satisfies it.
            
        Args:
            formula (FNode): The pysmt formula on which to compute the WMI.
            weights (FNode): The pysmt formula representing the weight function.
            
        Returns:
            real: The final volume of the integral computed by summing up all the integrals' results.
            int: The number of problems that have been computed.
        
        """
        problems = []
        for index, model in enumerate(WMI._model_iterator_base(formula)):
            atom_assignments = {a : model.get_value(a).constant_value()
                                   for a in formula.get_atoms()}
            problem = self._create_problem(atom_assignments, weights)
            problems.append(problem)

        results, cached = self.integrator.integrate_batch(problems, self.cache)
        volume = fsum(results)
        return volume, len(problems)-cached, cached
        
    def _compute_WMI_PA_no_boolean(self, lab_formula, pa_vars, labels, other_assignments={}):
        """Finds all the assignments that satisfy the given formula using AllSAT.
            
        Args:
            lab_formula (FNode): The labelled pysmt formula to examine.
            pa_vars (): 
            labels (dict): The dictionary containing the correlation between each label and their
                true value.
            
        Yields:
            dict: One of the assignments that satisfies the formula.
        
        """
        solver = Solver(name="msat",
                    solver_options={"dpll.allsat_minimize_model" : "true"})
        converter = solver.converter
        solver.add_assertion(lab_formula)
        lra_assignments = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in pa_vars],
            lambda model : WMI._callback(model, converter, lra_assignments))
        for mu_lra in lra_assignments:                    
            assignments = {}
            for atom, value in WMI._get_assignments(mu_lra).items():
                if atom in labels:
                    atom = labels[atom]
                assignments[atom] = value
            assignments.update(other_assignments)
            yield assignments

    def _compute_WMI_PA(self, formula, weights):
        """Computes WMI using the Predicate Abstraction (PA) algorithm.
        
        Args:
            formula (FNode): The formula on whick to compute WMI.
            weights (Weight): The corresponding weight.
            
        Returns:
            real: The final volume of the integral computed by summing up all the integrals' results.
            int: The number of problems that have been computed.
        
        """
        problems = []
        boolean_variables = get_boolean_variables(formula)
        if len(boolean_variables) == 0:
            # Enumerate partial TA over theory atoms
            lab_formula, pa_vars, labels = self.label_formula(formula, formula.get_atoms())
            # Predicate abstraction on LRA atoms with minimal models
            for assignments in self._compute_WMI_PA_no_boolean(lab_formula, pa_vars, labels):
                problem = self._create_problem(assignments, weights)
                problems.append(problem)
        else:
            solver = Solver(name="msat")
            converter = solver.converter
            solver.add_assertion(formula)
            boolean_models = []
            # perform AllSAT on the Boolean variables
            mathsat.msat_all_sat(
                solver.msat_env(),
                [converter.convert(v) for v in boolean_variables],
                lambda model : WMI._callback(model, converter, boolean_models))

            logger.debug("n_boolean_models: {}".format(len(boolean_models)))
            # for each boolean assignment mu^A of F        
            for model in boolean_models:
                atom_assignments = {}
                boolean_assignments = WMI._get_assignments(model)
                atom_assignments.update(boolean_assignments)
                subs = {k : Bool(v) for k, v in boolean_assignments.items()}
                f_next = formula
                # iteratively simplify F[A<-mu^A], getting (possibily part.) mu^LRA
                while True:            
                    f_before = f_next
                    f_next = simplify(substitute(f_before, subs))
                    lra_assignments, over = WMI._parse_lra_formula(f_next)
                    subs = {k : Bool(v) for k, v in lra_assignments.items()}
                    atom_assignments.update(lra_assignments)
                    if over or lra_assignments == {}:
                        break
                if not over:
                    # predicate abstraction on LRA atoms with minimal models
                    lab_formula, pa_vars, labels = self.label_formula(f_next, f_next.get_atoms())
                    expressions = []
                    for k, v in atom_assignments.items():
                        if k.is_theory_relation():
                            if v:
                                expressions.append(k)
                            else:
                                expressions.append(Not(k))
                                                
                    lab_formula = And([lab_formula] + expressions)
                    for assignments in self._compute_WMI_PA_no_boolean(lab_formula, pa_vars, labels, atom_assignments):
                        problem = self._create_problem(assignments, weights)
                        problems.append(problem)
                else:
                    # integrate over mu^A & mu^LRA
                    problem = self._create_problem(atom_assignments, weights)
                    problems.append(problem)

        results, cached = self.integrator.integrate_batch(problems, self.cache)
        volume = fsum(results)
        return volume, len(problems)-cached, cached

    def label_formula(self, formula, atoms_to_label):
        """Labels every atom in the input with a new fresh WMI variable.
        
        Args:
            formula (FNode): The formula containing the atoms.
            atoms_to_label (list): The list of atoms to assign a new label.
            
        Returns:
            labelled_formula (FNode): The formula with the labels in it and their respective atoms.
            pa_vars (set): The list of all the atoms_to_label (as labels).
            labels (dict): The list of the labels and corrispondent atom assigned to it.
        
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
        """Retrieve the assignments (formula: truth value) from a list of literals (positive or negative).
        
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
            assert(atom.is_theory_relation or
                   (atom.is_symbol() and atom.get_type() == BOOL))
            assignments[atom] = value
            
        return assignments

    @staticmethod
    def _parse_lra_formula(formula):
        """Wrapper for _plra_rec.
        
        Args:
            formula (FNode): The formula to parse.
        
        Returns:
            dict: the list of FNode in the formula with the corresponding truth value.
            bool: boolean that indicates if there are no more truth assignment to extract.
            
        """
        return WMI._plra_rec(formula, True)

    @staticmethod
    def _plra_rec(formula, pos_polarity):
        """This method extract all sub formulas in the formula and returns them as a dictionary.
        
        Args:
            formula (FNode): The formula to parse.
            pos_polarity (bool): The polarity of the formula.
        
        Returns:
            dict: the list of FNode in the formula with the corresponding truth value.
            bool: boolean that indicates if there are no more truth assignment to extract.
            
        """
        if formula.is_bool_constant():
            return {}, True            
        elif formula.is_theory_relation():
            return {formula : pos_polarity}, True
        elif formula.is_not():
            return WMI._plra_rec(formula.arg(0), not pos_polarity)
        elif formula.is_and() and pos_polarity:
            assignments = {}
            over = True
            for a in formula.args():
                assignment, rec_over = WMI._plra_rec(a, True)
                assignments.update(assignment)
                over = rec_over and over
            return assignments, over
        elif formula.is_or() and not pos_polarity:
            assignments = {}
            over = True
            for a in formula.args():
                assignment, rec_over = WMI._plra_rec(a, False) 
                assignments.update(assignment)
                over = rec_over and over
            return assignments, over
        elif formula.is_implies() and not pos_polarity:
            assignments, over_left = WMI._plra_rec(formula.arg(0), True)
            assignment_right, over_right = WMI._plra_rec(formula.arg(1), False)
            assignments.update(assignment_right)
            return assignments, over_left and over_right
        else:
            return {}, False

