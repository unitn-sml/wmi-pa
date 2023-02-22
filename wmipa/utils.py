"""This module implements some usefull methods used throughout the code.

Credits: least common multiple code by J.F. Sebastian
    (http://stackoverflow.com/a/147539)

"""

from functools import reduce

import networkx as nx
from pysmt.operators import POW
from pysmt.typing import BOOL, REAL

from wmipa.wmiexception import WMIParsingException

try:
    from pysmt.operators import EXP
except ImportError:
    EXP = None


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
        bool: True if the node is the Pow operator, False otherwise.

    """
    return node.node_type() == POW


def is_exp(node):
    """Test whether the node is the Exp operator
    If the pysmt version does not support Exp, then return False

    Args:
        node (FNode): The node to examine.

    Returns:
        bool: True if the node is the Exp operator, False otherwise.

    """
    return node.node_type() == EXP


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
        args (list(int)): The list of numbers on which to compute the
            lowest common multiple.

    Returns:
        int: The lowest common multiple of all the numbers in the list.

    """
    return reduce(_lcm, args)


def apply_aliases(expression, aliases):
    """Substitute the aliases within the expression in the right order.

    Args:
        expression (FNode): The pysmt expression to apply the aliases to.
        aliases (dict): The aliases to apply to the expression.
    """
    if len(aliases) > 0:
        # Build a dependency graph of the substitutions and apply them in
        # topological order
        Gsub = nx.DiGraph()
        constant_subs = {}

        # For every alias
        for x, alias_expr in aliases.items():
            for y in alias_expr.get_free_variables():
                # Create a node from the alias to every symbol inside it
                Gsub.add_edge(x, y)
            # If the alias substitution leads to a constant value (e.g: PI = 3.1415)
            if len(alias_expr.get_free_variables()) == 0:
                constant_subs.update({x: alias_expr})

        # Get the nodes in topological order
        try:
            sorted_substitutions = [
                node for node in nx.topological_sort(Gsub) if node in aliases
            ]
        except nx.exception.NetworkXUnfeasible:
            raise WMIParsingException(
                WMIParsingException.CYCLIC_ASSIGNMENT_IN_ALIASES, aliases
            )

        # Apply all the substitutions
        for alias in sorted_substitutions:
            expression = expression.substitute({alias: aliases[alias]})
        expression = expression.substitute(constant_subs)
    return expression


def is_atom(node):
    return node.is_symbol(BOOL) or node.is_theory_relation()


def is_literal(node):
    return is_atom(node) or (node.is_not() and is_atom(node.arg(0)))


def is_clause(formula):
    return is_literal(formula) or (
            formula.is_or() and all(is_literal(l) for l in formula.args())
    )


def is_cnf(formula):
    return is_clause(formula) or (
            formula.is_and() and all(is_clause(c) for c in formula.args())
    )
