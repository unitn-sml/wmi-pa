
from itertools import product

from pysmt.shortcuts import And, Iff, Symbol, get_env, serialize
from pysmt.typing import BOOL, REAL

from wmipa.utils import is_pow
from wmipa.wmiexception import WMIParsingException

class Weights:
    """This class handles a FIUC weight function and provides a method that can evaluate the weight result
        given a truth assignment of all the conditions inside the weight function.
        
    Attributes:
        weights (FNode): The pysmt formula that represents the weight function.
        labels (set(FNode)): The set of all the condition labels created when labelling the weight function.
        labelling (FNode): The pysmt formula representing all the correlations between the labels and the actual conditions
            (e.g: cond_3 <-> (x < 5)).
        n_conditions (int): The number of all the conditions inside the weight function.
        cache (dict): A dictionary where each item is of the type {truth assignment : corresponding weight}
    
    """

    def __init__(self, weight_func, variables, cache=True, expand=False):
        """Initialize the weight function by labelling it with new condition labels and saves in a new formula 
            the mapping from the labels to the relative condition.
            
        Args:
            weight_func (FNode): The pysmt formula representing the weight function.
            cache (bool, optional): The boolean that enables the use of the cache when evaluating the weight from a
                given assignment (default: True).
            expand (bool, optional): If True the cache will be populated with the values resulting from the application
                of the weight function on each possible truth assignment of the conditions inside it (default: False).
        
        """
        self.variables = variables
        
        # labels the weight function with new labels
        self.weights, subs = self.label_conditions(weight_func)
        self.labels = set(subs.values())
        self.n_conditions = len(subs)
        
        # create a formula representing all the substitution (e.g: cond_3 <-> (x < 5))
        labelling_list = []
        for cond, label in subs.items():
            labelling_list.append(Iff(cond, label))
        self.labelling = And(labelling_list)
        
        # inizialize the cache (if requested)
        if cache:
            self.cache = {}
            if expand:
                self._expand_to_dictionary()
        else:
            self.cache = None

    def weight_from_assignment(self, assignment):
        """Given a total truth assignment of all the conditions inside the weight function, this method
            evaluates the resulting value based on the assignment.
            
        Args:
            assignment (dict {FNode : bool}): The dictionary containing all the assignments of each condition
                (e.g: {(x < 3) : True, (y < 5) : False}).
                
        Returns:
            FNode: The result of the weight function on the given assignment.
        
        """
        # prepare an empty array of lenght 'n_conditions' to be populated with the values of the assignment
        label_assignment = [None for _ in range(self.n_conditions)]
        
        # populate the array with all the values
        for atom, value in assignment.items():
            assert(isinstance(value,bool)), "Assignment value should be Boolean"
            if (atom.is_symbol() and atom.get_type() == BOOL and self.variables.is_cond_label(atom)):
            
                # take the index of the variable from the label
                index = self.variables.get_label_index(atom)
                label_assignment[index] = value
                
        assert(not None in label_assignment), "Couldn't retrieve the complete assignment"
        label_assignment = tuple(label_assignment)
        
        # evaluate the weight from the assignment
        if self.cache != None:
        
            # first check into the cache if the weight associated to the particular assignment was already calculated
            if label_assignment in self.cache:
                return self.cache[label_assignment], label_assignment
                
            # else evaluate it and insert it into the cache
            else:
                flat_w = self._evaluate_weight(self.weights, label_assignment)
                self.cache[label_assignment] = flat_w
                return flat_w, label_assignment
                
        # if there is no cache just evaluate the weight
        else:
            return self._evaluate_weight(self.weights, label_assignment), label_assignment

    def label_conditions(self, weight_func):
        """Finds and labels all the conditions inside the weight function with fresh boolean atoms.
        
        Args:
            weight_func (FNode): The pysmt formula representing the weight function to label.
            
        Returns:
            FNode: The pysmt formula representing the weight function with all the conditions substituted
                with the new labels.
            dict {FNode : FNode}: The dictionary containing all the conditions and their respectivelly substitution
                (e.g: {(x < 3) : cond_0, (y < 5) : cond_1} ).
        
        """
        # recursively find all the conditions and create a label for all of them
        subs = self._find_conditions(weight_func, subs={})
        
        # perform labelling
        labelled_weight_func = weight_func.substitute(subs)
        
        return labelled_weight_func, subs

    def _expand_to_dictionary(self):
        """Populates the cache with the values resulting from the application
            of the weight function on each possible truth assignment of the conditions inside it."""
        assert(self.cache != None), "Cache should be already initialized"
        
        # create every possible combination of assigments
        for assignment in product([True, False], repeat=(self.n_conditions)):
            
            # evaluate the results for all assignments and save them in the chache
            cond_w = self._evaluate_weight(self.weights, assignment)
            self.cache[assignment] = cond_w

    def _evaluate_weight(self, node, assignment):
        """Evaluates the value of the given formula applied to the given assignment.
        
        Args:
            node (FNode): The pysmt formula representing (part of) the weight function.
            assignment (list(bool)): The dictionary containing the truth value of each assignment.
            
        Returns:
            FNode: The result of the formula representing (part of) the weight function applied to the given assignment.
        
        """
        if node.is_ite():
            cond, then, _else = node.args()
            
            # gets the index of the label to retrieve the truth value of that specific label
            index_cond = self.variables.get_label_index(cond)
            
            # iteratively retrieve the leaf nodes from the 'then' or 'else' part, depending on the truth value of the condition
            if assignment[index_cond]:
                return self._evaluate_weight(then, assignment)
            else:
                return self._evaluate_weight(_else, assignment)
                
        # found a leaf, return it
        elif len(node.args()) == 0:
            return node
            
        # this condition contains, for example, the Times operator
        else:
            new_children = []
            for child in node.args():
                new_children.append(self._evaluate_weight(child, assignment))
                
            # after retrieving all the leaf nodes of the children it creates a new node with these particular leafs
            return get_env().formula_manager.create_node(
                node_type=node.node_type(), args=tuple(new_children))

    def _find_conditions(self, node, subs):
        """Finds all the conditions inside the given formula and creates a new label for each of them,
            adding both the condition and relative label to the given dictionary.
            
        Args:
            node (FNode): The pysmt formula representing (part of) the weight function.
            subs (dict {FNode : FNode}): The dictionary that will contain the correlations between
                each conditions and their labels.
            
        Returns:
            dict {FNode : FNode}: The dictionary containing the correlations between each conditions
                of the given formula and their labels.
                
        Raises:
            WMIParsingException: If the weight formula does not represent a weight function.
        
        """
        if node.is_ite():
            cond, then, _else = node.args()
            
            # if this particolar condition was not already labelled
            if not cond in subs:
                label = self.variables.new_cond_label(len(subs))
                subs[cond] = label
            
            # recursively finds all the conditions in both the 'then' and 'else' term
            subs = self._find_conditions(then, subs)
            subs = self._find_conditions(_else, subs)

        elif node.is_plus() or node.is_times() or is_pow(node):
            # recursively finds all the conditions in all the children of the formula (i.e: PLUS, MINUS, TIMES, DIV, POW)
            for child in node.args():
                subs = self._find_conditions(child, subs)
        elif len(node.args()) != 0 or not (node.is_symbol(REAL) or node.is_constant()):
            # other possible types of admitted nodes are symbol or constant else an exception is raised
            raise WMIParsingException(WMIParsingException.INVALID_WEIGHT_FUNCTION, node)
            
        return subs
        
    def __str__(self):
        ret = "Weight object {\n"
        ret += "\tlabelled weight: "+serialize(self.weights)+"\n"
        ret += "\tlabels: "+", ".join([serialize(s) for s in self.labels])+"\n"
        ret += "\tlabelling: "+serialize(self.labelling)+"\n"
        ret += "\tnumber of conditions: "+str(self.n_conditions)+"\n"
        ret += "}"
        
        return ret
