
.. _getstarted:

Get started
===========

Installation
------------


.. include:: ../../INSTALL.md
   :parser: myst_parser.sphinx_

TODO


Command Line Interface
----------------------


.. include:: ../../CLI.md
   :parser: myst_parser.sphinx_

TODO

A short tour
------------

``wmipy`` evolved from ``wmipa``, a state-of-the-art SMT-based WMI
solver, with the goal of further extending its modular approach and
potentially accomodate other computational tasks over weighted SMT formulas.

Notice that the WMI task gracefully decomposes into two subtasks:

.. math::

   WMI(\Delta, w) = \overbrace{\sum_{\mu \models \Delta}}^{(1)} \quad \underbrace{\int_{\mu} w(\mathbf{x}) \: d\mathbf{x}}_{(2)}


1. **Enumerating** the satisfying TAs :math:`\mu` given a weighted SMT formula :math:`\langle \Delta, w \rangle`
2. **Integrating** the resulting convex polytopes / integrands

We are designing ``wmipy`` in order to be modular. TODO: continue

Enumerators
"""""""""""

The library offer different stand-alone enumerators. An enumerator constructor takes as
input a weighted SMT formula (plus the current ``pysmt`` environment).

.. code-block:: python

   import pysmt.shortcuts as smt
   from wmipa.enumeration import TotalEnumerator

   ...

   enumerator = TotalEnumerator(support, w, smt.get_env())

Enumerators provide an ``enumerate`` method that takes as input a
``query`` SMT-formula (encoding a subset of the support of interest)
and returns an `Iterable` over pairs of:

* Satisfying TAs (implemented as dict mapping ``pysmt`` atoms into ``bool``)
* The number of unassigned Boolean variables (``int``).

.. code-block:: python

   ...

   query = smt.LE(x, smt.Real(5))
   for ta, nb in enumerator.enumerate(query):
        print("TA:", ta, "\nUnassigned booleans:", nb, "\n")


.. warning::

   The number of unassigned Booleans is fundamental for computing the
   count/integral. It will always be 0 (and therefore it can be ignored) for
   enumerators returning *total* TAs, such as ``TotalEnumerator``.


Polytopes and  Polynomials
""""""""""""""""""""""""""

For some applications, the output of an enumerator is already in the
ideal format.

For all other use cases, ``wmipy`` leverages intermediate internal
representations for polytopes and polynomials. The classes
``Polytope`` and ``Polynomial`` are meant to implement all the useful
function for manipulating these algebraic objects.

``AssignmentConverter`` implements a wrapper around enumerators that
converts TAs into ``tuple(Polytope, Polynomial)``:

.. code-block:: python

   from wmipa.core import AssignmentConverter

   ...

   # the continuous domain
   domain = [Symbol("x", REAL), Symbol("y", REAL)] 

   converter = AssignmentConverter(self.enumerator)     
   for ta, nb in enumerator.enumerate(query):
        polytope, polynomial = converter.convert(truth_assignment, domain)


``Polytope`` and ``Polynomial`` are meant to be stand-alone objects
and can be instantiated directly. Both are defined on a continuous
domain plus a set of inequalities (for the former) of a polynomial
expression (for the latter). Passing a `pysmt` environment to the
constructor is optional but recommended.

The following code example shows how tos convert them into a ``numpy``
representation, or convert them back to (canonical) ``pysmt`` formulas
/ terms.
   
.. literalinclude :: ../examples/polys.py
    :language: python


Integration
"""""""""""

TODO
