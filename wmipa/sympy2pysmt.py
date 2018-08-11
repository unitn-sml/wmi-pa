"""This module leverages sympy to transform a pysmt polynomial in canonical
form.

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'


from sympy import expand #, is_Add, is_Mul, is_Pow, is_Symbol, is_Number
from pysmt.shortcuts import Plus, Times, Pow, Symbol, Real, serialize
from pysmt.typing import REAL

from wmipa.wmiexception import WMIParsingError

def pysmt2sympy(formula):
    return serialize(formula)


def sympy2pysmt(expression):
    """Converts a sympy formula representing a polynomial into a  pysmt formula.
    
    Keyword arguments:
    expression -- sympy formula.

    Raises:
    WMIParsingError -- If it fails to parse the formula.

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
        msg = "Couldn't parse the sympy formula: " + str(expression)
        raise WMIParsingError(msg, None)

def get_canonical_form(expression):
    """Given a pysmt formula representing a polynomial, rewrites it in canonical
    form.

    Keyword arguments:
    expression - pysmt formula

    Raises:
    WMIParsingError -- If it fails to parse back the formula after converting it

    """
    canonical = sympy2pysmt(expand(pysmt2sympy(expression)))
    return canonical
