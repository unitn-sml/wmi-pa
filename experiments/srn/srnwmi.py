"""This module implements the WMI encoding for the Strategic Road
Network experiment.
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from pysmt.shortcuts import *
from pysmt.typing import REAL

from sys import path
path.insert(0, "../../src/")

#from wmiexception import WMIRuntimeException
from wmipa.wmiexception import WMIRuntimeException
from srnencodings import *


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

def AtMostOne(formulas):
    """Given a list of formulas [f_1, ... , f_k] returns a formula which
    evaluates to True IFF at most one f_i is True.

    """
    conjuncts = []
    for x in range(len(formulas)-1):
        for y in range(x+1, len(formulas)):
            conjuncts.append(Not(And(formulas[x], formulas[y])))
    return And(conjuncts)

def ExactlyOne(formulas):
    """Given a list of formulas [f_1, ... , f_k] returns a formula which
    evaluates to True IFF exactly one f_i is True.

    """    
    return And(Or(formulas), AtMostOne(formulas))
            

class SRNWMI:

    # variable names
    AUX_NAME = "aux_{}_{}"
    JOURNEY_NAME = "x_{}"
    TIME_NAME = "t_{}"

    def __init__(self, graph, partitions, encoding=ENC_DEF):
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
        self.encoding = encoding_dict(encoding)

    def compile_knowledge(self, path):
        """Generates the formula and the weight functions given the path.

        Keyword arguments:
        path -- The path in the graph.

        """
        if len(path) <= 1:
            raise WMIRuntimeException(WMIRuntimeException.OTHER_ERROR, "Path length should be > 1")
        
        self.n_steps = len(path)-1
        t_vars, x_vars = self._init_time_x_vars()
        aux_vars = self._init_aux_vars()
        transitions = []
        time_equations = []
        cond_weights = []
        
        for k in range(self.n_steps):
            
            # t^(k+1) = t^k + x^k
            teq = Equals(t_vars[k+1], Plus(t_vars[k], x_vars[k]))
            time_equations.append(teq)
            src, dst = path[k], path[k+1]
            
            # subformula encoding the transition from step k to step k+1
            trans_k = self._transition(k, src, dst, t_vars, x_vars, aux_vars)
            transitions.append(trans_k)
            
            # add weight functions
            for p in range(len(self.partitions)-1):
                poly_var = x_vars[k]
                coeffs = self.graph[src][dst][p]['coefficients']
                
                weight_f = SRNWMI._poly_weight(poly_var, coeffs)
                cond_w = Ite(self._interval_constr(p, k, aux_vars, t_vars), weight_f, Real(1))
                cond_weights.append(cond_w)

        self.formula = And(And(transitions), And(time_equations))
        
        if self.encoding[UNION_CONSTRAINTS]:
            # bound each t^k to fall into a partition
            union_interval = self.partitions[0], self.partitions[-1]
            union_constraints = [IntoInterval(t_vars[k], union_interval, True)
                                for k in range(len(t_vars))]
            self.formula = And(self.formula, And(union_constraints))

            
        self.time_vars = t_vars
        self.weights = Times(cond_weights)

    def _interval_constr(self, p, k, aux_vars, t_vars):
        if self.encoding[LABEL_AUX]:
            return aux_vars[(p, k)]
        else:
            pt = (self.partitions[p], self.partitions[p+1])
            interval = IntoInterval(t_vars[k], pt, False)
            return interval
        
    def arriving_before(self, time, index=-1):
        return LE(self.time_vars[index], Real(float(time)))
    
    def arriving_after(self, time, index=-1):
        return Not(LE(self.time_vars[index], Real(float(time))))

    def departing_at(self, time):
        return Equals(self.time_vars[0], Real(float(time)))
                                                                         
    def _transition(self, step, src, dst, t_vars, x_vars, aux_vars):        
        interval_constraints = []
        auxiliary_defs = []
        support_constraints = []
        
        for p in range(len(self.partitions)-1):

            tc = self._interval_constr(p, step, aux_vars, t_vars)
            interval_constraints.append(tc)

            pt = (self.partitions[p], self.partitions[p+1])
            interval = IntoInterval(t_vars[step], pt, False)
            
            if self.encoding[LABEL_AUX]:  
                if self.encoding[AUX_IFF]:
                    auxiliary_defs.append(Iff(aux_vars[(p, step)], interval))
                else:
                    auxiliary_defs.append(Implies(interval, aux_vars[(p, step)]))

            if self.encoding[THEORY_CHAINS]:
                lb1, not_lb2 = interval.args()
                auxiliary_defs.append(Implies(not_lb2.arg(0), lb1))
                
            # current time partition defines the range of the weight function
            # aux_p^k -> (R_p^min <= x^k <= R_p^max)
            rng = self.graph[src][dst][p]['range']
            support_constr = Implies(self._interval_constr(p, step, aux_vars, t_vars),
                                IntoInterval(x_vars[step], rng, True))
            support_constraints.append(support_constr)

        # bigwedge_p (aux_p^k <-> (P_p^begin <= t^k <= P_p^end))
        trans_formula = And(And(auxiliary_defs), And(support_constraints))
        
        if self.encoding[AUX_CONSTRAINTS] == 'xor':
            trans_formula = And(trans_formula, ExactlyOne(interval_constraints))
        elif self.encoding[AUX_CONSTRAINTS] == 'or':
            trans_formula = And(trans_formula, Or(interval_constraints))

        return trans_formula

    def _init_aux_vars(self):
        aux_vars = {}
        for p in range(len(self.partitions)-1):
            for k in range(self.n_steps):
                aux_vars[(p, k)] = Symbol(SRNWMI.AUX_NAME.format(p, k))
                
        return aux_vars

    def _init_time_x_vars(self):
        t_vars = []
        x_vars = []
        for k in range(self.n_steps):
            x_vars.append(
                Symbol(SRNWMI.JOURNEY_NAME.format(k), REAL))
            t_vars.append(Symbol(SRNWMI.TIME_NAME.format(k), REAL))
        t_vars.append(Symbol(SRNWMI.TIME_NAME.format(self.n_steps), REAL))
        return t_vars, x_vars    

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

        
