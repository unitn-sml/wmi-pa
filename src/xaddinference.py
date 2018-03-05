"""This module leverages XADDs to implement an inference engine that
allows queries of the form P(Q(x,A)|E(x,A)) over an hybrid model
expressed by a weight formula w(x,A) and support Chi(x,A). Q, E, w and
Chi are SMT-LRA formulas.

"""
__version__ = '0.999'
__author__ = 'Paolo Morettin'

from os.path import dirname, abspath
from subprocess import Popen, PIPE
from time import sleep
import xaddnestedlang as nl
from pysmt.typing import REAL, BOOL

from wmiexception import WMIRuntimeException, WMIParsingError,\
    WMITimeoutException
from pysmt2latte import is_pow


class XADDInference:

    DEF_PATH_MODEL = "xadd_model.txt"
    DEF_PATH_QUERY = "xadd_query.txt"    
    DEF_TIMEOUT = 10000
    POLL_DELTA = 1

    JAR_NAME = "xxxadd.jar"
    JAR_PATH = dirname(abspath(__file__)) + "/thirdparties/" + JAR_NAME

    def __init__(self, support, weights, timeout=None):
        self.timeout = timeout or XADDInference.DEF_TIMEOUT
        self.convert(support, weights)

    def convert(self, support, weights):
        converted_support = nl.formulaIntoEvidence(
            XADDInference.convert_formula(support))
        converted_weights = XADDInference.convert_formula(weights)

        self.model = nl.Times([converted_support, converted_weights])
                    
    def compute_normalized_probability(self, query, evidence=None):

        model_path = XADDInference.DEF_PATH_MODEL
        query_path = XADDInference.DEF_PATH_QUERY

        model_evidence = self.model
        if evidence:
            if not isinstance(evidence, str):
                evidence = nl.formulaIntoEvidence(
                    XADDInference.convert_formula(evidence))
                model_evidence = nl.Times([model_evidence, evidence])
                
        with open(model_path, "w") as f:
            f.write(model_evidence)

        if not isinstance(query, str):
            query = XADDInference.convert_formula(query)

        with open(query_path, "w") as f:
            f.write(query)            

        tout = int(self.timeout / XADDInference.POLL_DELTA)
        task = Popen(["java", "-jar", XADDInference.JAR_PATH, model_path,
                      query_path], stdout=PIPE, stderr=PIPE)

        # polling every POLL_DELTA seconds
        while task.poll() is None and tout > 0:
            sleep(XADDInference.POLL_DELTA)
            tout -= XADDInference.POLL_DELTA

        if task.poll() != None:
            out, err = task.communicate()

            if err != '':
                msg = "XADD error: {}"
                raise WMIRuntimeException(msg.format(err))

            return XADDInference._parse_result(out)
        
        else:
            task.terminate()
            raise WMITimeoutException()

        
    @staticmethod
    def _parse_result(result_str):
        for line in result_str.split("\n"):
            line = line.strip()
            if line.startswith("Normalized"):
                result_str = line.partition(": ")[-1].strip()
                return float(result_str)
    

    @staticmethod
    def convert_formula(formula):

        # 0-ariety expressions
        if formula.is_constant():
            return str(formula.constant_value()).lower()
        
        elif formula.is_symbol():
            var_name = formula.symbol_name()
            return nl.Symbol(var_name)
        
        else:
            # recursively convert subformulas
            args = []
            for arg in formula.args():
                args.append(XADDInference.convert_formula(arg))

            # boolean operators
            if formula.is_not():
                assert(len(args) == 1)
                return nl.Not(args[0])
            
            elif formula.is_and():
                return nl.And(args)
            
            elif formula.is_or():
                return nl.Or(args)
            
            elif formula.is_implies():
                assert(len(args) == 2)
                return nl.Implies(args[0], args[1])
            
            elif formula.is_iff():
                assert(len(args) == 2)
                return nl.Iff(args[0], args[1])

            # theory relations
            elif formula.is_le():
                assert(len(args) == 2)
                return nl.LE(args[0], args[1])
            
            elif formula.is_lt():
                assert(len(args) == 2)
                return nl.LT(args[0], args[1])
            
            elif formula.is_equals():
                assert(len(args) == 2)
                return nl.Equals(args[0], args[1])

            # algebraic operators
            if formula.is_plus():
                return nl.Plus(args)
            
            elif formula.is_minus():
                return nl.Minus(args)
            
            elif formula.is_times():
                return nl.Times(args)
            
            elif is_pow(formula):
                assert(len(args) == 2)
                return nl.Pow(args[0], args[1])

            # if-then-else
            elif formula.is_ite():
                assert(len(args) == 3)
                return nl.Ite(args[0], args[1], args[2])
            
            else:
                raise WMIParsingError("Unhandled formula format", formula)


if __name__ == "__main__":
    from pysmt.shortcuts import Symbol, Ite, And, LE, LT, Real, Times, serialize
    from pysmt.typing import REAL

    def compute_print(method, query, evidence):
        print "query: ", serialize(query)
        print "evidence: ", serialize(evidence) if evidence else "-"
        prob = method.compute_normalized_probability(query, evidence)
        print "normalized: ", prob
        print "--------------------------------------------------"

    x = Symbol("x", REAL)
    A = Symbol("A")
    support = And(LE(Real(-1), x), LE(x, Real(1)))
    weights = Ite(LT(Real(0), x),
                  Ite(A, Times(Real(2), x), x),
                  Ite(A, Times(Real(-2), x), Times(Real(-1),x)))

    xadd = XADDInference(support, weights)
    print "support: ", serialize(support)
    print "weights: ", serialize(weights)
    print "=================================================="

    suite = [(A, None),
             (And(A, LE(Real(0), x)), None),
             (LE(Real(0), x), A)]

    for query, evidence in suite:
        compute_print(xadd, query, evidence)
