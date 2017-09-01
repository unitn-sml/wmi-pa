"""This module implements the PRAiSE encoding for the Strategic Road
Network experiment
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from math import ceil, log

from pysmt.shortcuts import *
from pysmt.typing import REAL

from sys import path
path.insert(0, "../../src/")

from wmiexception import WMIRuntimeException

def AtLeastOne(terms):
    return "(" + " or ".join(terms) + ");"

def AtMostOne(terms):
    excl = []
    for i in xrange(len(terms) - 1):
        for j in xrange(i+1, len(terms)):
            not_both = "(not ({} and {}))".format(terms[i], terms[j])
            excl.append(not_both)
    return "(" + " and ".join(excl) + ");"
    
def ExactlyOne(terms):    
    return "{}\n{}".format(AtLeastOne(terms), AtMostOne(terms))
    

# some utility functions
def IntoInterval(var, interval, closed):
    """Given an LRA variable x and an interval (lower, upper), returns the SMT
    formula ((lower <= x) and (x <= upper)) or ((lower <= x) and (x < upper)).

    Keyword arguments:
    var -- the variable name
    interval -- a pair (lower_bound, upper_bound)
    closed -- Boolean, True iff the interval is closed.

    """
    lower, upper = map(float, interval)
    if closed:
        rel = "<="
    else:
        rel = "<"
    return "(({} <= {}) and ({} {} {}))".format(lower, var, var, rel, upper)

class SRNPRAiSE:

    ENC_DEF = "def_enc"
    ENC_OR = "or_enc"
    ENC_XOR = "xor_enc"
    ENCODINGS = [ENC_DEF, ENC_OR, ENC_XOR]

    # default variable names
    JOURNEY_NAME = "xe{}"
    TIME_NAME = "te{}"

    

    def __init__(self, graph, partitions, encoding=ENC_OR):
        """Default constructor.
        Initializes the query-independent data.

        Keyword arguments:
        graph -- Strategic Road Network directed graph
        partitions -- list of the bounds of the partitions

        """        
        self.graph = graph
        self.partitions = partitions
        self.model = None
        self.encoding = encoding

    @staticmethod
    def real_var(name):
        return "random {} : Real;".format(name)

    def compile_knowledge(self, path, t_departure):
        """Generates the model according to the given path.

        Keyword arguments:
        path -- a path in the SRN graph
        t_departure -- departure time.

        """
        if len(path) <= 1:
            raise WMIRuntimeException("Path length should be > 1")

        self.n_steps = len(path)-1
        assertions = []
        t_vars = []
        jt_vars = []
        for k in xrange(self.n_steps):
            jtk = SRNPRAiSE.JOURNEY_NAME.format(k)
            tk = "(" + " + ".join([str(float(t_departure))] + jt_vars) + ")"
            t_vars.append(tk)
            jt_vars.append(jtk)
            assertions.append(SRNPRAiSE.real_var(jtk))

        t_last = "(" + " + ".join([str(float(t_departure))] + jt_vars) + ")"
        t_vars.append(t_last)
        
        for k in xrange(self.n_steps):
            src, dst = path[k], path[k+1]
            step_xor = []
            for p in xrange(len(self.partitions)-1):
                partition = (self.partitions[p], self.partitions[p+1])
                cond = IntoInterval(t_vars[k], partition, False)
                rng = self.graph[src][dst][p]['range']
                rng_expr = IntoInterval(jt_vars[k], rng, True)
                rng_constr = "({} => {});".format(cond, rng_expr)
                assertions.append(rng_constr)
                coeffs = self.graph[src][dst][p]['coefficients']
                pos = SRNPRAiSE._poly_weight(jt_vars[k], coeffs)
                neg = 1
                potential = "if {}\nthen {}\nelse {};".format(cond, pos, neg)
                assertions.append(potential)
                step_xor.append(cond)

            if self.encoding == SRNPRAiSE.ENC_OR:
                assertions.append(AtLeastOne(step_xor))
            elif self.encoding == SRNPRAiSE.ENC_XOR:
                assertions.append(ExactlyOne(step_xor))            

        # bound each t^final to fall into a partition
        t_domain = (self.partitions[0], self.partitions[-1])
        assertions.append("{};".format(IntoInterval(t_vars[-1], t_domain, True)))
        self.model = "\n".join(assertions)
        self.time_vars = t_vars

    def arriving_after(self, time, index=-1):
        return "({} > {})".format(self.time_vars[index], float(time))

    def arriving_before(self, time, index=-1):
        return "({} <= {})".format(self.time_vars[index], float(time))

    def departing_at(self, time):
        return "({} = {})".format(self.time_vars[0], float(time))

    @staticmethod
    def _poly_weight(variable, coefficients):
        monomials = []
        max_degree = len(coefficients)-1

        for i, coefficient in enumerate(coefficients):
            exponent = max_degree-i
            if exponent > 0 :                
                monomial = "({} * ({} ^ {}))".format(float(coefficient),
                                                     variable,
                                                     float(exponent))
            else:
                monomial = "({})".format(float(coefficient))

            monomials.append(monomial)
        return " + ".join(monomials)

        
