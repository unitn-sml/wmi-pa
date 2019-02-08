
from functools import reduce

from pysmt.shortcuts import Symbol
from pysmt.typing import BOOL, REAL


COND_PREFIX = "__cond_"
QUERY_PREFIX = "__query_"
WMI_PREFIX = "__wmi_"

PREFIXES = [COND_PREFIX, QUERY_PREFIX, WMI_PREFIX]

def new_cond_label(index):
    """Returns a condition label."""
    return _new_label(COND_PREFIX, index)

def new_query_label(index):
    """Returns a query label."""    
    return _new_label(QUERY_PREFIX, index)

def new_wmi_label(index):
    """Returns a generic WMI label."""
    return _new_label(WMI_PREFIX, index)

def is_cond_label(variable):
    """Returns True if the variable is a condition label, False otherwise."""    
    return variable.symbol_name().startswith(COND_PREFIX)

def is_query_label(variable):
    """Returns True if the variable is a query label, False otherwise."""    
    return variable.symbol_name().startswith(QUERY_PREFIX)

def is_wmi_label(variable):
    """Returns True if the variable is a WMI label, False otherwise."""
    return variable.symbol_name().startswith(WMI_PREFIX)

def is_label(variable):
    for prefix in PREFIXES:
        if variable.symbol_name().startswith(prefix):
            return True
    return False

def contains_labels(formula):
    """Returns True if the formula contains variables with reserved names,
    False otherwise.

    """    
    for var in get_boolean_variables(formula):
        if is_label(var):
            return True
    return False

def get_boolean_variables(formula):
    """Returns the list of Boolean variables in the formula."""
    return _get_variables(formula, BOOL)

def get_real_variables(formula):
    """Returns the list of real variables in the formula."""    
    return _get_variables(formula, REAL)

def get_lra_atoms(formula):
    """Returns the list of LRA atoms in the formula."""    
    return {a for a in formula.get_atoms() if a.is_theory_relation()}
    

def _get_variables(formula, type_):
    return {a for a in formula.get_free_variables() if a.get_type() == type_}

def _new_label(prefix, index):
    label_name = "{}_{}".format(prefix, index)
    return Symbol(label_name)

def _gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:      
        a, b = b, a % b
    return a

def _lcm(a, b):
    """Return lowest common multiple."""
    return a * b // _gcd(a, b)

def lcmm(args):
    """Return lcm of args."""   
    return reduce(_lcm, args)

