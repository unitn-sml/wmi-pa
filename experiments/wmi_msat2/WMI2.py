import wmipa

import mathsat
from pysmt.shortcuts import *
from math import fsum

from wmipa import logger
from wmipa.utils import get_boolean_variables


class WMI2(wmipa.WMI):

    def _compute_TTAs(self, formula):

        # Label LRA atoms with fresh boolean variables
        labelled_formula, pa_vars, labels = self.label_formula(formula, formula.get_atoms())

        # Perform AllSMT on the labelled formula

        solver = Solver(name="msat", solver_options={
            "dpll.allsat_allow_duplicates": "false",
            "dpll.allsat_minimize_model": "false"
        })

        converter = solver.converter
        solver.add_assertion(labelled_formula)
        models = []
        mathsat.msat_all_sat(solver.msat_env(),
                             [converter.convert(v) for v in pa_vars],
                             lambda model: wmipa.WMI._callback(model, converter, models))
        return models, labels

    def _compute_WMI_AllSMT(self, formula, weights):
        models, labels = self._compute_TTAs(formula)
        problems = []
        for index, model in enumerate(models):
            # retrieve truth assignments for the original atoms of the formula
            atom_assignments = {}
            for atom, value in wmipa.WMI._get_assignments(model).items():
                if atom in labels:
                    atom = labels[atom]
                atom_assignments[atom] = value
            problem = self._create_problem(atom_assignments, weights)
            problems.append(problem)

        volume = fsum(self.integrator.integrate_batch(problems))
        return volume, len(problems)

    def _compute_WMI_PA_no_boolean(self, lab_formula, pa_vars, labels, other_assignments={}):

        solver = Solver(name="msat", solver_options={
            "dpll.allsat_minimize_model": "true",
            "dpll.allsat_allow_duplicates": "false",
            "preprocessor.toplevel_propagation": "false",
            "preprocessor.simplification": "0"
        })

        converter = solver.converter
        solver.add_assertion(lab_formula)
        lra_assignments = []
        mathsat.msat_all_sat(
            solver.msat_env(),
            [converter.convert(v) for v in pa_vars],
            lambda model: wmipa.WMI._callback(model, converter, lra_assignments))
        for mu_lra in lra_assignments:
            assignments = {}
            for atom, value in wmipa.WMI._get_assignments(mu_lra).items():
                if atom in labels:
                    atom = labels[atom]
                assignments[atom] = value
            assignments.update(other_assignments)
            yield assignments

    def _compute_WMI_PA(self, formula, weights):

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

            solver = Solver(name="msat", solver_options={
                "dpll.allsat_allow_duplicates": "false",
                "dpll.allsat_minimize_model": "false"
            })

            converter = solver.converter
            solver.add_assertion(formula)
            boolean_models = []
            # perform AllSAT on the Boolean variables
            mathsat.msat_all_sat(
                solver.msat_env(),
                [converter.convert(v) for v in boolean_variables],
                lambda model: wmipa.WMI._callback(model, converter, boolean_models))

            logger.debug("n_boolean_models: {}".format(len(boolean_models)))
            # for each boolean assignment mu^A of F
            for model in boolean_models:
                atom_assignments = {}
                boolean_assignments = wmipa.WMI._get_assignments(model)
                atom_assignments.update(boolean_assignments)
                subs = {k: Bool(v) for k, v in boolean_assignments.items()}
                f_next = formula
                # iteratively simplify F[A<-mu^A], getting (possibily part.) mu^LRA
                while True:
                    f_before = f_next
                    f_next = simplify(substitute(f_before, subs))
                    lra_assignments, over = wmipa.WMI._parse_lra_formula(f_next)
                    subs = {k: Bool(v) for k, v in lra_assignments.items()}
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

        temp = self.integrator.integrate_batch(problems)
        volume = fsum(temp)
        return volume, len(problems)