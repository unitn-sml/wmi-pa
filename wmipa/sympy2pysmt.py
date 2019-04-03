"""This module leverages sympy to transform a pysmt polynomial in canonical form.

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'


from sympy import expand, sympify, SympifyError
from pysmt.shortcuts import Plus, Times, Pow, Symbol, Real, serialize
from pysmt.typing import REAL

from wmipa.wmiexception import WMIParsingException

def pysmt2sympy(expression):
    """Converts a pysmt formula representing a polynomial into a string.
        The string can then be read and modified by sympy.
    
    Args:
        formula (FNode): The pysmt formula to convert.
    
    Returns:
        str: The string representing the formula.
        
    Raises:
        WMIParsingException: If the method fails to parse the formula.
        
    """
    serialize_formula = serialize(expression)
    try:
        sympy_formula = sympify(serialize_formula)
    except SympifyError:
        raise WMIParsingException(WMIParsingException.CANNOT_CONVERT_PYSMT_FORMULA_TO_SYMPY, expression)
    return sympy_formula

def sympy2pysmt(expression):
    """Converts a sympy formula representing a polynomial into a pysmt formula.
    
    Args:
        expression: The sympy formula to convert.
        
    Returns:
        FNode: The pysmt formula.

    Raises:
        WMIParsingException: If the method fails to parse the formula.
        
    """
    if expression.is_Add:
        return Plus(map(sympy2pysmt, expression.args))
    elif expression.is_Mul:
        return Times(map(sympy2pysmt, expression.args))
    elif expression.is_Pow:
        base, exp = expression.args
        return Pow(sympy2pysmt(base), sympy2pysmt(exp))
    elif expression.is_Symbol:
        return Symbol(str(expression), REAL)
    elif expression.is_Number:
        return Real(float(expression))
    else:
        raise WMIParsingException(WMIParsingException.CANNOT_CONVERT_SYMPY_FORMULA_TO_PYSMT, expression)

def get_canonical_form(expression):
    """Given a pysmt formula representing a polynomial, rewrites it in canonical form.

    Args:
        expression (FNode): The pysmt formula to rewrite.
        
    Returns:
        (FNode): The pysmt formula in canonical form.
        
    Raises:
        WMIParsingException: If the method fails to parse the formula.
        
    """
    sympy_formula = pysmt2sympy(expression)
    sympy_expand = expand(sympy_formula)
    canonical = sympy2pysmt(sympy_expand)
    return canonical
