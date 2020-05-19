"""This module implements the utility classes used to convert LRA expressions,
such as linear inequalities and polynomial weight functions, into a format that
is more suitable to be processed by LattE Integrale.

"""

__version__ = '0.99'
__author__ = 'Paolo Morettin'

from fractions import Fraction
import networkx as nx
from pysmt.shortcuts import Plus, Minus, Real, Times, serialize
from wmipa.sympy2pysmt import get_canonical_form
from wmipa.utils import lcmm, is_pow
from wmipa.wmiexception import WMIParsingException

class Monomial:
    """Intermediate representation of a monomial.

    c * x_1^e_1 * ... * x_k^e_k

    Attributes:
        coefficient (Fraction): The coefficient of the monomial.
        exponents (dict {FNode : Fraction}): The dictionary containing the exponents {x_i : e_i}

    """
    
    def __init__(self, expression):
        """Default constructor. 

        Takes as input a pysmt formula representing a monomial.

        Args:
            expression (FNode): The pysmt formula representing a monomial.
        
        Raises:
            WMIParsingException: If the expression is not a monomial.

        """
        if not (expression.is_times() or expression.is_real_constant()
               or expression.is_symbol() or is_pow(expression)):
            raise WMIParsingException(WMIParsingException.NOT_A_MONOMIAL, expression)
        
        self.coefficient, self.exponents = self._parse_sub(expression)

    def __str__(self):
        """The str method.
        
        Returns:
            str: The string representation of the monomial (e.g: (-6 * x^3 * y^2) ).
        
        """
        powers = ["{}^{}".format(k, e) for k, e in self.exponents.items()]
        if (len(self.exponents)==0):
            return "(" + str(self.coefficient) +")"
        else:
            return "(" + str(self.coefficient)+" * " + " * ".join(powers) + ")"

    def degree(self):
        """Calculates the degree of the monomial.
        
        This method evaluates the degree by summing up all the values of the exponents.
        
        Returns:
            int: The degree of the monomial.
            
        """
        return sum(self.exponents.values())

    def multiply_by_monomial(self, monomial):
        """Multiplies this instance with another monomial.

        Args:
            monomial (FNode): The other monomial.

        """
        assert(isinstance(monomial, Monomial)), "Argument should be an instance of Monomial"
        
        # multiply the coefficients
        self.coefficient *= monomial.coefficient
        
        # update all the exponents
        for name, exp in monomial.exponents.items():
            if not name in self.exponents:
                self.exponents[name] = Fraction(0)
            self.exponents[name] += exp

    def negate(self):
        """Negates the monomial by changing the sign of the coefficient."""
        self.coefficient *= -1

    def _parse_sub(self, expression):
        """Parse an expression representing a monomial.
        
        Args:
            expression (FNode): The pysmt formula representing a monomial.
            
        Returns:
            Fraction: The coefficient of the expression.
            (dict {FNode : Fraction}): The dictionary containing the exponents.
            
        Raises:
            WMIParsingException: If the expression is not a monomial.
            
        """
        
        if expression.is_real_constant():
            return expression.constant_value(), {}
        elif expression.is_symbol():
            return Fraction(1), {expression.symbol_name():Fraction(1)}
        elif is_pow(expression):
            base, exp = expression.args()
            
            # Check that the exponent is constant
            if not exp.is_real_constant():
                raise WMIParsingException(WMIParsingException.NOT_A_MONOMIAL, expression)
            exp_value = exp.constant_value()

            # Parse the base
            base_value, base_var = self._parse_sub(base)
            
            ret_value = pow(base_value, exp_value)
            for x in base_var.keys():
                base_var[x] *= exp_value
            
            return ret_value, base_var
        elif expression.is_times():
            ret_value = Fraction(1)
            ret_var = {}
            
            # Parse all the terms of the multiplication
            for sub in expression.args():
                sub_value, sub_var = self._parse_sub(sub)
                ret_value *= sub_value
                
                for x, v in sub_var.items():
                    if x not in ret_var:
                        ret_var[x] = 0
                    ret_var[x] += v
            return ret_value, ret_var
        else:
            raise WMIParsingException(WMIParsingException.NOT_A_MONOMIAL, expression)


