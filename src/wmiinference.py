"""This module leverages WMI to implement an inference engine that
allows queries of the form P(Q(x,A)|E(x,A)) over an hybrid model
expressed by a weight formula w(x,A) and support Chi(x,A). Q, E, w and
Chi are SMT-LRA formulas.

"""

__version__ = '0.999'
__author__ = 'Paolo Morettin'

from pysmt.shortcuts import And, Iff, Symbol, serialize
from pysmt.typing import BOOL, REAL

from logger import Loggable, init_root_logger
from weights import Weights
from wmi import WMI
from wmiexception import WMIRuntimeException
from utils import contains_labels, get_boolean_variables, \
    get_real_variables, is_label, new_query_label

class WMIInference(Loggable):   
    # default WMI algorithm
    DEF_MODE = WMI.MODE_PA

    MSG_NEGATIVE_RES = "WMI returned a negative result: {}"
    MSG_INCONSISTENT_SUPPORT = "The model is inconsistent"

    def __init__(self, support, weights, check_consistency=False):
        """Default constructor.

        Keyword arguments: 
        support -- pysmt formula encoding the
        support weights -- pysmt formula encoding the FIUC weight function
        check_consistency -- if True, raises a WMIRuntimeException if
            the model is inconsistent (default: False)

        """
        self.init_sublogger(__name__)

        # check if the support and weight function contain reserved names
        if contains_labels(support):
            msg = "The support contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        if contains_labels(weights):
            msg = "The weight function contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        # labelling the weight function conditions
        self.weights = Weights(weights)
        self.support = And(support, self.weights.labelling)

        self.logger.debug("Support: {}".format(serialize(support)))
        self.logger.debug("Weights: {}".format(serialize(weights)))

        # initialize the WMI engine
        self.wmi = WMI()

        # check support consistency if requested
        if check_consistency and not WMI.check_consistency(support):
            raise WMIRuntimeException(WMIInference.MSG_INCONSISTENT_SUPPORT)


    # common interface method to all inference engines
    def compute_normalized_probability(self, query, evidence=None):
        return self.perform_query(query, evidence)[0]

    
    def perform_query(self, query, evidence = None, mode = None,
                      non_negative=True):
        """Performs a query P(Q). Optional evidence can be specified, performing
        P(Q|E). Returns the probability of the query, calculated as:

            P(Q|E) = WMI(Q & E & kb) / WMI(E & kb)

        as well as the number of integrations performed.
        
        Keyword arguments:
        query -- pysmt formula encoding the query
        evidence -- pysmt formula encoding the evidence (default: None)
        mode -- string in WMI.MODES to select the method (optional)
        non_negative -- if True, negative WMI results raise an exception (default: True)
        """
        mode = mode or WMIInference.DEF_MODE
        evstr = (serialize(evidence) if evidence != None else "None")
        msg = "Computing P(Q|E), Q: {}, E: {}".format(serialize(query),evstr)
        self.logger.debug(msg)
        query_labels = set()
        
        if evidence:
            # check if evidence contains reserved variable names
            if contains_labels(evidence):
                msg = "The evidence contains variables with reserved names."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            
            # label LRA-atoms in the evidence
            bool_evidence = WMIInference._query_labelling(evidence, query_labels)
            f_e = And(self.support, bool_evidence)
        else:
            f_e = self.support

        if contains_labels(query):
            msg = "The query contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        # label LRA-atoms in the query
        bool_query = WMIInference._query_labelling(query, query_labels)
        f_e_q = And(f_e, bool_query)

        # extract the domain of integration according to the model,
        # query and evidence
        domX = set(get_real_variables(f_e_q))
        domA = {x for x in get_boolean_variables(f_e_q) if not is_label(x)}
        self.logger.debug("domX: {}, domA: {}".format(domX, domA))

        # compute WMI(Q & E & kb)
        wmi_e_q, n_e_q = self.wmi.compute(f_e_q, self.weights, mode, domA, domX)
        if wmi_e_q > 0 or (wmi_e_q < 0 and not non_negative):
            # compute WMI(E & kb)
            wmi_e, n_e = self.wmi.compute(f_e, self.weights, mode, domA, domX)  
            if wmi_e == 0:
                msg = "(Knowledge base & Evidence) is inconsistent."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            elif wmi_e < 0 and non_negative:
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

    def enumerate_TTAs(self, query, evidence = None):
        """Enumerates the total truth assignments computed for the given query.
        
        Keyword arguments:
        query -- pysmt formula encoding the query
        evidence -- pysmt formula encoding the evidence (optional, default: None)

        """
        msg = "Enumerating TTAs for P(Q|E), Q: {},E: {}".format(serialize(query),
                                                        serialize(evidence)
                                                        if evidence != None
                                                        else "None")
        self.logger.debug(msg)
        query_labels = set()

        if evidence:
            if contains_labels(evidence):
                msg = "The evidence contains variables with reserved names."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)

            # label LRA-atoms in the evidence
            bool_evidence = WMIInference._query_labelling(evidence, query_labels)
            f_e = And(self.support, bool_evidence)
        else:
            f_e = self.support

        if contains_labels(query):
            msg = "The query contains variables with reserved names."
            self.logger.error(msg)
            raise WMIRuntimeException(msg)

        # label LRA-atoms in the query
        bool_query = WMIInference._query_labelling(query, query_labels)
        f_e_q = And(f_e, bool_query)

        # extract the domain of integration according to the model,
        # query and evidence
        domX = set(get_real_variables(f_e_q))
        domA = {x for x in get_boolean_variables(f_e_q) if not is_label(x)}

        n_ttas_e_q = self.wmi.enumerate_TTAs(f_e_q, self.weights, domA, domX)
        if n_ttas_e_q > 0:
            n_ttas_e = self.wmi.enumerate_TTAs(f_e, self.weights, domA, domX)  
            if n_ttas_e == 0:
                msg = "(Knowledge base & Evidence) is inconsistent."
                self.logger.error(msg)
                raise WMIRuntimeException(msg)
            
            return n_ttas_e_q + n_ttas_e
        else:
            return 0

    @staticmethod
    def _query_labelling(formula, query_labels):
        lra_atoms = [a for a in formula.get_atoms() if a.is_theory_relation()]
        labelling = []
        for lra_atom in lra_atoms:
            q_var = new_query_label(len(query_labels))
            query_labels.add(q_var)
            labelling.append(Iff(q_var, lra_atom))
                             
        return And(formula, And(labelling))


if __name__ == "__main__":
    from pysmt.shortcuts import Symbol, Ite, And, LE, LT, Real, Times, serialize
    from pysmt.typing import REAL

    init_root_logger("cane.log",True)

    def compute_print(method, query, evidence):
        print "query: ", serialize(query)
        print "evidence: ", serialize(evidence) if evidence else "-"
        prob = method.compute_normalized_probability(query, evidence)
        print "normalized: ", prob
        print "--------------------------------------------------"

    x = Symbol("x", REAL)
    A = Symbol("A")
    B = Symbol("B")    
    support = And(LE(Real(-1), x), LE(x, Real(1)))
    weights = Ite(LT(Real(0), x),
                  Ite(A, Times(Real(2), x), x),
                  Ite(A, Times(Real(-2), x), Times(Real(-1),x)))

    wmi = WMIInference(support, weights)
    print "support: ", serialize(support)
    print "weights: ", serialize(weights)
    print "=================================================="

    suite = [#(A, None),
        (B, None),
             (And(A, LE(Real(0), x)), None),
             (LE(Real(0), x), A)]

    for query, evidence in suite:
        compute_print(wmi, query, evidence)

    
