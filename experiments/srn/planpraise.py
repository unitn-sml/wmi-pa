"""This module implements the PRAiSE encoding for the Strategic Road
Network experiment

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from math import ceil, log

from sys import path
path.insert(0, "../../src/")

from wmiexception import WMIRuntimeException
from srnencodings import *
from praiselang import Or, And, Not, Implies, Iff, RealVar, BooleanVar, \
    ExactlyOne, LE, LT, Equals, Plus, Pow, Times, Ite, Real
from srnpraise import IntoInterval
    

class PlanPRAiSE:

    # default variable names
    JOURNEY_NAME = "x_{}"
    LOC_NAME = "l_{}_{}"
    AUX_NAME = "aux_{}_{}"

    def __init__(self, partitions, conditional_plan, encoding=ENC_DEF,
                 use_aux_vars=False):
        """Default constructor.
        Initializes the query-independent data.

        Keyword arguments:
        partitions -- list of the bounds of the partitions
        conditional_plan -- mapping: (curr_loc, curr_interval, destination) -> next_loc
        use_aux_vars -- use auxiliary Boolean vars (default: False)

        """
        self.conditional_plan = conditional_plan
        self.partitions = partitions
        self.model = None
        self.encoding = encoding_dict(encoding)
        self.use_aux_vars = use_aux_vars

    def compile_knowledge(self, subgraph, n_steps, init_location,
                          final_location, t_departure):
        """Generates the model according to the path length, initial and final
        locations.

        Keyword arguments:
        subgraph -- subpart of the road network
        n_steps -- path length
        init_location -- str
        final_location -- str
        t_departure -- departure time

        """
        if n_steps < 1:
            raise WMIRuntimeException("Path length should be > 0")

        self.n_steps = n_steps
        self.locations = subgraph.nodes()

        t_vars, x_vars, loc_vars, aux_vars = self._init_vars(t_departure)
        variable_definitions = [RealVar(x) for x in x_vars] + \
                               [BooleanVar(l) for lk in loc_vars
                                for l in lk]

        if self.use_aux_vars:
            variable_definitions += [BooleanVar(a)
                                     for ak in aux_vars for a in ak]
        
        subformulas = []
        
        for k in range(self.n_steps+1):
            # exactly one location at each step
            subformulas.append(ExactlyOne(loc_vars[k]))
            
        relevant_edges = set()
        for k in range(self.n_steps):
            # each x^k should be nonnegative
            nonneg_x_k = LE(Real(0), x_vars[k])
            subformulas.append(nonneg_x_k)            

            if self.use_aux_vars:
                if self.encoding[AUX_CONSTRAINTS] == 'xor':
                    subformulas.append(ExactlyOne(aux_vars[k]))
                elif self.encoding[AUX_CONSTRAINTS] == 'or':
                    subformulas.append(Or(aux_vars[k]))           
            
            #step_xor = set()            
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

                        ssf = Implies(aux_vars[k][p], And([rng_expr, nxt_expr]))
                        subsubformulas.append(ssf)            

                if len(subsubformulas) > 0:
                    subformulas.append(Implies(cond, And(subsubformulas)))

            for p in range(len(self.partitions)-1):
                last = (p == len(self.partitions)-2)
                partition = (self.partitions[p], self.partitions[p+1])

                if self.use_aux_vars:
                    interval = IntoInterval(t_vars[k], partition, last)
                    if self.encoding[AUX_IFF]:
                        subformulas.append(Iff(aux_vars[k][p], interval))
                    else:
                        subformulas.append(Implies(interval, aux_vars[k][p]))

                if self.encoding[THEORY_CHAINS] and not last:
                    lb1 = LE(Real(partition[0]), t_vars[k])
                    lb2 = LE(Real(partition[1]), t_vars[k])
                    subformulas.append(Implies(lb2, lb1))


        # initialization
        subformulas.append(loc_vars[0][self.locations.index(init_location)])
        subformulas.append(loc_vars[self.n_steps]
                           [self.locations.index(final_location)])
                    
        if self.encoding[UNION_CONSTRAINTS]:
            # bound each t^k to fall into a partition
            union_interval = self.partitions[0], self.partitions[-1]
            union_constraints = [IntoInterval(t_vars[k], union_interval, True)
                                for k in range(len(t_vars))]
            subformulas.append(And(union_constraints))

        cond_weights = self._compute_weights(subgraph, relevant_edges, aux_vars,
                                             loc_vars, x_vars)
            
        add_terminator = lambda s : s + ";"
        subformulas = map(add_terminator, subformulas + cond_weights)
        self.model = "\n".join(variable_definitions + subformulas)
        self.time_vars = t_vars
        

    def _compute_weights(self, subgraph, edges, aux_vars, loc_vars, x_vars):
        conditionals = []
        for i in range(self.n_steps):
            for src, dst in edges:
                l1 = self.locations.index(src)
                l2 = self.locations.index(dst)                
                cond = And([loc_vars[i][l1], loc_vars[i+1][l2]])
                subconditionals = []
                for p in range(len(self.partitions)-1):
                    subcond = aux_vars[i][p]
                    poly_var = x_vars[i]
                    coeffs = subgraph[src][dst][p]['coefficients']
                    weight_f = PlanPRAiSE._poly_weight(poly_var, coeffs)
                    subconditionals.append(Ite(subcond, weight_f, Real(1)))

                conditional = Ite(cond, Times(subconditionals), Real(1))
                conditionals.append(conditional)
                
        return conditionals
        

    def  _init_vars(self, t_init):
        t_vars = [Real(t_init)]
        x_vars = []
        loc_vars = []
        aux_vars = []
        
        for k in range(self.n_steps+1):
            loc_k = []
            for l in range(len(self.locations)):
                var = PlanPRAiSE.LOC_NAME.format(k, l)
                loc_k.append(var)
                
            loc_vars.append(loc_k)
        
        for k in range(self.n_steps):
            x_vars.append(PlanPRAiSE.JOURNEY_NAME.format(k))
            prev = " + ".join(x_vars)
            tvar = "({} + {})".format(t_init, prev)
            t_vars.append(tvar)
            aux_k = []
            for p in range(len(self.partitions)-1):
                
                if self.use_aux_vars:
                    avar = PlanPRAiSE.AUX_NAME.format(p, k)
                else:
                    last = (p == len(self.partitions)-2)
                    partition = (self.partitions[p], self.partitions[p+1])
                    avar = IntoInterval(t_vars[k], partition, last)

                aux_k.append(avar)
                
            aux_vars.append(aux_k)

        return t_vars, x_vars, loc_vars, aux_vars
        
    def arriving_before(self, time):
        return LE(self.time_vars[-1], Real(time))

    @staticmethod
    def _poly_weight(variable, coefficients):
        monomials = []
        max_degree = len(coefficients)-1

        for i, coefficient in enumerate(coefficients):
            exponent = max_degree-i
            if exponent > 0 :                
                monomial = Times([Real(coefficient),
                                  Pow(variable, Real(exponent))])
            else:
                monomial = Real(coefficient)

            monomials.append(monomial)
        return Plus(monomials)
