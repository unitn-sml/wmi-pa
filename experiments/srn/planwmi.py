"""This module implements the WMI encoding for the SRN Planning experiment.
"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from itertools import product

from pysmt.shortcuts import *
from pysmt.typing import REAL, BOOL

from sys import path
path.insert(0, "../../src/")

from wmipa.wmiexception import WMIRuntimeException
from srnwmi import ExactlyOne, IntoInterval
from srnencodings import *


class PlanWMI():

    # variable names
    AUX_NAME = "aux_{}_{}"
    JOURNEY_NAME = "x_{}"
    TIME_NAME = "t_{}"
    LOC_NAME = "loc_{}_{}"

    def __init__(self, partitions, conditional_plan, encoding=ENC_DEF):
        """Default constructor.
        Initializes the query-independent data.

        Keyword arguments:
        partitions -- list of the bounds of the partitions
        conditional_plan -- mapping: (curr_loc, curr_interval, destination) -> next_loc

        """
        self.conditional_plan = conditional_plan
        self.partitions = partitions
        self.formula = None
        self.weights = None
        self.encoding = encoding_dict(encoding)        

    def compile_knowledge(self, subgraph, n_steps, init_location, final_location):
        """Generates the formula and the weight functions according to the
        path length, initial and final locations.

        Keyword arguments:
        subgraph -- subpart of the road network
        n_steps -- path length
        init_location -- str
        final_location -- str

        """
        if n_steps < 1:
            raise WMIRuntimeException("Path length should be > 0")

        self.n_steps = n_steps
        self.locations = list(subgraph.nodes())

        t_vars, x_vars, loc_vars, aux_vars = self._init_vars()
        subformulas = []

        for k in range(self.n_steps+1):
            # exactly one location at each step    
            subformulas.append(ExactlyOne(loc_vars[k]))

        relevant_edges = set()    
        for k in range(self.n_steps):
            # t^(k+1) = t^k + x^k
            teq = Equals(t_vars[k+1], Plus(t_vars[k], x_vars[k]))
            subformulas.append(teq)

            # each x^k should be nonnegative
            nonneg_x_k = LE(Real(0), x_vars[k])
            subformulas.append(nonneg_x_k)

            if self.encoding[AUX_CONSTRAINTS] == 'xor':
                subformulas.append(ExactlyOne(aux_vars[k]))
            elif self.encoding[AUX_CONSTRAINTS] == 'or':
                subformulas.append(Or(aux_vars[k]))           

            for l in range(len(self.locations)):
                src = self.locations[l]
                cond = loc_vars[k][l]
                subsubformulas = []
                
                for p in range(len(self.partitions)-1):
                    nxt = self.conditional_plan[(src, p, final_location)]
                    if nxt in self.locations:
                        nxt_expr = loc_vars[k+1][self.locations.index(nxt)]
                        
                        if src != nxt:
                            relevant_edges.add((src, nxt))
                            rng = subgraph[src][nxt][p]['range']
                            rng_expr = IntoInterval(x_vars[k], rng, True)
                        else:
                            rng_expr = Equals(x_vars[k], Real(0))
                                                                               
                        ssf = Implies(aux_vars[k][p], And(rng_expr, nxt_expr))
                        subsubformulas.append(ssf)                    
                        
                subformulas.append(Implies(cond, And(subsubformulas)))
                        
            for p in range(len(self.partitions)-1):
                last = (p == len(self.partitions)-2)
                partition = (self.partitions[p], self.partitions[p+1])
                interval = IntoInterval(t_vars[k], partition, last)
                if self.encoding[AUX_IFF]:
                    subformulas.append(Iff(aux_vars[k][p], interval))
                else:
                    subformulas.append(Implies(interval, aux_vars[k][p]))

                if self.encoding[THEORY_CHAINS] and not last:
                    lb1, not_lb2 = interval.args()
                    subformulas.append(Implies(not_lb2.arg(0), lb1))

        # initialization
        subformulas.append(loc_vars[0][self.locations.index(init_location)])
        subformulas.append(loc_vars[self.n_steps]
                           [self.locations.index(final_location)])
        
        self.formula = And(subformulas)

        if self.encoding[UNION_CONSTRAINTS]:
            # bound each t^k to fall into a partition
            union_interval = self.partitions[0], self.partitions[-1]
            union_constraints = [IntoInterval(t_vars[k], union_interval, True)
                                for k in range(len(t_vars))]
            self.formula = And(self.formula, And(union_constraints))

        self.time_vars = t_vars
        self.location_vars = loc_vars
        self.weights = self._compute_weights(subgraph, relevant_edges, aux_vars,
                                             loc_vars, x_vars)
        
        msg = "real variables: {}, boolean variables: {}"
        nreals = len([v for v in self.formula.get_free_variables()
                      if v.get_type() == REAL])
        nbools = len([v for v in self.formula.get_atoms()
                      if v.get_type() == BOOL])
        print(msg.format(nreals, nbools))

    def _compute_weights(self, subgraph, edges, aux_vars, loc_vars, x_vars):
        #loc_indexes = range(len(self.locations))
        conditionals = []
        for i in range(self.n_steps):
            for src, dst in edges:
                l1 = self.locations.index(src)
                l2 = self.locations.index(dst)                
                cond = And(loc_vars[i][l1], loc_vars[i+1][l2])
                subconditionals = []
                for p in range(len(self.partitions)-1):
                    subcond = aux_vars[i][p]
                    poly_var = x_vars[i]
                    coeffs = subgraph[src][dst][p]['coefficients']
                    weight_f = PlanWMI._poly_weight(poly_var, coeffs)
                    subconditionals.append(Ite(subcond, weight_f, Real(1)))

                conditional = Ite(cond, Times(subconditionals), Real(1))
                conditionals.append(conditional)
                
        return Times(conditionals)
        
    def arriving_before(self, time):
        return LE(self.time_vars[-1], Real(float(time)))
    
    def departing_at(self, time):
        return Equals(self.time_vars[0], Real(float(time)))

    def _init_vars(self):
        t_vars = []
        x_vars = []
        loc_vars = []
        aux_vars = []
    
        for k in range(self.n_steps+1):
            t_vars.append(Symbol(PlanWMI.TIME_NAME.format(k), REAL))            
            loc_k = []
            for l in range(len(self.locations)):
                var = Symbol(PlanWMI.LOC_NAME.format(k, l))
                loc_k.append(var)
            loc_vars.append(loc_k)
        
        for k in range(self.n_steps):
            x_vars.append(Symbol(PlanWMI.JOURNEY_NAME.format(k), REAL))
            aux_k = []
            for p in range(len(self.partitions)-1):            
                aux_k.append(Symbol(PlanWMI.AUX_NAME.format(p, k)))
                
            aux_vars.append(aux_k)                
                
        return t_vars, x_vars, loc_vars, aux_vars

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

        
