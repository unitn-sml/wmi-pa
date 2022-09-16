"""This module implements the utility classes used to convert LRA expressions,
such as linear inequalities and polynomial weight functions, into a format that
is more suitable to be processed by LattE Integrale.

"""

__version__ = "0.99"
__author__ = "Paolo Morettin"

from pysmt.shortcuts import LT, And, Bool, Plus, Real, Symbol, Times
from pysmt.typing import REAL

from wmipa.integration.polynomial import Polynomial
from wmipa.utils import lcmm
from wmipa.wmiexception import WMIParsingException


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
            aliases (dict {FNode : FNode}): The dictionary containing the aliases
                definitions.

        Raises:
            WMIParsingException: If the expression is not an inequality or the
                polynomial has degree more than 1.

        """
        if not (expression.is_le() or expression.is_lt()):
            raise WMIParsingException(WMIParsingException.NOT_AN_INEQUALITY, expression)
        left, right = expression.args()
        if right.is_real_constant():
            # Polynomial OP Constant
            self._parse_expression(left, right, False, aliases)
        elif left.is_real_constant():
            # Constant OP Polynomial
            self._parse_expression(right, left, True, aliases)
        else:
            # Polynomial1 OP Polynomial2  converted into  Polynomial1 - Polynomial2 OP 0
            self._parse_expression(
                Plus(left, Times(Real(-1), right)), Real(0), False, aliases
            )

    def _parse_expression(self, polynomial, constant, negate, aliases):
        """Parse the expression representing the inequality.

        Args:
            polynomial (FNode): The pysmt formula representing the polynomial part.
            constant (FNode): The pysmt formula representing the constant part.
            negate (bool): If True the inequality will be flipped.
            aliases (dict {FNode : FNode}): The dictionary containing the aliases
                definitions.

        Raises:
            WMIParsingException: If the polynomial has degree more than 1.

        """
        assert constant.is_real_constant(), "Not a Real instance: " + str(constant)
        b = constant.constant_value()
        poly = Polynomial(polynomial, aliases)

        if negate:
            poly.negate()
            b = -b

        if poly.degree() > 1:
            raise WMIParsingException(
                WMIParsingException.POLYNOMIAL_WITH_DEGREE_GREATER_THAN_ONE, poly
            )

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
            denominators = [m.coefficient.denominator for m in poly.monomials] + [
                b.denominator
            ]
            lcd = lcmm(denominators)
            for monomial in poly.monomials:
                assert (
                        len(monomial.exponents) == 1
                        and list(monomial.exponents.values())[0] == 1
                ), "Not a monomial of degree 1"
                name = list(monomial.exponents.keys())[0]
                assert name not in self.coefficients, "Polynomial not in canonical form"
                self.coefficients[name] = int(monomial.coefficient * lcd)
            self.constant = int(b * lcd)
        else:
            pass
            # self.constant = Minus(Real(b), polynomial)

    def __str__(self):
        """The str method.

        Returns:
            str: The string representation of the inequality (e.g: (3x) + (-2y) < 7).

        """
        if len(self.coefficients) > 0:
            polynomial = " + ".join(
                ["(" + str(c) + " * " + x + ")" for x, c in self.coefficients.items()]
            )
            return polynomial + " < " + str(self.constant)
        else:
            return "0 < " + str(self.constant)

    def __eq__(self, other):
        if isinstance(other, Bound):
            return (
                    self.constant == other.constant
                    and self.coefficients == other.coefficients
            )
        return False

    def __hash__(self):
        return hash(self.constant)

    def to_pysmt(self):
        if not self.coefficients:
            return Bool(True)
        polynomial = Plus(
            *(Times(Real(c), Symbol(x, REAL)) for x, c in self.coefficients.items()),
        )
        return LT(polynomial, Real(self.constant))


class Polytope:
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
            expressions (list(FNode)): The list of pysmt formulas representing the
                inequalities.
            aliases (dict {FNode : FNode}): The dictionary containing the aliases
                definitions.

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
            str: The string representation of the polytope
                (e.g: [(3x) + (-2y) < 7], [(5z < 10]).

        """
        bounds = ["[" + str(b) + "]" for b in self.bounds]
        return ", ".join(bounds)

    def is_empty(self):
        for i1 in range(len(self.bounds) - 1):
            for i2 in range(i1, len(self.bounds)):
                if self.bounds[i1].constant == -self.bounds[i2].constant:
                    coeff1 = self.bounds[i1].coefficients
                    coeff2 = self.bounds[i2].coefficients
                    if coeff1.keys() == coeff2.keys():
                        if all(coeff1[v] == -coeff2[v] for v in coeff1.keys()):
                            return True

        return False

    def to_pysmt(self):
        if not self.bounds:
            return Bool(True)
        return And(*map(lambda x: x.to_pysmt(), self.bounds))
