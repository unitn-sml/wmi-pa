import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.oracles import AtomsOracle
from pysmt.shortcuts import Bool, get_env, simplify, serialize, substitute
from pysmt.walkers import handles


class Weights:
    """This class handles a FIUC weight function and provides a method that can evaluate
        the weight result given a truth assignment of all the conditions inside the
        weight function.

    Attributes:
        weight_func (FNode): The pysmt formula that represents the weight function.
    """

    def __init__(self, weight_func):
        """Initializes the weight object.

        Args:
            weight_func (FNode): The pysmt formula representing the weight function.
        """
        self.weight_func = weight_func
        self.atoms_finder = WeightAtomsFinder()

    def get_atoms(self):
        atoms = self.atoms_finder.get_atoms(self.weight_func)
        return atoms if atoms is not None else frozenset([])

    def weight_from_assignment(self, assignment):
        """Given a truth assignment of the conditions inside the weight function,
            this method evaluates the resulting value based on the assignment.

        Args:
            assignment (dict {FNode : bool}): The dictionary containing all the
                assignments of each condition (e.g: {(x < 3) : True, (y < 5) : False}).

        Returns:
            FNode: The result of the weight function on the given assignment.
        """
        assignment = {atom: Bool(v) for atom, v in assignment.items()}

        return self._evaluate_weight(self.weight_func, assignment)

    def _evaluate_weight(self, node, assignment):
        """Evaluates the value of the given formula applied to the given assignment.

        Args:
            node (FNode): The pysmt formula representing (part of) the weight function.
            assignment (list(bool)): The dictionary containing the truth value of
                each assignment.

        Returns:
            FNode: The result of the formula representing (part of) the weight function
                applied to the given assignment.

        """
        if node.is_ite():
            cond, then, _else = node.args()
            value = self._evaluate_condition(cond, assignment)
            if value:
                return self._evaluate_weight(then, assignment)
            else:
                return self._evaluate_weight(_else, assignment)

        # found a leaf, return it
        elif len(node.args()) == 0:
            return node

        # this condition contains, for example, the Times operator
        else:
            new_children = (self._evaluate_weight(child, assignment) for child in node.args())
            return get_env().formula_manager.create_node(
                node_type=node.node_type(), args=tuple(new_children)
            )

    def _evaluate_condition(self, condition, assignment):
        val = simplify(substitute(condition, assignment))
        assert val.is_bool_constant(), (
                "Weight condition "
                + serialize(condition)
                + "\n\n cannot be evaluated with assignment "
                + "\n".join([str((x, v)) for x, v in assignment.items()])
                + "\n\n simplified into "
                + serialize(condition)
        )
        return val.constant_value()

    def __str__(self):
        return ("Weight {"
                "\t{weight}\n"
                "}").format(
            weight=serialize(self.weight_func),
        )


class WeightAtomsFinder(AtomsOracle):

    def walk_ite(self, formula, args, **kwargs):
        return frozenset(x for a in args if a is not None for x in a)

    @handles(op.THEORY_OPERATORS - {op.ARRAY_SELECT})
    def walk_theory_op(self, formula, args, **kwargs):
        return frozenset(x for a in args if a is not None for x in a)
