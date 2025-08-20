import queue
import threading
from typing import Callable, Collection, Generator, Iterable, Optional, cast

import pysmt.operators as op
from pysmt.environment import Environment, get_env
from pysmt.fnode import FNode
from pysmt.solvers.msat import MSatConverter
from pysmt.typing import BOOL
from pysmt.walkers import TreeWalker, handles

from wmipa.core.utils import BooleanSimplifier, LiteralNormalizer
from wmipa.core.weights import Weights

try:
    import mathsat
except ImportError as e:
    mathsat = None
    _IMPORT_ERR = e


class SAEnumerator:
    def __init__(
        self,
        support: FNode,
        weight: Optional[FNode] = None,
        env: Optional[Environment] = None,
        max_queue_size: int = 1,
    ) -> None:
        """
        Constructs a SAEnumerator instance.
        Args:
            weights (Weights): The representation of the weight function.
            support (FNode): The pysmt formula that contains the support of the formula
            env (Environment) : The pysmt environment
            max_queue_size: Maximum number of assignments to compute in parallel.
                             1 means we will compute the assignments one by one.
                             0 means no limit.
        """

        # check whether MathSAT is installed or not
        if mathsat is None:
            raise ImportError(
                "MathSAT is not installed. Please install it using the `wmipa install` command."
            ) from _IMPORT_ERR

        self.support = support

        if env is not None:
            self.env = env
        else:
            self.env = cast(Environment, get_env())

        if weight is None:
            weight = self.env.formula_manager.Real(1)  # Default weight is 1

        self.weights = Weights(weight, self.env)

        # 0 for no limit, the default is 1
        # the queue blocks until it has an available slot
        # so 1 means we will compute the assignments one by one
        self.max_queue_size = max_queue_size

        self.weights_skeleton = self.weights.compute_skeleton()
        self.simplifier = BooleanSimplifier(self.env)
        self.normalizer = LiteralNormalizer(self.env)
        self.assignment_extractor = AssignmentExtractor(self.env)

    def enumerate(self, phi: FNode) -> Iterable[tuple[dict[FNode, bool], int]]:
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
        mgr = self.env.formula_manager

        # conjoin query and support
        formula = mgr.And(phi, self.support)

        # sort the different atoms
        atoms = self.env.ao.get_atoms(formula) | self.weights.get_atoms()
        bool_atoms, lra_atoms = set(), set()
        for a in atoms:
            if a.is_symbol(BOOL):
                bool_atoms.add(a)
            elif a.is_theory_relation():
                lra_atoms.add(a)
            else:
                raise ValueError(f"Unhandled atom type: {a}")

        # conjoin the skeleton of the weight function
        formula = mgr.And(formula, self.weights_skeleton)

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
                    formula, ta_bool, ta, atoms
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
                            if a.symbol_type() == BOOL and a in bool_atoms
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

    def _get_allsat(
        self,
        formula: FNode,
        atoms: Collection[FNode],
        force_total: bool = False,
    ) -> Generator[dict[FNode, bool], None, None]:
        """
        Gets the list of assignments that satisfy the formula.

        Args:
            formula: The formula to satisfy
            atoms: List of atoms on which to find the assignments.
            force_total: Forces total truth assignments.
                Defaults to False.

        Yields:
            list: assignments on the atoms
        """

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
            if not atom.is_symbol(BOOL):
                _ = self.normalizer.normalize(atom, remember_alias=True)

        def callback(model: list["mathsat.msat_term"]) -> dict[FNode, bool]:
            converted_model = [converter.back(v) for v in model]
            assignments: dict[FNode, bool] = {}
            for lit in converted_model:
                atom = lit.arg(0) if lit.is_not() else lit
                value = not lit.is_not()

                if atom.is_symbol(BOOL):
                    assignments[atom] = value
                else:
                    # retrieve the original (unnormalized) atom
                    normalized_atom, negated = self.normalizer.normalize(atom)
                    if negated:
                        value = not value
                    known_aliases = self.normalizer.known_aliases(normalized_atom)
                    for original_atom, negated in known_aliases:
                        assignments[original_atom] = not value if negated else value

            return assignments

        with self.env.factory.Solver(
            name="msat", solver_options=msat_options
        ) as solver:
            converter: MSatConverter = solver.converter
            solver.add_assertion(formula)

            msat_env = solver.msat_env()

            return self._all_sat_stream(msat_env, atoms, converter, callback)

    def _all_sat_stream(
        self,
        msat_env: "mathsat.msat_env",
        atoms: Collection[FNode],
        converter: MSatConverter,
        f: Callable[[list["mathsat.msat_term"]], dict[FNode, bool]],
    ) -> Generator[dict[FNode, bool], None, None]:
        """
        Enumerates all satisfying assignments for the given atoms in the MathSAT
        environment. This function runs asynchronously and yields results as
        soon as they are found.
        Args:
            msat_env: The MathSAT environment.
            atoms: The atoms to enumerate.
            converter: The converter to convert atoms to MathSAT format.
            f: A function to apply to each model found.
        """
        q: queue.Queue = queue.Queue(maxsize=self.max_queue_size)
        stop_token = object()
        error_token = object()

        # Thread control
        thread_stop_event = threading.Event()

        def _callback(model: list[mathsat.msat_term]) -> int:
            q.put(f(model))
            if thread_stop_event.is_set():
                return 0
            else:
                return 1

        def run() -> None:
            try:
                mathsat.msat_all_sat(
                    msat_env, [converter.convert(v) for v in atoms], _callback
                )
                q.put(stop_token)
            except Exception as e:
                q.put((error_token, e))

        t = threading.Thread(target=run, daemon=True)
        t.start()  # We enumerate async

        try:
            while True:
                item = q.get()
                if item is stop_token:
                    break
                elif isinstance(item, tuple) and item[0] is error_token:
                    raise item[1]  # Re-raise the exception from the thread
                else:
                    # Only yield valid assignments
                    yield item
        finally:
            if t is not None and t.is_alive():
                thread_stop_event.set()
                t.join()  # Wait for the thread to finish

    def _simplify_formula(
        self,
        formula: FNode,
        subs: dict[FNode, bool],
        truth_assignment: dict[FNode, bool],
        scope: set[FNode],
    ) -> tuple[bool, FNode]:
        """Substitute the subs in the formula and iteratively simplify it.
        truth_assignment is updated with unit-propagated atoms.

        Args:
            formula (FNode): The formula to simplify.
            subs (dict): Dictionary with the substitutions to perform.
            truth_assignment (dict): Dictionary with atoms and assigned value.
            scope (set): Set of atoms that should end up in 'truth_assignment'

        Returns:
            bool: True if the formula is completely simplified.
            FNode: The simplified formula.
        """
        mgr = self.env.formula_manager
        subs_node = {k: mgr.Bool(v) for k, v in subs.items()}
        f_next = formula
        # iteratively simplify F[A<-mu^A], getting (possibly part.) mu^LRA
        while True:
            f_before = f_next
            f_next = self.simplifier.simplify(f_before.substitute(subs_node))
            lra_assignments, is_convex = self.assignment_extractor.extract(f_next)
            subs_node = {k: mgr.Bool(v) for k, v in lra_assignments.items()}
            truth_assignment.update(
                {k: v for k, v in lra_assignments.items() if k in scope}
            )
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
                        expressions.append(mgr.Not(k))
            f_next = mgr.And([f_next] + expressions)
        return is_convex, f_next


