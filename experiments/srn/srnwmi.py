"""This module implements the WMI encoding for the Strategic Road
Network experiment.
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from math import ceil, log

from pysmt.shortcuts import *
from pysmt.typing import REAL

from sys import path
path.insert(0, "../../src/")

from wmiexception import WMIRuntimeException


# some utility functions
def IntoInterval(variable, interval, closed):
    """Given an LRA variable x and an interval (lower, upper), returns the SMT
    formula ((lower <= x) and (x <= upper)) or ((lower <= x) and (x < upper)).

    Keyword arguments:
    var -- the variable
    interval -- a pair (lower_bound, upper_bound)
    closed -- Boolean, True iff the interval is closed.

    """
    lower, upper = map(lambda x : Real(float(x)),interval)
    if closed:
        upper_bound = LE(variable, upper)
    else:
        upper_bound = Not(LE(upper, variable))
    return And(LE(lower, variable), upper_bound)

def AtLeastOne(formulas):
    return Or(formulas)

def AtMostOne(formulas):
    """Given a list of formulas [f_1, ... , f_k] returns a formula which
    evaluates to True IFF at most one f_i is True.

    """
    conjuncts = []
    for x in xrange(len(formulas)-1):
        for y in xrange(x+1, len(formulas)):
            conjuncts.append(Not(And(formulas[x], formulas[y])))
    return And(conjuncts)

def ExactlyOne(formulas):
    """Given a list of formulas [f_1, ... , f_k] returns a formula which
    evaluates to True IFF exactly one f_i is True.

    """    
    return And(AtLeastOne(formulas), AtMostOne(formulas))
            

class SRNWMI:

    ENC_DEF = "def_enc"
    ENC_OR = "or_enc"
    ENC_XOR = "xor_enc"
    ENC_ALT = "alt_enc"
    ENCODINGS = [ENC_DEF, ENC_OR, ENC_XOR, ENC_ALT]

    # variable names
    AUX_NAME = "aux_{}e{}"
    JOURNEY_NAME = "xe{}"
    TIME_NAME = "te{}"

    def __init__(self, graph, partitions, encoding=ENC_ALT):
        """Default constructor.
        Initializes the query-independent data.

        Keyword arguments:
        graph -- Strategic Road Network directed graph
        partitions -- list of the bounds of the partitions

        """        
        self.graph = graph
        self.partitions = partitions
        self.formula = None
        self.weights = None
        self.encoding = encoding

    def compile_knowledge(self, path):
        """Generates the formula and the weight functions according to the
        given path.

        Keyword arguments:
        path -- The path in the graph.

        """
        if len(path) <= 1:
            raise WMIRuntimeException("Path length should be > 1")
        
        self.n_steps = len(path)-1
        t_vars, jt_vars = self._init_time_jt_vars()
        aux_vars = self._init_aux_vars()
        transitions = []
        time_equations = []
        cond_weights = []
        for k in xrange(self.n_steps):
            # t^(k+1) = t^k + x^k
            teq = Equals(t_vars[k+1], Plus(t_vars[k], jt_vars[k]))
            time_equations.append(teq)
            src, dst = path[k], path[k+1]
            # subformula encoding the transition from step k to step k+1
            trans_k = self._transition(k, src, dst, t_vars, jt_vars, aux_vars)
            transitions.append(trans_k)
            # add weight functions
            for p in xrange(len(self.partitions)-1):
                poly_var = jt_vars[k]
                coeffs = self.graph[src][dst][p]['coefficients']
                
                weight_f = SRNWMI._poly_weight(poly_var, coeffs)
                cond_w = Ite(aux_vars[(p, k)], weight_f, Real(1))
                cond_weights.append(cond_w)

        if self.encoding == SRNWMI.ENC_ALT :
            # bound each t^k to fall into a partition
            t_min, t_max = self.partitions[0], self.partitions[-1]
            time_constraints = [IntoInterval(t_vars[k], (t_min, t_max), True)
                                for k in xrange(len(t_vars))]

            self.formula = And(And(transitions), And(time_equations),
                               And(time_constraints))
        else:
            self.formula = And(And(transitions), And(time_equations))
        self.time_vars = t_vars
        self.weights = Times(cond_weights)
        
    def arriving_before(self, time, index=-1):
        return LE(self.time_vars[index], Real(float(time)))
    
    def arriving_after(self, time, index=-1):
        return Not(LE(self.time_vars[index], Real(float(time))))

    def departing_at(self, time):
        return Equals(self.time_vars[0], Real(float(time)))
                                                                         
    def _transition(self, step, src, dst, t_vars, jt_vars, aux_vars):        
        partition_vars = []
        partition_defs = []
        range_constraints = []
        for p in xrange(len(self.partitions)-1):
            aux = aux_vars[(p, step)]
            partition = (self.partitions[p], self.partitions[p+1])
            interval = IntoInterval(t_vars[step], partition, False)
            partition_vars.append(aux)
            if self.encoding == SRNWMI.ENC_ALT:
                partition_defs.append(Implies(interval, aux))
            else :
                partition_defs.append(Iff(aux, interval))                
                lb1, not_lb2 = interval.args()
                partition_defs.append(Implies(not_lb2.arg(0), lb1))            
            # current time partition defines the range of the weight function
            # aux_p^k -> (R_p^min <= x^k <= R_p^max)
            rng = self.graph[src][dst][p]['range']
            rng_constr = Implies(aux_vars[(p, step)],
                                IntoInterval(jt_vars[step], rng, True))
            range_constraints.append(rng_constr)

        # bigwedge_p (aux_p^k <-> (P_p^begin <= t^k <= P_p^end))
        partition_definitions = And(partition_defs)
        trans_formula = And(partition_definitions, And(range_constraints))
        
        if self.encoding == SRNWMI.ENC_XOR or self.encoding == SRNWMI.ENC_ALT:
            return And(trans_formula, ExactlyOne(partition_vars))
        elif self.encoding == SRNWMI.ENC_OR:
            return And(trans_formula, AtLeastOne(partition_vars))
        else:
            return trans_formula

    def _init_aux_vars(self):
        aux_vars = {}
        for p in xrange(len(self.partitions)-1):
            for k in xrange(self.n_steps):
                aux_vars[(p, k)] = Symbol(SRNWMI.AUX_NAME.format(p, k))
                
        return aux_vars

    def _init_time_jt_vars(self):
        t_vars = []
        jt_vars = []
        for k in xrange(self.n_steps):
            jt_vars.append(
                Symbol(SRNWMI.JOURNEY_NAME.format(k), REAL))
            t_vars.append(Symbol(SRNWMI.TIME_NAME.format(k), REAL))
        t_vars.append(Symbol(SRNWMI.TIME_NAME.format(self.n_steps), REAL))
        return t_vars, jt_vars    

    @staticmethod
    def _poly_weight(variable, coefficients):
        monomials = []
        max_degree = len(coefficients)-1

        for i, coefficient in enumerate(coefficients):
            exponent = max_degree-i
            if exponent > 0 :                
                monomial = Times(Real(float(coefficient)),
                                 Pow(variable, Real(exponent)))
            else:
                monomial = Real(float(coefficient))

            monomials.append(monomial)
        return Plus(monomials)

        
