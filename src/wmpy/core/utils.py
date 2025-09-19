"""This module implements some useful methods used throughout the code."""

from collections import defaultdict
from typing import Any

from pysmt import operators as op
from pysmt.environment import Environment
from pysmt.fnode import FNode
from pysmt.simplifier import Simplifier
from pysmt.typing import BOOL
from pysmt.walkers import handles


def is_atom(node: FNode) -> bool:
    """Returns true iff node is a propositional or theory atom."""
    return node.is_symbol(BOOL) or node.is_theory_relation()


def is_literal(node: FNode) -> bool:
    """Returns true iff node is an atom or its negation."""
    return is_atom(node) or (node.is_not() and is_atom(node.arg(0)))


def is_clause(formula: FNode) -> bool:
    """Returns true iff formula is a disjuction of literals."""
    return is_literal(formula) or (
        formula.is_or() and all(is_literal(lit) for lit in formula.args())
    )


def is_cnf(formula: FNode) -> bool:
    """Returns true iff formula is in Conjunctive Normal Form."""
    return is_clause(formula) or (
        formula.is_and() and all(is_clause(c) for c in formula.args())
    )


class LiteralNormalizer:
    """A helper class for normalizing literals. This class is useful
    whenever literals involving algebraic atoms are manipulated by an
    external procedure, such as an SMT-based enumerator.
    """

    def __init__(self, env: Environment):
        self._solver = env.factory.Solver(name="msat")
        self._cache: dict[FNode, FNode] = {}  # literal -> normalized literal
        self._known_aliases: dict[FNode, set[tuple[FNode, bool]]] = defaultdict(
            set
        )  # literal -> literals normalized into it in the form (atom, negated)

    def __del__(self) -> None:
        self._solver.exit()

    def _normalize(self, literal: FNode) -> FNode:
        if literal not in self._cache:
            converter = self._solver.converter
            normalized_literal = converter.back(converter.convert(literal))
            self._cache[literal] = normalized_literal
        return self._cache[literal]

    def normalize(self, literal: FNode, remember_alias: bool = False) -> tuple[FNode, bool]:
        """Normalizes 'literal', possibly storing original formula in the alias dictionary.

        Args:
            literal: the literal in pysmt format
            remember_alias: store 'literal' as an alias (def: False)

        Returns:
            A normalized atom plus a Boolean that indicates if the normalized literal was negative.
        """
        normalized_literal = self._normalize(literal)
        negative = False
        if normalized_literal.is_not():
            normalized_literal = normalized_literal.arg(0)
            negative = True
        if remember_alias:
            self._known_aliases[normalized_literal].add((literal, negative))
        return normalized_literal, negative

    def known_aliases(self, literal: FNode) -> set[tuple[FNode, bool]]:
        """Maps back a normalized atom into the original ones (multiple literals might map into the same normalized literal).

        Returns:
            The set of known aliases for a normalized (positive) 'literal'.

            Each alias is a tuple containing:
            - the original literal
            - the Boolean flag 'negative'
        """
        if literal not in self._known_aliases:
            known_aliases_str = "\n".join(str(x) for x in self._known_aliases.keys())
            error_str = "Literal {}\nnot found in\n{}".format(
                literal.serialize(), known_aliases_str
            )
            raise ValueError(error_str)
        return self._known_aliases[literal]


class BooleanSimplifier(Simplifier):
    """Simplifier that only performs Boolean simplifications."""

    def __init__(self, env: Environment):
        super().__init__(env)

    @handles(op.IRA_OPERATORS)
    @handles(op.IRA_RELATIONS)
    def walk_identity(self, formula: FNode, args: list[FNode], **kwargs: Any) -> FNode:
        return self.manager.create_node(
            formula.node_type(), args=tuple(map(self.walk, args))
        )
