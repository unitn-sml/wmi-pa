
from itertools import product

from pysmt.shortcuts import And, Iff, Symbol, get_env, serialize
from pysmt.typing import BOOL

from wmipa.utils import new_cond_label, is_cond_label

class Weights:

    def __init__(self, weight_func, expand=False, cache=True):
        self.weights, subs = Weights.label_conditions(weight_func)
        self.labels = set(subs.values())
        labelling_list = []
        for cond, label in subs.items():
            labelling_list.append(Iff(cond, label))

        self.labelling = And(labelling_list)
        
        self.n_conditions = len(subs)
        if cache:
            self.cache = {}
            if expand:
                self._expand_to_dictionary()
        else:
            self.cache = None

    def weight_from_assignment(self, assignment):        
        label_assignment = [None for _ in range(self.n_conditions)]
        for atom, value in assignment.items():            
            assert(isinstance(value,bool)), "Assignment value should be Boolean"
            if (atom.is_symbol() and atom.get_type() == BOOL and
                     is_cond_label(atom)):
                index = int(atom.symbol_name().partition("_")[-1])
                label_assignment[index] = value
            
        assert(not None in label_assignment),\
            "Couldn't retrieve the complete assignment"
        label_assignment = tuple(label_assignment)
        if self.cache != None:
            if label_assignment in self.cache:
                return self.cache[label_assignment]
            else:
                flat_w = Weights._evaluate_weight(self.weights, label_assignment)
                self.cache[label_assignment] = flat_w
                return flat_w
        else:
            return Weights._evaluate_weight(self.weights, label_assignment)

    @staticmethod
    def label_conditions(weight_func):
        # recursively find all the conditions
        subs = Weights._find_conditions(weight_func, subs={})
        # perform labelling
        labelled_weight_func = weight_func.substitute(subs)
        return labelled_weight_func, subs
        

    def _expand_to_dictionary(self):
        """Expands a FIUC weight function expressed as a pysmt formula.
        - all conditions are labelled with fresh Boolean atoms B = {b_i | i in 1..n}
        - the conditional weight function is converted in a dictionary mapping
          each assignments to B to the corresponding FI weight.

        Returns such dictionary and the dictionary containing the substitutions:
        {cond_i : b_i}

        Keyword arguments:
        weight_func -- the conditional weight function written as a pysmt formula        

        """
        assert(self.cache != None), "Cache should be already initialized"
        for assignment in product([True, False], repeat=(self.n_conditions)):
            cond_w = Weights._evaluate_weight(self.weights, assignment)
            self.cache[assignment] = cond_w

    @staticmethod
    def _evaluate_weight(node, assignment):
        if node.is_ite():
            cond, then, _else = node.args()
            index_cond = int(cond.symbol_name().partition("_")[-1])
            if assignment[index_cond]:
                return Weights._evaluate_weight(then, assignment)
            else:
                return Weights._evaluate_weight(_else, assignment)
        elif len(node.args()) == 0:
            return node
        else:
            new_children = []
            for child in node.args():
                new_children.append(Weights._evaluate_weight(child, assignment))
            return get_env().formula_manager.create_node(
                node_type=node.node_type(), args=tuple(new_children))

    @staticmethod
    def _find_conditions(node, subs):
        if node.is_ite():
            cond, then, _else = node.args()
            if not cond in subs:
                label = new_cond_label(len(subs))
                subs[cond] = label

            subs = Weights._find_conditions(then, subs)
            subs = Weights._find_conditions(_else, subs)

        else:
            for child in node.args():
                subs = Weights._find_conditions(child, subs)

        return subs
