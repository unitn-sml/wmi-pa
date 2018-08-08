"""This module implements the PRAiSE encoding for the Strategic Road
Network experiment
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from math import ceil, log

#from pysmt.shortcuts import *
from pysmt.typing import REAL

from sys import path
path.insert(0, "../../src/")

from wmiexception import WMIRuntimeException
from srnencodings import *
from praiselang import Or, And, Not, Implies, Iff, RealVar, BooleanVar, \
    ExactlyOne, LE, LT, Equals, Plus, Pow, Times, Ite, Real


# some utility functions
def IntoInterval(var, interval, closed):
    """Given an LRA variable x and an interval (lower, upper), returns the SMT
    formula ((lower <= x) and (x <= upper)) or ((lower <= x) and (x < upper)).

    Keyword arguments:
    var -- the variable name
    interval -- a pair (lower_bound, upper_bound)
    closed -- Boolean, True iff the interval is closed.

    """
    lower, upper = map(Real, interval)
    if closed:
        upper_bound = LE(var, upper)
    else:
        upper_bound = Not(LE(upper, var))

    return And([LE(lower, var), upper_bound])

class SRNPRAiSE:

    # default variable names
    AUX_NAME = "aux_{}_{}"
    JOURNEY_NAME = "x_{}"
    # TIME_NAME = "t_{}"    

    def __init__(self, graph, partitions, encoding=ENC_DEF, use_aux_vars=False):
        """Default constructor.
        Initializes the query-independent data.

        Keyword arguments:
        graph -- Strategic Road Network directed graph
        partitions -- list of the bounds of the partitions
        use_aux_vars -- use auxiliary Boolean vars (default: False)

        """        
        self.graph = graph
        self.partitions = partitions
        self.model = None
        self.encoding = encoding_dict(encoding)
        self.use_aux_vars = use_aux_vars

    def compile_knowledge(self, path, t_departure):
        """Generates the model according to the given path.

        Keyword arguments:
        path -- a path in the SRN graph
        t_departure -- departure time.

        """
        if len(path) <= 1:
            raise WMIRuntimeException("Path length should be > 1")

        self.n_steps = len(path)-1
        t_vars, x_vars, aux_vars = self._init_vars(t_departure)
        variable_definitions = [RealVar(x) for x in x_vars]

        if self.use_aux_vars:
            variable_definitions += [BooleanVar(a)
                                     for ak in aux_vars for a in ak]

        statements = []
        cond_weights = []

        # initialize t_0 (in WMI, this is passed as evidence)
        #time_equations.append(Equals(t_vars[0], str(t_departure)))

        for k in range(self.n_steps):

            # t^(k+1) = t^k + x^k
            #teq = Equals(t_vars[k+1], Plus([t_vars[k], x_vars[k]]))
            #time_equations.append(teq)

            src, dst = path[k], path[k+1]
            
            # subformula encoding the transition from step k to step k+1
            trans_k = self._transition(k, src, dst, t_vars, x_vars, aux_vars)
            statements.append(trans_k)            

            for p in range(len(self.partitions)-1):
                poly_var = x_vars[k]
                coeffs = self.graph[src][dst][p]['coefficients']
                
                weight_f = SRNPRAiSE._poly_weight(poly_var, coeffs)
                cond_w = Ite(aux_vars[(p, k)], weight_f, Real(1))
                cond_weights.append(cond_w)

        if self.encoding[UNION_CONSTRAINTS]:
            # bound each t^k to fall into a partition
            union_interval = self.partitions[0], self.partitions[-1]
            union_constraints = [IntoInterval(t_vars[k], union_interval, True)
                                for k in range(len(t_vars))]
            statements = statements + union_constraints

        add_terminator = lambda s : s + ";"
        statements = map(add_terminator, statements + cond_weights)
        self.model = "\n".join(variable_definitions + statements)
        self.time_vars = t_vars

    def _transition(self, step, src, dst, t_vars, x_vars, aux_vars):        
        auxiliary_vars = []
        auxiliary_defs = []
        support_constraints = []
        
        for p in range(len(self.partitions)-1):
            last = (p == len(self.partitions)-2)            
            aux = aux_vars[(p, step)]
            auxiliary_vars.append(aux)
            pt = (self.partitions[p], self.partitions[p+1])

            if self.use_aux_vars:
                interval = IntoInterval(t_vars[step], pt, last)
                if self.encoding[AUX_IFF]:
                    aux_def = Iff(aux, interval)
                else:
                    aux_def = Implies(interval, aux)

                auxiliary_defs.append(aux_def)

            if self.encoding[THEORY_CHAINS] and not last:
                lb1 = LE(Real(pt[0]), t_vars[step])
                lb2 = LE(Real(pt[1]), t_vars[step])
                auxiliary_defs.append(Implies(lb2, lb1))
                
            # current time partition defines the range of the weight function
            # aux_p^k -> (R_p^min <= x^k <= R_p^max)
            rng = self.graph[src][dst][p]['range']
            support_constr = Implies(aux_vars[(p, step)],
                                IntoInterval(x_vars[step], rng, True))
            support_constraints.append(support_constr)

        # bigwedge_p (aux_p^k <-> (P_p^begin <= t^k <= P_p^end))
        trans_formula = And(support_constraints)
        if len(auxiliary_defs) > 0:
            trans_formula = And([trans_formula, And(auxiliary_defs)])

        if self.use_aux_vars:
            if self.encoding[AUX_CONSTRAINTS] == 'xor':
                trans_formula = And([trans_formula, ExactlyOne(auxiliary_vars)])
            elif self.encoding[AUX_CONSTRAINTS] == 'or':
                trans_formula = And([trans_formula, Or(auxiliary_vars)])

        return trans_formula
    


    def  _init_vars(self, t_init):
        t_vars = ["({})".format(t_init)]
        x_vars = []
        aux_vars = {}

        for k in range(self.n_steps):
            x_vars.append(SRNPRAiSE.JOURNEY_NAME.format(k))
            prev = " + ".join(x_vars)
            tvar = "({} + {})".format(t_init, prev)
            t_vars.append(tvar)

            for p in range(len(self.partitions)-1):
                if self.use_aux_vars:
                    avar = SRNPRAiSE.AUX_NAME.format(p, k)
                else:
                    last = (p == len(self.partitions)-2)
                    partition = (self.partitions[p], self.partitions[p+1])
                    avar = IntoInterval(t_vars[k], partition, last)
                
                aux_vars[(p, k)] = avar

        return t_vars, x_vars, aux_vars

    def arriving_after(self, time, index=-1):
        return Not(LE(self.time_vars[index], Real(time)))

    def arriving_before(self, time, index=-1):
        return LE(self.time_vars[index], Real(time))

    def departing_at(self, time):
        return Equals(self.time_vars[0], Real(time))

    @staticmethod
    def _poly_weight(variable, coefficients):
        monomials = []
        max_degree = len(coefficients)-1

        for i, coefficient in enumerate(coefficients):
            exponent = max_degree-i
            if exponent > 0:
                monomial = Times([Real(coefficient),
                                  Pow(variable, Real(exponent))])
            else:
                monomial = Real(coefficient)

            monomials.append(monomial)
        return Plus(monomials)

        
