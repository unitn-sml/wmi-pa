"""The wmipy.core submodule contains task-agnostic classes and utilities.

It exposes:

- AssignmentConverter: a class that facilitates the conversion of satisfying TAs into polytope, polynomial pairs
- Polynomial: the internal class for handling polynomials
- Polytope: the internal class for handling convex polytopes
"""

from .assignmentconverter import AssignmentConverter
from .polynomial import Polynomial
from .polytope import Polytope
