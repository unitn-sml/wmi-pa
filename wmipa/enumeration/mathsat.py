import mathsat
import pysmt.shortcuts as smt

from wmipa.utils import BooleanSimplifier, TermNormalizer


class MathSATEnumerator:

    def __init__(self, solver):
        self.solver = solver
        self.weights_skeleton = self.weights.compute_skeleton()
        self.simplifier = BooleanSimplifier()
        self.normalizer = TermNormalizer()

    @property
    def support(self):
        return self.solver.support

    @property
    def weights(self):
        return self.solver.weights

    def enumerate(self, phi):
        """Enumerates the convex fragments of (phi & support), using
        MathSAT's partial enumeration and structurally aware WMI
        enumeration. Since the truth assignments (TA) are partial,
        the number of unassigned Boolean variables is also returned.

        Yields:
        <TA, n>

        where:
        - TA is dict {pysmt_atom : bool}
        - n is int
        """
        # conjoin query and support
        formula = smt.And(phi, self.support)

        # sort the different atoms
        atoms = smt.get_atoms(formula) | self.weights.get_atoms()
        bool_atoms, lra_atoms = set(), set()
        for a in atoms:
            if a.is_symbol(smt.BOOL):
                bool_atoms.add(a)
            elif a.is_theory_relation():
                lra_atoms.add(a)
            else:
                raise ValueError(f"Unhandled atom type: {a}")

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
                    residual_atoms = list(
                        {
                            a
                            for a in simplified_formula.get_free_variables()
                            if a.symbol_type() == smt.BOOL and a in bool_atoms
                        }
                    )
                    residual_atoms.extend(
                        list(
                            {
                                a
                                for a in simplified_formula.get_atoms()
                                if a.is_theory_relation()
                            }
                        )
                    )

                    # may be both on LRA and boolean atoms
                    for ta_residual in self._get_allsat(
                        simplified_formula, residual_atoms
                    ):
                        curr_ta = dict(ta)
                        curr_ta.update(ta_residual)
                        yield curr_ta, len(bool_atoms - curr_ta.keys())

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

        msat_options = (
            {
                "dpll.allsat_minimize_model": "true",
                "dpll.allsat_allow_duplicates": "false",
                "preprocessor.toplevel_propagation": "false",
                "preprocessor.simplification": "0",
            }
            if not force_total
            else {}
        )

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
                        assignments[original_atom] = not value if negated else value

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
            lra_assignments, is_convex = MathSATEnumerator._plra_rec(f_next, True)
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
            return MathSATEnumerator._plra_rec(formula.arg(0), not pos_polarity)
        elif formula.is_and() and pos_polarity:
            assignments = {}
            is_convex = True
            for a in formula.args():
                assignment, rec_is_convex = MathSATEnumerator._plra_rec(a, True)
                assignments.update(assignment)
                is_convex = rec_is_convex and is_convex
            return assignments, is_convex
        elif formula.is_or() and not pos_polarity:
            assignments = {}
            is_convex = True
            for a in formula.args():
                assignment, rec_is_convex = MathSATEnumerator._plra_rec(a, False)
                assignments.update(assignment)
                is_convex = rec_is_convex and is_convex
            return assignments, is_convex
        elif formula.is_implies() and not pos_polarity:
            assignments, is_convex_left = MathSATEnumerator._plra_rec(
                formula.arg(0), True
            )
            assignment_right, is_convex_right = MathSATEnumerator._plra_rec(
                formula.arg(1), False
            )
            assignments.update(assignment_right)
            return assignments, is_convex_left and is_convex_right
        else:
            return {}, False
