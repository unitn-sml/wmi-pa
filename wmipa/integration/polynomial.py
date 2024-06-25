
from fractions import Fraction
from pysmt.shortcuts import Real, Times, Pow, Symbol, Plus
from pysmt.typing import REAL

from wmipa.integration.sympy2pysmt import get_canonical_form
from wmipa.utils import is_pow
from wmipa.wmiexception import WMIParsingException


class Monomial:
    """Intermediate representation of a monomial.

    c * x_1^e_1 * ... * x_k^e_k

    Attributes:
        coefficient (Fraction): The coefficient of the monomial.
        exponents (dict {FNode : Fraction}): The dictionary containing the
            exponents {x_i : e_i}

    """

    def __init__(self, expression):
        """Default constructor.

        Takes as input a pysmt formula representing a monomial.

        Args:
            expression (FNode): The pysmt formula representing a monomial.

        Raises:
            WMIParsingException: If the expression is not a monomial.

        """
        if not (
                expression.is_times()
                or expression.is_real_constant()
                or expression.is_symbol()
                or is_pow(expression)
        ):
            raise WMIParsingException(WMIParsingException.NOT_A_MONOMIAL, expression)

        self.coefficient, self.exponents = self._parse_sub(expression)

    def __str__(self):
        powers = ["{}^{}".format(k, e) for k, e in self.exponents.items()]
        if len(self.exponents) == 0:
            return "(" + str(self.coefficient) + ")"
        else:
            return "(" + str(self.coefficient) + " * " + " * ".join(powers) + ")"

    @property
    def degree(self):
        return sum(self.exponents.values())

    def multiply_by_monomial(self, monomial):
        """Multiplies this instance with another monomial.

        Args:
            monomial (FNode): The other monomial.

        """
        # multiply the coefficients
        self.coefficient *= monomial.coefficient

        # update all the exponents
        for name, exp in monomial.exponents.items():
            if name not in self.exponents:
                self.exponents[name] = Fraction(0)
            self.exponents[name] += exp

    def negate(self):
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
            return Fraction(1), {expression.symbol_name(): Fraction(1)}
        elif is_pow(expression):
            base, exp = expression.args()

            # Check that the exponent is constant
            if not exp.is_real_constant():
                raise WMIParsingException(
                    WMIParsingException.NOT_A_MONOMIAL, expression
                )
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

    def to_pysmt(self):
        if not self.exponents:
            return Real(self.coefficient)
        return Times(
            Real(self.coefficient),
            *map(
                lambda i: Pow(Symbol(i[0], REAL), Real(i[1])),
                self.exponents.items(),
            ),
        )


class Polynomial:
    """Intermediate representation of a polynomial.

    Attributes:
        monomials (Monomial): The list of Monomial instances.
        variables (set(FNode)): The set of all the variables of the polynomial.

    """

    def __init__(self, expression):
        """Default constructor.

        Args:
            expression (FNode): The pysmt formula representing the polynomial.

        """
        super().__init__()
        canonical = get_canonical_form(expression)
        
        # Process every monomial individually
        self.monomials = []
        if canonical.is_plus():
            for term in canonical.args():
                self._add_monomial(Monomial(term))
        else:
            self._add_monomial(Monomial(canonical))

    def __str__(self):
        return " + ".join(map(str, self.monomials))

    @property
    def degree(self):
        return max([m.degree for m in self.monomials]) if len(self.monomials) > 0 else 0

    def negate(self):
        """Negates the polynomial."""
        for monomial in self.monomials:
            monomial.negate()

    def _add_monomial(self, monomial):
        """Add a monomial to the polynomial.

        Args:
            monomial (Monomial): The monomial to be added.

        """
        if monomial.coefficient != 0:
            self.monomials.append(monomial)
            self.variables = self.variables.union(set(monomial.exponents.keys()))

    def to_pysmt(self):
        if not self.monomials:
            return Real(0)
        return Plus(*map(lambda x: x.to_pysmt(), self.monomials))