class AssignmentExtractor(TreeWalker):
    """Extracts forced literals from a formula.

    A forced literal is a literal that must be true for the formula to be satisfied.
    Such literals are found recursively in the formula structure:
    - If the formula is a conjunction, all literals in the conjunction are forced.
    - If the formula is a negated disjunction, all literals in the disjunction are forced with a negated value.
    """

    def __init__(self, env: Environment):
        super().__init__(env)
        self.polarity = True
        self.is_convex = False
        self.assignment: dict[FNode, bool] = {}

    def extract(self, formula: FNode) -> tuple[dict[FNode, bool], bool]:
        """Extracts the assignment of forced literals from a formula.

        Args:
            formula: The formula to extract the assignment from.
        Returns:
            A tuple containing:
                - A dictionary with forced literals as keys and their truth values as values.
                - A boolean indicating whether the formula is convex (i.e., can be expressed as a conjunction of literals).
        """

        self.assignment = {}
        self.polarity = True
        self.is_convex = True

        self.walk(formula)

        return self.assignment, self.is_convex

    def walk_bool_constant(self, node: FNode) -> None:
        return

    @handles(op.SYMBOL)
    @handles(op.IRA_RELATIONS)
    def walk_term(self, node: FNode) -> None:
        assert node.is_symbol(BOOL) or node.is_theory_relation()
        self.assignment[node] = self.polarity

    def walk_not(self, node: FNode) -> Generator[FNode, None, None]:
        self.polarity = not self.polarity
        yield node.arg(0)  # recursion into the negated argument
        self.polarity = not self.polarity

    def walk_and(self, node: FNode) -> Generator[FNode, None, None]:
        if self.polarity:
            for arg in node.args():
                yield arg  # recursion into the arguments
        else:
            self.is_convex = False

    def walk_or(self, node: FNode) -> Generator[FNode, None, None]:
        if not self.polarity:
            for arg in node.args():
                yield arg  # recursion into the arguments
        else:
            self.is_convex = False

    def walk_implies(self, node: FNode) -> Generator[FNode, None, None]:
        if not self.polarity:
            self.polarity = False
            yield node.arg(0)
            self.polarity = True
            yield node.arg(1)
        else:
            self.is_convex = False