class Polynomial:
    """Intermediate representation of a polynomial.

    Attributes:
        monomials (Monomial): The list of Monomial instances.
        variables (set(FNode)): The set of all the variables of the polynomial.

    """
    
    def __init__(self, expression, aliases={}):
        """Default constructor.

        Takes as input a pysmt formula representing a polynomial and a dict of
        aliases to be substituted before the parsing.

        Args:
            expression (FNode): The pysmt formula representing the polynomial.
            aliases (dict {FNode : FNode}): The dict containing the aliases definitions.

        """
        # Perform aliases substitution and put in canonical form
        canonical = Polynomial._preprocess_formula(expression, aliases)
        
        # Process every monomial individually 
        self.monomials = []
        self.variables = set()
        if canonical.is_plus():
            for term in canonical.args():
                self._add_monomial(Monomial(term))
        else:
            self._add_monomial(Monomial(canonical))

    def __str__(self):
        """The str method.
                
        Returns:
            str: The string representation of the polynomial (e.g: (3 * x^5) + (-2 * y^3)).
        
        """
        return " + ".join(map(str, self.monomials))

    def degree(self):
        """Calculates the degree of the polynomial.
        
        This method evaluates the degree by taking the maximum degree of the monomials in it.
        
        Returns:
            int: The degree of the polynomial.
            
        """
        if len(self.monomials) > 0:
            return max([m.degree() for m in self.monomials])
        else:
            return 0

    def negate(self):
        """Negates the polinomial by negating all its monomials."""
        for monomial in self.monomials:
            monomial.negate()
            
    def _add_monomial(self, monomial):
        """Add a monomial to the polynomial.
        
        Args:
            monomial (Monomial): The monomial to be added.
        
        """
        assert(isinstance(monomial, Monomial)), "Argument should be an instance of Monomial"
        if monomial.coefficient != 0:
            self.monomials.append(monomial)
            self.variables = self.variables.union(
                set(monomial.exponents.keys()))

    @staticmethod
    def _preprocess_formula(expression, aliases):
        """Preprocesses a pysmt polynomial by substituting the aliases and
        rewriting it in canonical form.
        
        Args:
            expression (FNode): The pysmt formula representing a polynomial.
            aliases (dict {FNode : FNode}): The dict containing the aliases definitions.

        Returns:
            FNode: The pysmt formula in canonical form with all the aliases substituted.
            
        Raises:
            WMIParsingException: If in the aliases there is a cyclic assignment (e.g: x = y, y = x).
        """
        # Apply alias substitutions in the correct order
        if len(aliases) > 0:
            # Build a dependency graph of the substitutions and apply them in topological order
            Gsub = nx.DiGraph()
            constant_subs = {}
            
            # For every alias
            for x, alias_expr in aliases.items():
                for y in alias_expr.get_free_variables():
                    # Create a node from the alias to every symbol inside it
                    Gsub.add_edge(x, y)
                # If the alias substitution leads to a constant value (e.g: PI = 3.1415)
                if len(alias_expr.get_free_variables()) == 0:
                    constant_subs.update({x:alias_expr})
                    
            # Get the nodes in topological order
            try:
                sorted_substitutions = [node for node in nx.topological_sort(Gsub)
                                    if node in aliases]
            except nx.exception.NetworkXUnfeasible:
                raise WMIParsingException(WMIParsingException.CYCLIC_ASSIGNMENT_IN_ALIASES, aliases)
                
            # Apply all the substitutions
            for alias in sorted_substitutions:
                expression = expression.substitute({alias : aliases[alias]})
            expression = expression.substitute(constant_subs)
        
        return get_canonical_form(expression)


