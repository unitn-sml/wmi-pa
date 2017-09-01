"""This module implements utility functions to translate a Hybrid Probabilistic
Graphical Model into the PRAiSE format.
"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from os.path import dirname, abspath
from subprocess import check_output
from fractions import Fraction
from pysmt.shortcuts import *
from pysmt.typing import *

from wmiexception import WMIRuntimeException, WMIParsingError
from pysmt2latte import is_pow


class PRAiSE:
    """This class implements the methods used to dump PRAiSE models, to perform
    queries and to convert a HPGM into a PRAiSE model.

    It requires the PRAiSE jar to be called 'praise.jar' and to be located in:

        src/thirdparties/

    Attributes:
    variables -- dict {variable_name : type}
    model -- the PRAiSE model

    """
    def __init__(self):
        """Default constructor."""        
        self.model_path = None
        jar_directory = dirname(abspath(__file__)) + "/thirdparties/"
        self.jar_path = jar_directory + "praise.jar"

    def convert(self, formula, weights):
        """Converts a HPGM defined by the pair (formula, weights) into an
        equivalent PRAiSE model.

        Keyword arguments:
        formula -- pysmt formula
        weights -- dict containing weight functions associated with the literals

        Raises:
        WMIParsingError -- The parsing may fail for a number of reasons.

        """
        self.variables = {}
        converted_formula = self._convert_formula(formula, update_vars = True)
        converted_weights = self._convert_weights(weights)
        definitions = self._get_definitions()
        self.model = "\n\n".join([definitions,
                            converted_formula + ";",
                            converted_weights])
                    
    def dump_model(self, path):
        """Dumps the current model to disk and stores its path.

        Keyword arguments:
        path -- Path to the output file

        """
        with open(path, "w") as f:
            f.write(self.model)
        self.model_path = path
    
    def perform_query(self, query):
        """Performs a query on the dumped model.

        Keyword arguments:
        query -- string representing the query

        Raises:
        WMIRuntimeException -- If the model was not dumped on disk.

        """
        if not self.model_path:
            raise WMIRuntimeException("The model wasn't dumped on disk")
        if not isinstance(query, str):
            query = self._convert_formula(query)

        res = str(check_output(["java", "-jar", self.jar_path,
                                self.model_path, "--query", query]))
        
        return PRAiSE._parse_result(res)

    
    def _get_definitions(self):
        definitions = []        
        for var_name, var_type in self.variables.iteritems():
            if var_type == BOOL:
                definitions.append("random {} : Boolean;".format(var_name))
            elif var_type == REAL:
                definitions.append("random {} : Real;".format(var_name))
            else:
                raise WMIParsingError("Unknown type", None)
        return "\n".join(definitions)

    @staticmethod
    def _parse_result(praise_out):
        for line in praise_out.split("\n"):
            line = line.strip()
            if line.startswith("RESULT"):
                result_str = line.partition("= ")[-1]
                return float(Fraction(result_str))
    

    def _convert_formula(self, formula, update_vars = False):
        if formula.is_constant():
            return str(formula.constant_value()).lower()
        elif formula.is_symbol():
            # whenever a variable is found, return its name and optionally add
            # an entry to the variables dictionary with the corresponding type
            var_name = formula.symbol_name()
            if update_vars:
                var_type = formula.get_type()
                self.variables[var_name] = var_type
            return var_name
        elif formula.is_bool_op():
            if formula.is_not():
                return "(not {})".format(self._convert_formula(formula.arg(0),
                                                              update_vars))
            else:
                if formula.is_and():
                    op = "and"
                elif formula.is_or():
                    op = "or"
                elif formula.is_implies():
                    op = "=>"
                elif formula.is_iff():
                    op = "<=>"
                else:
                    raise WMIParsingError("Unhandled Boolean operator", formula)
                    
                args = []
                for arg in formula.args():
                    args.append(self._convert_formula(arg, update_vars))
                return "(" + " {} ".format(op).join(args) + ")"
        elif formula.is_theory_relation():
            if formula.is_le():
                op = "<="
            elif formula.is_lt():
                op = "<"
            elif formula.is_equals():
                op = "="
            else:
                raise WMIParsingError("Unhandled theory relation", formula)
            left = self._convert_formula(formula.arg(0), update_vars)
            right = self._convert_formula(formula.arg(1), update_vars)
            return "({} {} {})".format(left, op, right)
        elif formula.is_theory_op():
            if formula.is_plus():
                op = "+"
            elif formula.is_minus():
                op = "-"
            elif formula.is_times():
                op = "*"
            elif is_pow(formula):
                op = "^"
            else:
                raise WMIParsingError("Unhandled theory operator", formula)
            args = []
            for arg in formula.args():
                args.append(self._convert_formula(arg, update_vars))
            return "(" + " {} ".format(op).join(args) + ")"
        else:
            raise WMIParsingError("Unhandled formula format", formula)
            
    def _convert_weights(self, weights):
        statements = []
        for atom, weight in weights.iteritems():
            cond = self._convert_formula(atom)
            pos = self._convert_formula(weight[0])
            neg = self._convert_formula(weight[1])
            statements.append("if {}\nthen {}\nelse {};".format(cond, pos, neg))
        return "\n".join(statements)            
