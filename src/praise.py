"""This module implements utility functions to translate a Hybrid Probabilistic
Graphical Model into the PRAiSE format.
"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from os.path import dirname, abspath
from subprocess import Popen, PIPE
from time import sleep
from fractions import Fraction
from praiselang import *
from pysmt.typing import REAL, BOOL

from wmiexception import WMIRuntimeException, WMIParsingError, WMITimeoutException
from pysmt2latte import is_pow


class PRAiSE:
    """This class implements the methods used to dump PRAiSE models, to perform
    queries and to convert a HPGM into a PRAiSE model.

    It requires the PRAiSE jar to be called 'praise.jar' and to be located in:

        src/thirdparties/

    """

    DEF_TIMEOUT = 10000
    POLL_DELTA = 1
    
    def __init__(self, timeout=DEF_TIMEOUT):
        """Default constructor."""
        self.timeout = timeout
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

        Raises: WMIRuntimeException -- If the model was not dumped on
                                       disk or timeout occurs.

        """
        if not self.model_path:
            raise WMIRuntimeException("The model wasn't dumped on disk")
        if not isinstance(query, str):
            query = self._convert_formula(query)


        tout = int(self.timeout / PRAiSE.POLL_DELTA)
        task = Popen(["java", "-jar", self.jar_path, self.model_path,
                      "--query", query], stdout=PIPE, stderr=PIPE)

        # polling every POLL_DELTA seconds
        while task.poll() is None and tout > 0:
            sleep(PRAiSE.POLL_DELTA)
            tout -= PRAiSE.POLL_DELTA

        if task.poll() != None:
            out, err = task.communicate()

            if err != '':
                msg = "PRAiSE error: {}"
                raise WMIRuntimeException(msg.format(err))

            return PRAiSE._parse_result(out)
        
        else:
            raise WMITimeoutException()
        
    
    def _get_definitions(self):
        definitions = []        
        for var_name, var_type in self.variables.iteritems():
            if var_type == BOOL:
                definitions.append(BooleanVar(var_name))
            elif var_type == REAL:
                definitions.append(RealVar(var_name))
            else:
                raise WMIParsingError("Unknown type", None)
        return "\n".join(definitions)

    @staticmethod
    def _parse_result(praise_out):
        for line in praise_out.split("\n"):
            line = line.strip()
            if line.startswith("Result"):
                result_str = line.partition(": ")[-1].strip()
                numerator, denominator = result_str.split("/")                
                numerator = int(float(numerator))
                denominator = int(float(denominator))
                return float(Fraction(numerator, denominator))
    

    def _convert_formula(self, formula, update_vars = False):

        # 0-ariety expressions
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
        
        else:
            # recursively convert subformulas
            args = []
            for arg in formula.args():
                args.append(self._convert_formula(arg, update_vars))

            # boolean operators
            if formula.is_not():
                assert(len(args) == 1)
                return Not(args[0])
            
            elif formula.is_and():
                return And(args)
            
            elif formula.is_or():
                return Or(args)
            
            elif formula.is_implies():
                assert(len(args) == 2)
                return Implies(args[0], args[1])
            
            elif formula.is_iff():
                assert(len(args) == 2)
                return Iff(args[0], args[1])

            # theory relations
            elif formula.is_le():
                assert(len(args) == 2)
                return LE(args[0], args[1])
            
            elif formula.is_lt():
                assert(len(args) == 2)
                return LT(args[0], args[1])
            
            elif formula.is_equals():
                assert(len(args) == 2)
                return Equals(args[0], args[1])

            # algebraic operators
            if formula.is_plus():
                return Plus(args)
            
            elif formula.is_minus():
                return Minus(args)
            
            elif formula.is_times():
                return Times(args)
            
            elif is_pow(formula):
                assert(len(args) == 2)
                return Pow(args[0], args[1])
            
            else:
                raise WMIParsingError("Unhandled formula format", formula)
            
    def _convert_weights(self, weights):
        statements = []
        for atom, weight in weights.iteritems():
            cond = self._convert_formula(atom)
            then = self._convert_formula(weight[0])
            else_ = self._convert_formula(weight[1])

            ite = ITE(cond, then, else_) + ";"
            statements.append(ite)
            
        return "\n".join(statements)
