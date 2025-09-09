from fractions import Fraction
from functools import reduce
from typing import Any, Callable, Collection, SupportsInt

import numpy as np
from pysmt.environment import Environment
from pysmt.fnode import FNode
from pysmt.typing import REAL
from pysmt.walkers import DagWalker

Monomials = dict[tuple[int, ...], float]  # Maps exponent tuples to coefficients


class Polynomial:
    """Internal class representing canonical polynomials.
    Implemented as a dict, having for each monomial: {key : coefficient}
    where key is a tuple encoding exponents of the ordered variables.

    E.g. {(2,0,1): 3} = "3 * x^2 * y^0 * z^1"

    Attributes:
        monomials: the monomial dictionary
        variables: the continuous integration domain
        ordered_keys: sorted list of monomial keys
        mgr: the pysmt formula manager
    """

    def __init__(self, expr: FNode, variables: Collection[FNode], env: Environment):
        """Default constructor.

        Args:
            expr: the polynomial in pysmt format
            variables: the continuous integration domain
            env: the pysmt environment
        """
        self.monomials = PolynomialParser(variables).parse(expr)
        const_key = tuple(0 for _ in range(len(variables)))
        if const_key in self.monomials and self.monomials[const_key] == 0:
            self.monomials.pop(const_key)
        self.variables = variables
        self.ordered_keys = sorted(self.monomials.keys())
        self.mgr = env.formula_manager

    @property
    def degree(self) -> int:
        """Returns the degree of the polynomial."""
        if len(self.monomials) == 0:
            return 0
        else:
            return max(sum(exponents) for exponents in self.monomials)

    def to_numpy(self) -> Callable[[np.ndarray], np.ndarray]:
        """Returns the polynomial as a callable function.

        This function can be used to evaluate a numpy array.
        """
        return lambda x: np.sum(
            np.array(
                [k * np.prod(np.pow(x, e), axis=1) for e, k in self.monomials.items()]
            ).T,
            axis=1,
        )

    def to_pysmt(self) -> FNode:
        """Returns the polynomial in pysmt format."""
        if len(self.monomials) == 0:
            return self.mgr.Real(0)

        pysmt_monos = []
        for key in self.ordered_keys:
            factors = [self.mgr.Real(self.monomials[key])]
            for i, var in enumerate(self.variables):
                if key[i] > 1 or key[i] < 0:
                    factors.append(self.mgr.Pow(var, self.mgr.Real(key[i])))
                elif key[i] == 1:
                    factors.append(var)

            pysmt_monos.append(self.mgr.Times(*factors))

        return self.mgr.Plus(*pysmt_monos)

    def __len__(self) -> int:
        return len(self.monomials)

    def __str__(self) -> str:
        str_monos = []
        for key in self.ordered_keys:
            coeff = f"{self.monomials[key]}"

            term = "*".join(
                [
                    f"{var.symbol_name()}^{key[i]}"
                    # " * ".join([f"{var.symbol_name()}^{key[i]}"
                    for i, var in enumerate(self.variables)
                    if key[i] != 0
                ]
            )

            mono = f"{coeff}*{term}" if term else coeff
            str_monos.append(mono)

        return " + ".join(str_monos)


class PolynomialParser(DagWalker):
    """A walker to parse a polynomial expression (pysmt.FNode) into a dictionary of monomials."""

    def __init__(self, variables: Collection[FNode]):
        super().__init__()
        self.variables = variables

    def parse(self, expr: FNode) -> Monomials:
        return self.walk(expr)

    def walk_real_constant(self, formula: FNode, **kwargs: Any) -> Monomials:
        exp_key = tuple(0 for _ in range(len(self.variables)))
        coeff = formula.constant_value()
        return {exp_key: coeff}

    def walk_symbol(self, formula: FNode, **kwargs: Any) -> Monomials:
        assert formula.is_symbol(REAL)
        exp_key = tuple(0 if v != formula else 1 for v in self.variables)
        assert any(e != 0 for e in exp_key)
        coeff = 1
        return {exp_key: coeff}

    def walk_plus(
        self, formula: FNode, args: list[Monomials], **kwargs: Any
    ) -> Monomials:
        return reduce(self._sum_polys, args)

    def walk_minus(
        self, formula: FNode, args: list[Monomials], **kwargs: Any
    ) -> Monomials:
        mono_first, mono_second = args
        mono_second = {exp_key: -coeff for exp_key, coeff in mono_second.items()}
        return self.walk_plus(formula, [mono_first, mono_second])

    def walk_times(
        self, formula: FNode, args: list[Monomials], **kwargs: Any
    ) -> Monomials:
        return reduce(self._multiply_polys, args)

    def walk_pow(
        self, formula: FNode, args: list[Monomials], **kwargs: Any
    ) -> Monomials:
        base, exp = formula.args()
        if (
            not exp.is_constant(REAL)
            or not _is_integral(c := exp.constant_value())
            or c < 0
        ):
            raise ValueError(
                f"Exponent {exp} is not a non-negative integer constant in {formula.serialize()}"
            )
        exp_val = int(exp.constant_value())
        if base.is_symbol(REAL):
            exp_key = tuple(0 if v != base else exp_val for v in self.variables)
            return {exp_key: 1}
        else:
            base_poly = args[0]
            return self._expand_power(base_poly, exp_val)

    @staticmethod
    def _sum_polys(mono_first: Monomials, mono_second: Monomials) -> Monomials:
        """Sum two polynomials represented as monomial dictionaries."""
        result = mono_first.copy()
        for exp_key, coeff in mono_second.items():
            if exp_key not in result:
                result[exp_key] = coeff
            else:
                result[exp_key] += coeff
        return result

    @staticmethod
    def _multiply_polys(mono_first: Monomials, mono_second: Monomials) -> Monomials:
        """Multiplies two polynomials represented as monomial dictionaries."""
        result = {}
        n = (
            len(next(iter(mono_first.keys())))
            if mono_first
            else len(next(iter(mono_second.keys())))
        )

        for exp_key1, coeff1 in mono_first.items():
            for exp_key2, coeff2 in mono_second.items():
                exp_key_new = tuple(exp_key1[i] + exp_key2[i] for i in range(n))
                coeff_new = coeff1 * coeff2

                if exp_key_new not in result:
                    result[exp_key_new] = coeff_new
                else:
                    result[exp_key_new] += coeff_new

        return result

    @classmethod
    def _expand_power(cls, base_poly: Monomials, exp_val: int) -> Monomials:
        """Expands (polynomial)^n by repeated multiplication."""
        if exp_val == 0:
            n = len(next(iter(base_poly.keys())))
            return {tuple(0 for _ in range(n)): 1}

        result = base_poly.copy()
        for _ in range(exp_val - 1):
            result = cls._multiply_polys(result, base_poly)

        return result


def _is_integral(v: SupportsInt) -> bool:
    if isinstance(v, int):
        return True
    elif isinstance(v, float):
        return v.is_integer()
    elif isinstance(v, Fraction):
        return v.denominator == 1
    else:
        return False
