"""This module leverages PRAiSE to implement an inference engine that
allows queries of the form P(Q(x,A)|E(x,A)) over an hybrid model
expressed by a weight formula w(x,A) and support Chi(x,A). Q, E, w and
Chi are SMT-LRA formulas.

"""
__version__ = '0.999'
__author__ = 'Paolo Morettin'

from os.path import abspath, dirname, join
from subprocess import Popen, PIPE
from time import sleep
from fractions import Fraction
from pysmt.typing import REAL, BOOL
import sys
from tempfile import TemporaryDirectory
import wmipa.praiselang as pl
from wmipa.wmiexception import WMIRuntimeException, WMIParsingException
from wmipa.utils import is_pow


class PRAiSEInference:

    DEF_TIMEOUT = 10000
    POLL_DELTA = 1

    JAR_NAME = "praise.jar"
    JAR_PATH = dirname(abspath(__file__)) + "/thirdparties/" + JAR_NAME

    def __init__(self, support, weights, timeout=None):
        self.timeout = timeout or PRAiSEInference.DEF_TIMEOUT
        self.convert(support, weights)

    def convert(self, formula, weights):
        self.variables = {}
        converted_formula = PRAiSEInference.convert_formula(formula, self.variables)
        converted_weights = PRAiSEInference.convert_formula(weights, self.variables)
        definitions = PRAiSEInference._get_definitions(self.variables)
        self.model = "\n\n".join([definitions,
                            converted_formula + ";",
                            converted_weights + ";"])
    
    def compute_normalized_probability(self, query, evidence=None):

        model_evidence = self.model
        query_variables = dict(self.variables)
        if evidence:
            evidence = PRAiSEInference.convert_formula(evidence, query_variables)
            model_evidence += "\n\n" + evidence +";\n"

        query = PRAiSEInference.convert_formula(query, query_variables)
        new_variables = {k : v for k,v in query_variables.items() if k not in self.variables.keys()}
        new_vars_definition = PRAiSEInference._get_definitions(new_variables)
        model_evidence += "\n\n" + new_vars_definition

        with TemporaryDirectory(dir=".") as folder:

            temp_path = join(abspath(folder), "model.txt")
            with open(temp_path, "w") as f:
                f.write(model_evidence)

            tout = int(self.timeout / PRAiSEInference.POLL_DELTA)
            task = Popen(["java", "-jar", PRAiSEInference.JAR_PATH, temp_path,
            "--query", query], stdout=PIPE, stderr=PIPE)

            # polling every POLL_DELTA seconds
            while task.poll() is None and tout > 0:
                sleep(PRAiSEInference.POLL_DELTA)
                tout -= PRAiSEInference.POLL_DELTA

            if task.poll() != None:
                out, err = task.communicate()

                err = err.decode(sys.stdout.encoding)
                out = out.decode(sys.stdout.encoding)

                if len(err) > 0:
                    msg = "PRAiSE error: {}"
                    raise WMIRuntimeException(msg.format(err))

                return PRAiSEInference._parse_result(out)
        
            else:
                task.terminate()
                raise Exception("PRAiSE timed out")
        
    @staticmethod
    def _get_definitions(variables):
        definitions = []        
        for var_name, var_type in variables.items():
            if var_type == BOOL:
                definitions.append(pl.BooleanVar(var_name))
            elif var_type == REAL:
                definitions.append(pl.RealVar(var_name))
            else:
                raise WMIParsingError("Unknown type", None)
        return "\n".join(definitions)

    @staticmethod
    def _parse_result(praise_out):
        for line in praise_out.split("\n"):
            line = line.strip()
            if line.startswith("Result"):
                result_str = line.partition(": ")[-1].strip()
                try :
                    numerator, denominator = result_str.split("/")
                    numerator = int(float(numerator))
                    denominator = int(float(denominator))
                    return float(Fraction(numerator, denominator))
                except ValueError:
                    return float(result_str)
    
    @staticmethod
    def convert_formula(formula, variables):

        # 0-ariety expressions
        if formula.is_constant():
            return str(formula.constant_value()).lower()
        
        elif formula.is_symbol():
            # whenever a variable is found, return its name and optionally add
            # an entry to the variables dictionary with the corresponding type
            var_name = formula.symbol_name()
            var_type = formula.get_type()
            if var_name not in variables:
                variables[var_name] = var_type
            return var_name
        
        else:
            # recursively convert subformulas
            args = []
            for arg in formula.args():
                args.append(PRAiSEInference.convert_formula(arg, variables))

            # boolean operators
            if formula.is_not():
                assert(len(args) == 1)
                return pl.Not(args[0])
            
            elif formula.is_and():
                return pl.And(args)
            
            elif formula.is_or():
                return pl.Or(args)
            
            elif formula.is_implies():
                assert(len(args) == 2)
                return pl.Implies(args[0], args[1])
            
            elif formula.is_iff():
                assert(len(args) == 2)
                return pl.Iff(args[0], args[1])

            # theory relations
            elif formula.is_le():
                assert(len(args) == 2)
                return pl.LE(args[0], args[1])
            
            elif formula.is_lt():
                assert(len(args) == 2)
                return pl.LT(args[0], args[1])
            
            elif formula.is_equals():
                assert(len(args) == 2)
                return pl.Equals(args[0], args[1])

            # algebraic operators
            if formula.is_plus():
                return pl.Plus(args)
            
            elif formula.is_minus():
                return pl.Minus(args)
            
            elif formula.is_times():
                return pl.Times(args)
            
            elif is_pow(formula):
                assert(len(args) == 2)
                return pl.Pow(args[0], args[1])

            # if-then-else
            elif formula.is_ite():
                assert(len(args) == 3)
                return pl.Ite(args[0], args[1], args[2])
            
            else:
                raise WMIParsingError("Unhandled formula format", formula)


if __name__ == "__main__":
    from pysmt.shortcuts import Symbol, Ite, And, LE, LT, Real, Times, serialize
    from pysmt.typing import REAL

    def compute_print(method, query, evidence):
        print("query: ", serialize(query))
        print("evidence: ", serialize(evidence) if evidence else "-")
        prob = method.compute_normalized_probability(query, evidence)
        print("normalized: ", prob)
        print("--------------------------------------------------")

    x = Symbol("x", REAL)
    A = Symbol("A")
    support = And(LE(Real(-1), x), LE(x, Real(1)))
    weights = Ite(LT(Real(0), x),
                  Ite(A, Times(Real(2), x), x),
                  Ite(A, Times(Real(-2), x), Times(Real(-1),x)))

    praise = PRAiSEInference(support, weights)
    print("support: ", serialize(support))
    print("weights: ", serialize(weights))
    print("==================================================")

    suite = [(A, None),
             (And(A, LE(Real(0), x)), None),
             (LE(Real(0), x), A)]

    for query, evidence in suite:
        compute_print(praise, query, evidence)
