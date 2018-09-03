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

from math import fsum
from functools import partial
from multiprocessing import Pool

import mathsat
from pysmt.shortcuts import *
from pysmt.typing import BOOL, REAL
from pysmt.fnode import FNode

from wmipa import Integrator
from wmipa import Weights

from wmipa.logger import  get_sublogger
from wmipa.pysmt2latte import Polytope, Polynomial
from wmipa.utils import is_label, new_wmi_label, \
    get_boolean_variables, get_real_variables
from wmipa.wmiexception import WMIParsingError, WMIRuntimeException



# apparently Pool.map requires an unbound top-level method, here it is
def integrate_worker(obj, integrand_polytope_index):
    integrand, polytope, index = integrand_polytope_index
    volume =  obj.integrator.integrate(integrand, polytope, index)
    if volume == None :
        return 0.0
    else:
        return volume


class WMI:

    # WMI methods
    MODE_BC = "BC"
    MODE_ALLSMT = "AllSMT"
    MODE_PA = "PA"    
    MODES = [MODE_BC, MODE_ALLSMT, MODE_PA]

    # default number of threads used
    DEF_THREADS = 7

    # the following two methods were overwritten to allow the serialization
    # of the class instances (logger contains unserializable data structures).
    # serialization is necessary for multiprocessing.
    
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        return d
    def __setstate__(self, d):
        self.__dict__.update(d) 
    
    def __init__(self, n_threads=None):
        """Default constructor.

        Keyword arguments:
        n_threads -- number of threads (optional)

        """
        self.logger = get_sublogger(__name__)
        self.integrator = Integrator()
        self.n_threads = WMI.DEF_THREADS if n_threads == None else n_threads

    def compute(self, formula, weights, mode, domA=None, domX=None):
        """Computes WMI(formula, weights, X, A). Returns the result and the
        number of integrations performed.

        Keyword arguments:
        formula -- pysmt formula
        weights -- Weights instance encoding the FIUC weight function
        mode -- string in WMI.MODES
        domA -- set of pysmt vars encoding the Boolean integration domain (optional)
        domX -- set of pysmt vars encoding the real integration domain (optional)

        """
            
        self.logger.debug("Computing WMI with mode: {}".format(mode))
        A = {x for x in get_boolean_variables(formula) if not is_label(x)}
        x = get_real_variables(formula)
        dom_msg = "The domain of integration of the numerical variables" +\
                  " should be x. The domain of integration of the Boolean" +\
                  " variables should be a superset of A."

        # Currently, domX has to be the set of real variables in the
        # formula, whereas domA can be a superset of the boolean
        # variables A. The resulting volume is multiplied by 2^|domA - A|.
        factor = 1
        self.logger.debug("A: {}, domA: {}".format(A, domA))
        if domA != None:
            if len(A - domA) > 0:
                self.logger.error(dom_msg + "A - domA = {}".format(A - domA))
                raise WMIRuntimeException(dom_msg)
            else:
                factor = 2**len(domA - A)


        self.logger.debug("factor: {}".format(factor))
        if domX != None and not set(domX) == x:
            self.logger.error(dom_msg)
            raise WMIRuntimeException(dom_msg) 
            

        compute_with_mode = {WMI.MODE_BC : self._compute_WMI_BC,
                             WMI.MODE_ALLSMT : self._compute_WMI_AllSMT,
                             WMI.MODE_PA : self._compute_WMI_PA}

        try:
            volume, n_integrations = compute_with_mode[mode](formula, weights)
        except KeyError:
            msg = "Invalid mode, use one: " + ", ".join(WMI.MODES)
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        volume = volume * factor
        self.logger.debug("Volume: {}, n_integrations: {}".format(
            volume, n_integrations))

        return volume, n_integrations

    def enumerate_TTAs(self, formula, weights, domA=None, domX=None):
        """Enumerates the total truth assignments for 
        WMI(formula, weights, X, A).

        Keyword arguments:
        formula -- pysmt formula
        weights -- Weights instance encoding the FIUC weight function
        domA -- set of pysmt vars encoding the Boolean integration domain (optional)
        domX -- set of pysmt vars encoding the real integration domain (optional)

        """
        if isinstance(weights, FNode):
            weights = Weights(weights)
            
        A = {x for x in get_boolean_variables(formula) if not is_label(x)}
        x = get_real_variables(formula)
        dom_msg = "The domain of integration of the numerical variables" +\
                  " should be x. The domain of integration of the Boolean" +\
                  " variables should be a superset of A."

        if domA != None:
            if len(A - domA) > 0:
                self.logger.error(dom_msg)
                raise WMIRuntimeException(dom_msg)

        if domX != None and not set(domX) == x:
            self.logger.error(dom_msg)
            raise WMIRuntimeException(dom_msg) 
            
        formula = And(formula, weights.labelling)

        return len(self._compute_TTAs(formula, weights)[0])

    @staticmethod
    def check_consistency(formula):
        """Returns True iff the formula has at least a total truth assignment
        which is both theory-consistent and it propositionally satisfies it.

        Keyword arguments:
        formula -- a pysmt formula

        """
        for _ in WMI._model_iterator_base(formula):
            return True
        
        return False                

    @staticmethod
    def _convert_to_latte(atom_assignments, weights):
        """Transforms an assignment into a LattE problem, defined by:
        - a polynomial integrand
        - a convex polytope.

        """
        bounds = []
        aliases = {}
        for atom, value in atom_assignments.items():            
            assert(isinstance(value,bool)), "Assignment value should be Boolean"
            # skip atoms without variables
            if len(atom.get_free_variables()) == 0:
                continue
            
            if value is True and atom.is_equals():
                # if the positive literal is an equality, add it to the aliases
                alias, expression = WMI._parse_alias(atom)
                aliases[alias] = expression                    
            elif value is False:
                # if the negative literal is an inequality, change its direction
                if atom.is_le():
                    left, right = atom.args()
                    atom = LT(right, left)
                elif atom.is_lt():
                    left, right = atom.args()
                    atom = LE(right, left)
                    
            # add a bound if the atom is an inequality
            if atom.is_le() or atom.is_lt():                    
                bounds.append(atom)

        current_weight = weights.weight_from_assignment(atom_assignments)
        integrand = Polynomial(current_weight, aliases)
        polytope = Polytope(bounds, aliases)
        return integrand, polytope
    
    @staticmethod
    def _parse_alias(equality):
        assert(equality.is_equals()), "Not an equality"
        left, right = equality.args()
        if left.is_symbol() and (left.get_type() == REAL):
            alias, expr = left, right
        elif right.is_symbol() and (right.get_type() == REAL):
            alias, expr = right, left
        else:
            raise WMIParsingError("Malformed alias expression", equality)
        return left, right
        
    @staticmethod
    def _model_iterator_base(formula):
        solver = Solver(name="msat")
        solver.add_assertion(formula)
        while solver.solve():
            model = solver.get_model()
            yield model
            atom_assignments = {a : model.get_value(a)
                                   for a in formula.get_atoms()}
            # constrain the solver to find a different assignment
            solver.add_assertion(
                Not(And([Iff(var,val)
                         for var,val in atom_assignments.items()])))

    @staticmethod
    def _callback(model, converter, result):
        py_model = [converter.back(v) for v in model]
        result.append(py_model)
        return 1

    def _compute_TTAs(self, formula, weights):
        labels = {}
        expressions = []
        allsat_variables = set()
        index = 0
        # label LRA atoms with fresh boolean variables

        labelled_formula, pa_vars, labels = WMI.label_formula(formula,
                                                              formula.get_atoms())
        solver = Solver(name="msat")
        converter = solver.converter
        solver.add_assertion(labelled_formula)
        models = []
        # perform AllSMT on the labelled formula
        mathsat.msat_all_sat(solver.msat_env(),
                        [converter.convert(v) for v in pa_vars],
                        lambda model : WMI._callback(model, converter, models))
        return models, labels

    def _compute_WMI_AllSMT(self, formula, weights):
        models, labels = self._compute_TTAs(formula, weights)
        latte_problems = []
        for index, model in enumerate(models):
            # retrieve truth assignments for the original atoms of the formula
            atom_assignments = {}
            for atom, value in WMI._get_assignments(model).items():
                if atom in labels:
                    atom = labels[atom]
                atom_assignments[atom] = value

            integrand, polytope = WMI._convert_to_latte(atom_assignments,
                                                        weights)
            latte_problems.append((integrand, polytope, index))

        formula_volume = self._parallel_volume_computation(latte_problems)
        return formula_volume, len(latte_problems)
    
    def _compute_WMI_BC(self, formula, weights):
        latte_problems = []
        for index, model in enumerate(WMI._model_iterator_base(formula)):
            atom_assignments = {a : model.get_value(a).constant_value()
                                   for a in formula.get_atoms()}
            integrand, polytope = WMI._convert_to_latte(atom_assignments,
                                                               weights)
            latte_problems.append((integrand, polytope, index))


        formula_volume = self._parallel_volume_computation(latte_problems)
        return formula_volume, len(latte_problems)

    def _compute_WMI_PA(self, formula, weights):
        latte_problems = []
        index = 0
        boolean_variables = get_boolean_variables(formula)
        if len(boolean_variables) == 0:
            # enumerate partial TA over theory atoms
            lab_formula, pa_vars, labels = WMI.label_formula(formula, formula.get_atoms())
            # predicate abstraction on LRA atoms with minimal models
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

                integrand, polytope =  WMI._convert_to_latte(
                        assignments, weights)
                latte_problems.append((integrand, polytope, index))
                index += 1                    

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

            self.logger.debug("n_boolean_models: {}".format(len(boolean_models)))
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
                    lab_formula, pa_vars, labels = WMI.label_formula(f_next, f_next.get_atoms())
                    expressions = []
                    for k, v in atom_assignments.items():
                        if k.is_theory_relation():
                            if v:
                                expressions.append(k)
                            else:
                                expressions.append(Not(k))
                                                
                    ssformula = And([lab_formula] + expressions)
                    secondstep_solver = Solver(name="msat",
                            solver_options={"dpll.allsat_minimize_model" : "true"})
                    converter = secondstep_solver.converter
                    secondstep_solver.add_assertion(ssformula)
                    ssmodels = []
                    mathsat.msat_all_sat(
                            secondstep_solver.msat_env(),
                            [converter.convert(v) for v in pa_vars],
                            lambda model : WMI._callback(model, converter, ssmodels))
                    for ssmodel in ssmodels:                    
                        secondstep_assignments = {}
                        for atom, value in WMI._get_assignments(ssmodel).items():
                            if atom in labels:
                                atom = labels[atom]
                            secondstep_assignments[atom] = value
                        secondstep_assignments.update(atom_assignments)
                        integrand, polytope =  WMI._convert_to_latte(
                            secondstep_assignments, weights)
                        latte_problems.append((integrand, polytope, index))
                        index += 1                    
                else:
                    # integrate over mu^A & mu^LRA
                    integrand, polytope =  WMI._convert_to_latte(atom_assignments,
                                                          weights)
                    latte_problems.append((integrand, polytope, index))
                    index += 1

        formula_volume = self._parallel_volume_computation(latte_problems)
        return formula_volume, len(latte_problems)

    @staticmethod
    def label_formula(formula, atoms_to_label):
        expressions = []
        labels = {}
        pa_vars = set()
        j = 0
        for a in atoms_to_label:
            if a.is_theory_relation():
                label_a = new_wmi_label(j)
                j += 1
                expressions.append(Iff(label_a, a))
                labels[label_a] = a
                pa_vars.add(label_a)
            else:
                pa_vars.add(a)
                                                
        labelled_formula = And([formula] + expressions)

        return labelled_formula, pa_vars, labels


    def _parallel_volume_computation(self, latte_problems):
        pool = Pool(self.n_threads)
        integrate_alias = partial(integrate_worker, self)
        volume = fsum(pool.map(integrate_alias, latte_problems))
        pool.close()
        pool.join()
        return volume

    @staticmethod
    def _get_assignments(literals):
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
        return WMI._plra_rec(formula, True)

    @staticmethod
    def _plra_rec(formula, pos_polarity):
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