class Bound:
    """Intermediate representation of a linear inequality.
    
    The inequality is rescaled in order to have integer coefficients.

    (c_1 * x_1 + ... + c_k * x_k) OP real_const
        where OP = {<, <=, >, >=}.

    Attributes:
        constant (int): int(real_const * LCD).
        coefficients (dict): Dictionary {x_i : int(c_i * LCD)}.

    where LCD = LCM(denominators({c_1, ... , c_k, real_const})).
    
    """
    
    def __init__(self, expression, aliases={}):
        """Default constructor. 

        Takes as input a pysmt formula representing a linear inequality and
            a dictionary of aliases to be substituted before the parsing.
        
        Args:
            expression (FNode): The pysmt formula representing the inequality.
            aliases (dict {FNode : FNode}): The dictionary containing the aliases definitions.

        Raises:
            WMIParsingException: If the expression is not an inequality or the polynomial has degree more than 1.

        """
        if not (expression.is_le() or expression.is_lt()):
            raise WMIParsingException(WMIParsingException.NOT_AN_INEQUALITY, expression)
        left, right = expression.args()
        if right.is_real_constant():
            # Polynomial OP Constant
            self._parse_expression(left, right,  False, aliases)
        elif left.is_real_constant():
            # Constant OP Polynomial
            self._parse_expression(right, left, True, aliases)
        else:
            # Polynomial1 OP Polynomial2  converted into  Polynomial1 - Polynomial2 OP 0
            self._parse_expression(Plus(left,Times(Real(-1),right)),Real(0),
                                   False, aliases)

    def _parse_expression(self, polynomial, constant, negate, aliases):
        """Parse the expression representing the inequality.
        
        Args:
            polynomial (FNode): The pysmt formula representing the polynomial part.
            constant (FNode): The pysmt formula representing the constant part.
            negate (bool): If True the inequality will be flipped.
            aliases (dict {FNode : FNode}): The dictionary containing the aliases definitions.
            
        Raises:
            WMIParsingException: If the polynomial has degree more than 1.
            
        """
        assert(constant.is_real_constant()), "Not a Real instance: " + str(constant)
        b = constant.constant_value()
        poly = Polynomial(polynomial, aliases)
        
        if negate:
            poly.negate()
            b = -b
        
        if poly.degree() > 1:
            raise WMIParsingException(WMIParsingException.POLYNOMIAL_WITH_DEGREE_GREATER_THAN_ONE, poly)
        
        self.coefficients = {}
        self.constant = b
        if poly.degree() > 0:
            # After the alias substitutions, the polynomial may contain monomials of
            # degree 0, which must be moved to the constant part
            variable_monomials = []
            for monomial in poly.monomials:
                if monomial.degree() == 0:
                    b -= monomial.coefficient
                else:
                    variable_monomials.append(monomial)
            poly.monomials = variable_monomials
            
            # Convert the constants to integers (LattE requirement for the polytope)
            denominators = [m.coefficient.denominator
                            for m in poly.monomials] + [b.denominator]
            lcd = lcmm(denominators)
            for monomial in poly.monomials:
                assert(len(monomial.exponents) == 1
                       and list(monomial.exponents.values())[0] == 1),\
                    "Not a monomial of degree 1"
                name = list(monomial.exponents.keys())[0]
                assert(name not in self.coefficients),\
                    "Polynomial not in canonical form"
                self.coefficients[name] = int(monomial.coefficient * lcd)
            self.constant = int(b * lcd)
        else:
            pass
            #self.constant = Minus(Real(b), polynomial)
        
    def __str__(self):
        """The str method.
                
        Returns:
            str: The string representation of the inequality (e.g: (3x) + (-2y) < 7).
        
        """
        if (len(self.coefficients) > 0):
            polynomial = " + ".join(["("+str(c)+" * "+x+")" for x, c in self.coefficients.items()])
            return polynomial+" < "+str(self.constant)
        else:
            return "0 < "+str(self.constant)

class Polytope():
    """Intermediate representation of a polytope.

    Attributes:
        polytope (list(Bounds)): The list of all the inequalities in the polytope.
        variables (list): The list of the involved variables.

    """
    
    def __init__(self, expressions, aliases={}):
        """Default constructor. 

        Takes as input a list of pysmt formulas representing the linear
            inequalities that define the polytope.

        Args:
            expressions (list(FNode)): The list of pysmt formulas representing the inequalities.
            aliases (dict {FNode : FNode}): The dictionary containing the aliases definitions.

        Raises:
            WMIParsingException: If one of the expressions is not an inequality or 
                its polynomial has degree > 1.

        """
        self.bounds = []
        for expr in expressions:
            b = Bound(expr, aliases)
            # After performing the aliases substitutions, the polynomials may be
            # simplified and have degree 0
            # In this case, ignore the inequality.
            if b.coefficients != {}:
                self.bounds.append(b)

        self.variables = set()
        for bound in self.bounds:
            for name in bound.coefficients.keys():
                self.variables.add(name)

    def __str__(self):
        """The str method.
                
        Returns:
            str: The string representation of the polytope (e.g: [(3x) + (-2y) < 7], [(5z < 10]).
        
        """
        bounds = ["["+str(b)+"]" for b in self.bounds]
        return ", ".join(bounds)


    def is_empty(self):
        for i1 in range(len(self.bounds)-1):
            for i2 in range(i1, len(self.bounds)):
                if self.bounds[i1].constant == -self.bounds[i2].constant:
                    coeff1 = self.bounds[i1].coefficients
                    coeff2 = self.bounds[i2].coefficients
                    if (coeff1.keys() == coeff2.keys()):
                        if all(coeff1[v] == -coeff2[v] for v in coeff1.keys()):
                            return True

        return False
