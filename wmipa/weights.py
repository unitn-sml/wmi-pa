from itertools import product

from pysmt.fnode import FNode
from pysmt.shortcuts import And, Bool, Iff, get_env, serialize
from pysmt.typing import REAL

from wmipa.weightconverter import WeightConverterEUF, WeightConverterSkeleton
from wmipa.wmiexception import WMIParsingException


class Weights:
    """This class handles a FIUC weight function and provides a method that can evaluate
        the weight result given a truth assignment of all the conditions inside the
        weight function.

    Attributes:
        weights (FNode): The pysmt formula that represents the weight function.
        labels (set(FNode)): The set of all the condition labels created when labelling
            the weight function.
        labelling (FNode): The pysmt formula representing all the correlations between
            the labels and the actual conditions (e.g: cond_3 <-> (x < 5)).
        n_conditions (int): The number of all the conditions inside the weight function.
        cache (dict): A dictionary where each item is of the type
            {truth assignment : corresponding weight}

    """

    def __init__(self, weight_func, variables, cache=True, expand=False):
        """Initialize the weight function by labelling it with new condition labels and saves
            in a new formula the mapping from the labels to the relative condition.

        Args:
            weight_func (FNode): The pysmt formula representing the weight function.
            cache (bool, optional): The boolean that enables the use of the cache when
                evaluating the weight from a given assignment (default: True).
            expand (bool, optional): If True the cache will be populated with the values
                resulting from the application of the weight function on each possible
                truth assignment of the conditions inside it (default: False).

        """
        self.variables = variables

        # labels the weight function with new labels
        self.labelled_weights, subs = self.label_conditions(weight_func)
        self.labels = {}
        self.weight_conditions = {}
        for cond, sub in subs.items():
            self.labels[sub] = self.variables.get_label_index(sub)
            self.weight_conditions[cond] = self.variables.get_label_index(sub)
        self.n_conditions = len(subs)

        # create a formula representing all the substitution (e.g: cond_3 <-> (x < 5))
        labelling_list = []
        for cond, label in subs.items():
            labelling_list.append(Iff(cond, label))
        self.labelling = And(labelling_list)

        # convert weights as formula for EUF
        self.converterEUF = WeightConverterEUF(variables)
        self.converterSK = WeightConverterSkeleton(variables)
        self.weights_as_formula_euf = self.converterEUF.convert(weight_func)
        self.weights_as_formula_sk = self.converterSK.convert(weight_func)
        self.weights = weight_func

        # initialize the cache (if requested)
        if cache:
            self.cache = {}
            if expand:
                self._expand_to_dictionary()
        else:
            self.cache = None

    def weight_from_assignment(self, assignment, on_labels=True):
        """Given a total truth assignment of all the conditions inside the weight function,
            this method evaluates the resulting value based on the assignment.

        Args:
            assignment (dict {FNode : bool}): The dictionary containing all the
                assignments of each condition (e.g: {(x < 3) : True, (y < 5) : False}).
            on_labels (bool): If True assignment is expected to be over labels of weight
                condition otherwise it is expected to be over unlabelled conditions

        Returns:
            FNode: The result of the weight function on the given assignment.

        """
        if on_labels:
            conditions = self.labels
            weights = self.labelled_weights
        else:
            conditions = self.weight_conditions
            weights = self.weights

        # prepare an empty array of length 'n_conditions' to be populated with the
        # values of the assignment
        cond_assignment = [None for _ in range(self.n_conditions)]
        if on_labels:
            # populate the array with all the values
            for atom, value in assignment.items():
                assert isinstance(value, bool), "Assignment value should be Boolean"
                # if (atom.is_symbol() and atom.get_type() == BOOL and
                # self.variables.is_cond_label(atom)):
                if atom in conditions:
                    # take the index of the variable from the label
                    index = conditions[atom]
                    cond_assignment[index] = value

            assert (
                    None not in cond_assignment
            ), "Couldn't retrieve the complete assignment"

        assignment = {atom: Bool(v) for atom, v in assignment.items()}
        # evaluate the weight from the assignment
        if self.cache is not None:
            cond_assignment_tuple = tuple(cond_assignment)

            # first check into the cache if the weight associated to the particular
            # assignment was already calculated
            if cond_assignment_tuple in self.cache:
                return self.cache[cond_assignment_tuple], cond_assignment_tuple

            # else evaluate it and insert it into the cache
            else:
                flat_w = self._evaluate_weight(
                    weights, cond_assignment, conditions, assignment
                )
                cond_assignment_tuple = tuple(cond_assignment)
                self.cache[cond_assignment_tuple] = flat_w
                return flat_w, cond_assignment_tuple

        # if there is no cache just evaluate the weight
        else:
            flat_w = self._evaluate_weight(
                weights, cond_assignment, conditions, assignment
            )
            return flat_w, tuple(cond_assignment)

    def label_conditions(self, weight_func):
        """Finds and labels all the conditions inside the weight function with fresh boolean
            atoms.

        Args:
            weight_func (FNode): The pysmt formula representing the weight function to
                label.

        Returns:
            FNode: The pysmt formula representing the weight function with all the
                conditions substituted with the new labels.
            dict {FNode : FNode}: The dictionary containing all the conditions and their
                respectively substitution (e.g: {(x < 3) : cond_0, (y < 5) : cond_1} ).

        """
        # recursively find all the conditions and create a label for all of them
        subs = {}
        self._find_conditions(weight_func, subs)
        # perform labelling
        labelled_weight_func = weight_func.substitute(subs)

        return labelled_weight_func, subs

    def _expand_to_dictionary(self):
        """Populates the cache with the values resulting from the application
        of the weight function on each possible truth assignment of
        the conditions
        inside it.

        """
        assert self.cache is not None, "Cache should be already initialized"

        # create every possible combination of assignments
        for assignment in product([True, False], repeat=self.n_conditions):
            # evaluate the results for all assignments and save them in the cache
            cond_w = self._evaluate_weight(
                self.labelled_weights, assignment, self.labels, {}
            )
            self.cache[assignment] = cond_w

    def _evaluate_weight(self, node, assignment, conditions, atom_assignment):
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
            # gets the index of the label to retrieve the truth value of that specific label
            index_cond = conditions[cond]
            # assert assignment[index_cond] is not None, cond
            if assignment[index_cond] is None:
                assignment[index_cond] = self._evaluate_condition(cond, atom_assignment)
            # iteratively retrieve the leaf nodes from the 'then' or 'else' part,
            # depending on the truth value of the condition
            if assignment[index_cond]:
                return self._evaluate_weight(then, assignment, conditions, atom_assignment)
            else:
                return self._evaluate_weight(_else, assignment, conditions, atom_assignment)

        # found a leaf, return it
        elif len(node.args()) == 0:
            return node

        # this condition contains, for example, the Times operator
        else:
            new_children = []

            for child in node.args():
                new_children.append(self._evaluate_weight(child, assignment, conditions, atom_assignment))

            # after retrieving all the leaf nodes of the children it creates a new
            # node with these particular leafs
            return get_env().formula_manager.create_node(
                node_type=node.node_type(), args=tuple(new_children)
            )

    def _find_conditions(self, node, subs):
        """Finds all the conditions inside the given formula and creates a new label for each of
            them, adding both the condition and relative label to the given dictionary.

        Args:
            node (FNode): The pysmt formula representing (part of) the weight function.
            subs (dict {FNode : FNode}): The dictionary that will contain the
                correlations between each condition and their labels.

        Raises:
            WMIParsingException: If the weight formula does not represent a weight
                function.

        """
        if node.is_ite():
            cond, then, _else = node.args()

            # if this particular condition was not already labelled
            if cond not in subs:
                label = self.variables.new_cond_label(len(subs))
                subs[cond] = label

            # recursively finds all the conditions in both the 'then' and 'else' term
            self._find_conditions(then, subs)
            self._find_conditions(_else, subs)

        elif node.is_ira_op():
            # recursively finds all the conditions in all the children of the formula
            # (i.e: PLUS, MINUS, TIMES, DIV, POW)
            for child in node.args():
                self._find_conditions(child, subs)
        elif len(node.args()) != 0 or not (node.is_symbol(REAL) or node.is_constant()):
            # other possible types of admitted nodes are symbol or constant else an
            # exception is raised
            raise WMIParsingException(WMIParsingException.INVALID_WEIGHT_FUNCTION, node)

    @staticmethod
    def _evaluate_condition(condition, assignment):
        val = condition.substitute(assignment).simplify()
        assert val.is_bool_constant(), (
                "Weight condition "
                + serialize(condition)
                + "\n\n cannot be evaluated with assignment "
                + "\n".join([str((x, assignment[x])) for x in assignment])
                + "\n\n simplified into "
                + serialize(val)
        )
        return val.constant_value()

    def __str__(self):
        return ("Weight object {"
                "\tweight: {weight},\n"
                "\tlabelled_weight: {labelled_weight},\n"
                "\tlabels: {labels},\n"
                "\tlabelling: {labelling},\n"
                "\tnumber of conditions: {n_conditions}\n"
                "\tw_as_euf: {w_as_euf},\n"
                "\tw_as_sk: {w_as_sk},\n"
                "}").format(
            weight=serialize(self.weights),
            labelled_weight=serialize(self.labelled_weights),
            labels=", ".join([serialize(s) for s in self.labels]),
            labelling=serialize(self.labelling),
            n_conditions=str(self.n_conditions),
            w_as_euf=serialize(self.weights_as_formula_euf),
            w_as_sk=serialize(self.weights_as_formula_sk)
        )
