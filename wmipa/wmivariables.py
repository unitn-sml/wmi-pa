from pysmt.shortcuts import FreshSymbol
from pysmt.typing import BOOL, REAL
from wmipa.utils import get_boolean_variables


COND = "cond"
WMI = "wmi"
QUERY = "query"
WEIGHT_ALIAS = "weight_alias"
WEIGHT_BOOL = "weight_bool"
EUF_ALIAS = "euf_alias"


class WMIVariables:
    """This class handles all the variables that the program will create in order to calculate the WMI.

    Attributes:
        variables (dict): List of all the variables with relative type and index.

    """

    def __init__(self):
        """Default constructor

        """
        self.variables = {}

    def new_cond_label(self, index):
        """Returns a symbol representing a condition label.

        Args:
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        return self._new_label(COND, index)

    def new_query_label(self, index):
        """Returns a symbol representing a query label.

        Args:
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        return self._new_label(QUERY, index)

    def new_wmi_label(self, index):
        """Returns a symbol representing a wmi label.

        Args:
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        return self._new_label(WMI, index)

    def new_weight_alias(self, index):
        """Returns a symbol representing a weight label.

        Args:
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        return self._new_label(WEIGHT_ALIAS, index, sym_type=REAL, template="FR%s")

    def new_EUF_alias(self, index):
        """Returns a symbol representing a weight label.

        Args:
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        return self._new_label(EUF_ALIAS, index, sym_type=REAL, template="EUF%s")

    def new_weight_bool(self, index):
        """Returns a symbol representing a weight bool.

        Args:
            index (int): The index to associate to the bool.

        Returns:
            FNode: The new bool.

        """
        return self._new_label(WEIGHT_BOOL, index, sym_type=BOOL, template="WB%s")

    def is_cond_label(self, variable):
        """Checks if the variable is a condition label.

        To recognize if the label is a condition label, it first check if it is a wmi variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a condition label, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == COND

    def is_query_label(self, variable):
        """Checks if the variable is a query label.

        To recognize if the label is a query label, it first check if it is a wmi variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a query label, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == QUERY

    def is_wmi_label(self, variable):
        """Checks if the variable is a wmi label.

        To recognize if the label is a wmi label, it first check if it is a wmi variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a wmi label, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == WMI


    def is_euf_alias(self, variable):
        """Checks if the variable is a weight label.

        To recognize if the label is a weight label, it first check if it is a weight variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a weight label, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == EUF_ALIAS


    def is_weight_alias(self, variable):
        """Checks if the variable is a weight label.

        To recognize if the label is a weight label, it first check if it is a weight variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a weight label, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == WEIGHT_ALIAS

    def is_weight_bool(self, variable):
        """Checks if the variable is a weight bool.

        To recognize if the bool is a weight bool, it first check if it is a weight variable and then it controls its label type.

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a weight bool, False otherwise.

        """
        return variable in self.variables and self.variables[variable][1] == WEIGHT_BOOL

    def is_label(self, variable):
        """Checks if the variable is a condition label, query label or wmi label.

        To recognize if the label is of one of these types, this method checks if it is a wmi variable

        Args:
            variable (FNode): The variable to examine.

        Returns:
            bool: True if the variable is a condition, query or wmi label, False otherwise.

        """
        return variable in self.variables

    def contains_labels(self, formula):
        """Checks if the formula contains at least one boolean variable with reserved names.

        The possible reserved names are condition label, query label or wmi label.

        Args:
            formula (FNode): The pysmt formula to examine.

        Returns:
            bool: True if the formula contains at least one boolean variable with reserved names, False otherwise.

        """
        for var in get_boolean_variables(formula):
            if self.is_label(var):
                return True
        return False

    def _new_label(self, type_, index, sym_type=BOOL, template=None):
        """Create a new label based on the type and the index.

        Args:
            type_ (str): The type of the new label.
            index (int): The index to associate to the label.

        Returns:
            FNode: The new label.

        """
        symbol = FreshSymbol(typename=sym_type, template=template)
        assert(symbol not in self.variables)
        self.variables[symbol] = [index, type_]
        return symbol

    def get_label_index(self, variable):
        """Get the index associated to the variable.

        Args:
            variable (FNode): The variable to examine

        Returns:
            int: The index associated to the variable.

        """
        assert (variable in self.variables)
        return self.variables[variable][0]
