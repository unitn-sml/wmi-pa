"""This module implements the utility classes used to convert LRA expressions
such as linear inequalities and polynomial weight functions into a format that
is more suitable to be processed by LattE Integrale.

Credits: least common multiple code by J.F. Sebastian
(http://stackoverflow.com/a/147539)

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from fractions import Fraction
import networkx as nx
from pysmt.operators import POW
from pysmt.shortcuts import Plus, Real, Times, serialize
from wmipa.sympy2pysmt import get_canonical_form
from wmipa.utils import lcmm
from wmipa.wmiexception import WMIParsingError, WMIRuntimeException

# utility unbound methods
def is_pow(expression):
    """Test whether the node is the Pow operator.
    This should be implemented in pysmt but is currently missing.

    """
    return expression.node_type() == POW            
    

class Polynomial:
    """Intermediate representation of a polynomial.

    Attributes:
    monomials -- list of Monomial instances.

    """
    def __init__(self, expression, aliases):
        """Default constructor.

        Takes as input a pysmt formula representing a polynomial and a dict of
        aliases to be substituted before the parsing.

        Keyword arguments:
        expression -- pysmt formula
        aliases -- dict containing the aliases definitions.

        """
        # perform aliases substitution and put in canonical form
        canonical = Polynomial._preprocess_formula(expression, aliases)
        self.monomials = []
        self.variables = set()
        if canonical.is_plus():
            for term in canonical.args():
                self._add_monomial(Monomial(term))
        else:
            self._add_monomial(Monomial(canonical))

    def __str__(self):
        return " + ".join(map(str, self.monomials))

    def constant_value(self):
        """If the polynomial has degree zero, returns its (constant) value as a
        Fraction, otherwise returns None.

        """
        constant = Fraction(1)
        for monomial in self.monomials:
            if monomial.degree() != 0:
                return None
            constant *= monomial.coefficient

        return constant

    def degree(self):
        """Returns the degree of the polynomial."""
        if len(self.monomials) > 0:
            return max([m.degree() for m in self.monomials])
        else:
            return 0

    def negate(self):
        """Negates the polinomial by negating all its monomials."""
        for monomial in self.monomials:
            monomial.negate()

            
    def _add_monomial(self, monomial):
        assert(isinstance(monomial, Monomial)),\
            "Argument should be an instance of Monomial"
        if monomial.coefficient != 0:
            self.monomials.append(monomial)
            self.variables = self.variables.union(
                set(monomial.exponents.keys()))

    @staticmethod
    def _preprocess_formula(expression, aliases):
        """Preprocesses a pysmt polynomial by substituting the aliases and
        rewriting it in canonical form.

        """
        # apply alias substitutions in the correct order
        if len(aliases) > 0:
            # build a dependency graph of the substitutions and apply them in
            # topological order
            Gsub = nx.DiGraph()
            for x, alias_expr in aliases.items():
                for y in alias_expr.get_free_variables():
                    Gsub.add_edge(x, y)           
            sorted_substitutions = [node for node in nx.topological_sort(Gsub)
                                    if node in aliases]
            for alias in sorted_substitutions:
                expression = expression.substitute({alias : aliases[alias]})

        return get_canonical_form(expression)

class Monomial:
    """Intermediate representation of a monomial.

    c * x_1^e_1 * ... * x_k^e_k

    Attributes:
    coefficient -- Fraction(c)
    exponents -- dict containing the exponents {x_i : Fraction(e_i)}

    """
    PARSING_ERROR_MSG = "Not a monomial."
    
    def __init__(self, expression):
        """Default constructor. 

        Takes as input a pysmt formula representing a monomial.

        Raises:
        WMIParsingError -- If expression is not a polynomial.

        Keyword arguments:
        expression -- a pysmt formula

        """
        if not (expression.is_times() or expression.is_real_constant()
               or expression.is_symbol() or is_pow(expression)):
            raise WMIParsingError(Monomial.PARSING_ERROR_MSG, expression)
        
        self.coefficient = Fraction(1)
        self.exponents = {}
        try:
            if expression.is_times():
                for sub in expression.args():
                    self._parse_sub(sub)
            else:
                self._parse_sub(expression)
        except WMIParsingError as e:
            raise WMIParsingError(Monomial.PARSING_ERROR_MSG, expression)

    def __str__(self):
        powers = ["{}^{}".format(k, e) for k, e in self.exponents.items()]
        return "(" + str(self.coefficient) + " " + " ".join(powers) + ")"

    def degree(self):
        """Returns the degree of the monomial."""
        return sum(self.exponents.values())

    def multiply_by_monomial(self, monomial):
        """Multiplies this instance with another monomial.

        Keyword arguments:
        monomial -- The other monomial.

        """
        assert(isinstance(monomial, Monomial)),\
            "Argument should be an instance of Monomial"
        self.coefficient *= monomial.coefficient
        for name, exp in monomial.exponents.items():
            self._update_exponent(name,exp)

    def negate(self):
        """Negates the monomial by changing the sign of the coefficient."""
        self.coefficient *= -1

    def _parse_sub(self, expression):
        if expression.is_real_constant():
            self.coefficient = self.coefficient * expression.constant_value()
        elif expression.is_symbol():
            self._update_exponent(expression.symbol_name(), Fraction(1))
        elif is_pow(expression):
            var, exp = expression.args()
            if not var.is_symbol() or not exp.is_real_constant():
                raise WMIParsingError(Monomial.PARSING_ERROR_MSG, None)
                
            self._update_exponent(var.symbol_name(), exp.constant_value())

    def _update_exponent(self, name, exponent):
        assert(isinstance(name, str) and isinstance(exponent, Fraction)),\
            "Arguments should be of type (str, Fraction)"
        if not name in self.exponents:
            self.exponents[name] = Fraction(0)
        self.exponents[name] += exponent

class Bound:
    """Intermediate representation of a linear inequality.
    Rescale it in order to have integer coefficients.

    (c_1 * x_1 + ... + c_k * x_k) OP real_const

    where OP = {<, <=, >, >=}

    Attributes:
    constant -- int(real_const * LCD)
    coefficients -- Dictionary {x_i : int(c_i * LCD)}

    where LCD = LCM(denominators({c_1, ... , c_k, real_const}))
    
    """
    def __init__(self, expression, aliases):
        """Default constructor. 

        Takes as input a pysmt formula representing a linear inequality and
        a dictionary of aliases to be substituted before the parsing.

        Raises:
        WMIParsingError -- If the expression is not an inequality or 
                           the polynomial has degree > 1
        WMIRuntimeException -- If the polynomial has degree 0.


        Keyword arguments:
        expression -- pysmt formula
        aliases -- dict containing the aliases definitions.

        """
        if not (expression.is_le() or expression.is_lt()):
            raise WMIParsingError("Not an inequality", expression)
        left, right = expression.args()
        if right.is_real_constant():
            self._parse_expression(left, right,  False, aliases)
        elif left.is_real_constant():
            self._parse_expression(right, left, True, aliases)
        else:
            self._parse_expression(Plus(left,Times(Real(-1),right)),Real(0),
                                   False, aliases)

    def _parse_expression(self, polynomial, constant, negate, aliases):
        assert(constant.is_real_constant()),\
            "Not a Real instance: " + str(constant)
        b = constant.constant_value()
        poly = Polynomial(polynomial, aliases)

        if negate:
            poly.negate()
            b = -b
                
        if poly.degree() > 1:
            raise WMIParsingError("Polynomial of degree > 1", poly)
        elif poly.degree() == 0:
            raise WMIRuntimeException("Polynomial of degree = 0")

        # after the alias substitutions, the polynomial may contain monomials of
        # degree 0, which must be moved to the constant part
        variable_monomials = []
        for monomial in poly.monomials:
            if monomial.degree() == 0:
                b -= monomial.coefficient
            else:
                variable_monomials.append(monomial)
        poly.monomials = variable_monomials

        
        # convert the constants to integers (LattE requirement for the polytope)
        denominators = [m.coefficient.denominator
                        for m in poly.monomials] + [b.denominator]
        lcd = lcmm(denominators)
        self.coefficients = {}
        for monomial in poly.monomials:
            assert(len(monomial.exponents) == 1
                   and list(monomial.exponents.values())[0] == 1),\
                "Not a monomial of degree 1"
            name = list(monomial.exponents.keys())[0]
            assert(name not in self.coefficients),\
                "Polynomial not in canonical form"
            self.coefficients[name] = int(monomial.coefficient * lcd)
        self.constant = int(b *lcd)
        

class Polytope(list):
    """Intermediate representation of a polytope.

    Attributes:
    polytope -- list of Bounds
    variables -- list of involved variables

    """
    def __init__(self, expressions, aliases):
        """Default constructor. 

        Takes as input a list of pysmt formulas representing the linear
        inequalities that define the polytope.

        Keyword arguments:
        expressions -- list of pysmt formulas
        aliases -- dict containing the aliases definitions.

        Raises:
        WMIParsingError -- If one of the expressions is not an inequality or 
                           its  polynomial has degree > 1

        """                    
        self.polytope = []
        for expr in expressions:
            # After performing the aliases substitutions, the polynomials may be
            # simplified and have degree 0, raising a WMIRuntimeException.
            # In this case, ignore the inequality.
            try:
                self.polytope.append(Bound(expr, aliases))
            except WMIRuntimeException:
                continue

        self.variables = set()
        for bound in self.polytope:
            for name in bound.coefficients.keys():
                self.variables.add(name)



