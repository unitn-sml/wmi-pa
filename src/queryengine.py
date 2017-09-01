"""This module implements the class that leverages WMI to perform probabilistic
queries over an Hybrid Probabilistic Graphical Model.

"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from pysmt.shortcuts import And, Iff, Symbol, serialize
from pysmt.typing import BOOL, REAL

from logger import Loggable, init_root_logger
from weights import Weights
from wmi import WMI
from wmiexception import WMIRuntimeException
from utils import get_boolean_variables, get_real_variables, new_query_label,\
    contains_labels

class QueryEngine(Loggable):
    
    # default WMI algorithm
    DEF_MODE = WMI.MODE_PA

    MSG_NEGATIVE_RES = "WMI returned a negative result: {}"

    def __init__(self, support, weights):
        """Default constructor.

        Keyword arguments:
        support -- pysmt formula encoding the support
        weights -- pysmt formula encoding the FIUC weight function

        """
        self.init_sublogger(__name__)
        if contains_labels(support):
            msg = "The support contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        if contains_labels(weights):
            msg = "The weight function contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        self.support = support
        self.weights = Weights(weights)
        self.logger.debug("Support: {}".format(serialize(support)))
        self.logger.debug("Weights: {}".format(serialize(weights)))
        self.wmi = WMI()        

    def perform_query(self, query, evidence = None, mode = None):
        """Performs a query P(Q). Optional evidence can be specified, performing
        P(Q|E). Returns the probability of the query, calculated as:

            P(Q|E) = WMI(Q & E & kb) / WMI(E & kb)

        as well as the number of integrations performed.
        
        Keyword arguments:
        query -- pysmt formula encoding the query
        evidence -- pysmt formula encoding the evidence (optional, default: None)
        mode -- string in WMI.MODES to select the method (optional)

        """
        self.labels = set()
        mode = mode or QueryEngine.DEF_MODE
        msg = "Computing P(Q|E), Q: {},E: {}".format(serialize(query),
                                                      serialize(evidence)
                                                      if evidence != None
                                                      else "None")
        self.logger.debug(msg)
        if evidence:
            if contains_labels(evidence):
                msg = "The evidence contains variables with reserved names."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            bool_evidence = self._label_lra_atoms(evidence)
            f_e = And(self.support, bool_evidence)
        else:
            f_e = self.support

        if contains_labels(query):
            msg = "The query contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        bool_query = self._label_lra_atoms(query)
        f_e_q = And(f_e, bool_query)

        # extract the domain of integration according to the model,
        # query and evidence
        domX = get_real_variables(f_e_q)
        domA = get_boolean_variables(f_e_q) - self.labels
        self.logger.debug("domX: {}, domA: {}".format(domX, domA))

        # compute WMI(Q & E & kb)
        wmi_e_q, n_e_q = self.wmi.compute(f_e_q, self.weights, mode, domA, domX)
        if wmi_e_q > 0:
            # compute WMI(E & kb)
            wmi_e, n_e = self.wmi.compute(f_e, self.weights, mode, domA, domX)  
            if wmi_e == 0:
                msg = "(Knowledge base & Evidence) is inconsistent."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            elif wmi_e < 0:
                msg = self.MSG_NEGATIVE_RES.format(wmi_e_q)
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            
            normalized_p = wmi_e_q / wmi_e
            n_integrations = n_e_q + n_e
        elif wmi_e_q == 0:
            normalized_p = 0.0
            n_integrations = n_e_q

        else:
            msg = self.MSG_NEGATIVE_RES.format(wmi_e_q)
            self.logger.error(msg)
            raise WMIRuntimeException(msg)
            
        msg = "Norm. P(Q|E): {}, n_integrations: {}"
        self.logger.debug(msg.format(normalized_p, n_integrations))
        return normalized_p, n_integrations
    
    def _label_lra_atoms(self, formula):
        lra_atoms = [a for a in formula.get_atoms() if a.is_theory_relation()]
        labelling = []        
        for lra_atom in lra_atoms:
            q_var = new_query_label(len(self.labels))
            self.labels.add(q_var)
            labelling.append(Iff(q_var, lra_atom))
                             
        return And(formula, And(labelling))

if __name__ == "__main__":
    from pysmt.shortcuts import serialize, Or, Times, Ite, Real, LE
    from pysmt.typing import REAL
    import sys

    init_root_logger(verbose=True)

    a, b, c = Symbol("A"), Symbol("B"), Symbol("C")
    x = Symbol("x", REAL)
    formula = And(Or(a,b), LE(Real(0), x), LE(x, Real(1)))
    weights = Times(Ite(a, Real(0.5), Real(1)),
                    Ite(b, Real(3), Real(1)))

    query = c
    query = LE(x, Real(0.5))
    qe = QueryEngine(formula, weights)

    qe.perform_query(query, mode=WMI.MODE_PA)
    

"""
==================================================
Models for Samuel
==================================================

if __name__ == "__main__":
    from pysmt.shortcuts import serialize
    from randommodels import ModelGenerator

    mg = ModelGenerator(2, 2, 666)
    iterations = 100
    problems = [(mg.generate_support(2),
                 mg.generate_weights(2),
                 mg._random_formula(2)) for _ in xrange(iterations)]
    for i, problem in enumerate(problems):
        formula, weights, query = problem
        #print "support:",serialize(formula),"\n"
        #print "weights:",serialize(weights),"\n"
        #print "query:",serialize(query),"\n"        
        qe = QueryEngine(formula, weights)
        try:
            results = [(m,qe.perform_query([query], mode=m)) for m in WMI.MODES]
        except WMIRuntimeException as e:
            print e
            print
            continue
        print "Iteration",i
        print "\n".join(map(str, results))
        print
"""
