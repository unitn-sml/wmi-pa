"""This module implements some usefull methods used throughout the code.

Credits: least common multiple code by J.F. Sebastian
    (http://stackoverflow.com/a/147539)

"""

from functools import reduce

from pysmt.typing import BOOL, REAL
from pysmt.operators import POW


def get_boolean_variables(formula):
    """Finds all the boolean variables in the formula.
    
    Args:
        formula (FNode): The pysmt formula to examine.
        
    Returns:
        set(FNode): The set of all the boolean variables in the formula.
    
    """
    return _get_variables(formula, BOOL)

def get_real_variables(formula):
    """Finds all the real variables in the formula.
    
    Args:
        formula (FNode): The pysmt formula to examine.
        
    Returns:
        set(FNode): The set of all the real variables in the formula.
    
    """
    return _get_variables(formula, REAL)

def get_lra_atoms(formula):
    """Finds all the LRA atoms in the formula.
    
    Args:
        formula (FNode): The pysmt formula to examine.
        
    Returns:
        set(FNode): The set of all the LRA atoms in the formula.
    
    """  
    return {a for a in formula.get_atoms() if a.is_theory_relation()}

def _get_variables(formula, type_):
    """Finds all the variables in the formula of the specific pysmt type.
    
    Args:
        formula (FNode): The pysmt formula to examine.
        type_: The pysmt type to find (e.g: REAL, BOOL).
        
    Returns:
        set(FNode): The set of all the variables in the formula of the specific type.
        
    """
    return {a for a in formula.get_free_variables() if a.get_type() == type_}
    
def is_pow(node):
    """Test whether the node is the Pow operator
        (this should be implemented in pysmt but is currently missing).
    
    Args:
        node (FNode): The node to examine.
        
    Returns:
        bool: True if the node is a Pow operator, False otherwise.

    """
    return node.node_type() == POW 

def _gcd(a, b):
    """Computes the greatest common divisor of two numbers using Euclid's Algorithm.
    
    Example:
        >>> _gcd(30, 18)
        6
    
    Args:
        a (int): The first parameter.
        b (int): The second parameter.
        
    Returns:
        int: The greatest common divisor of a and b.
        
    """
    while b:      
        a, b = b, a % b
    return a

def _lcm(a, b):
    """Compute the lowest common multiple of two numbers.
    
    Example:
        >>> _lcm(12, 20)
        60
        
    Args:
        a (int): The first parameter.
        b (int): The second parameter.
        
    Returns:
        int: The lowest common multiple of a and b.
        
    """
    return a * b // _gcd(a, b)

def lcmm(args):
    """Computes the lowest common multiple of a list of numbers.
    
    Example:
        >>> lcmm([5, 15, 12])
        60
        
    Args:
        args (list(int)): The list of numbers on which to compute the lowest common multiple.
        
    Returns:
        int: The lowest common multiple of all the numbers in the list.
        
    """
    return reduce(_lcm, args)
