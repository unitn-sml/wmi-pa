
.. _getstarted:

Get started
===========

Installation and Command Line Interface
---------------------------------------


.. include:: ../../INSTALL.md
   :parser: myst_parser.sphinx_


A short tour
------------

``wmpy`` evolved from ``wmpy``, a state-of-the-art SMT-based WMI
solver, with the goal of further extending its modular approach and
potentially accomodate other computational tasks over weighted SMT formulas.

Notice that the WMI task gracefully decomposes into two subtasks:

.. math::

   WMI(\Delta, w) = \overbrace{\sum_{\mu \models \Delta}}^{(1)} \quad \underbrace{\int_{\mu} w(\mathbf{x}) \: d\mathbf{x}}_{(2)}


1. **Enumerating** the satisfying TAs :math:`\mu` given a weighted SMT formula :math:`\langle \Delta, w \rangle`
2. **Integrating** the resulting convex polytopes / integrands

The initial phases of development were driven by questions like:

* What if one is only interested in the enumeration subtask?
* What if the convex subtask is not continuous integration?

As a result, the core design principle of ``wmpy`` is **modularity**:
we designed different classes in order to be used as stand-alone
objects as well as sub-components of a larger solver.

Enumerators
"""""""""""

The library offer different enumerators in the submodule
``wmpy.enumeration``. An enumerator constructor takes as input a
weighted SMT formula (plus the current ``pysmt`` environment).

.. code-block:: python

   from pysmt.shortcuts import *
   from wmpy.enumeration import TotalEnumerator

   ...

   smt_env = get_env()
   enumerator = TotalEnumerator(support, w, smt_env)

Enumerators provide an ``enumerate`` method that takes as input a
``query`` SMT-formula (encoding a subset of the support of interest)
and returns an `Iterable` over pairs of:

* Satisfying TAs (implemented as dict mapping ``pysmt`` atoms into ``bool``)
* The number of unassigned Boolean variables (``int``).

.. code-block:: python

   ...

   query = LE(x, Real(5))
   for ta, nb in enumerator.enumerate(query):
        print("TA:", ta, "\nUnassigned booleans:", nb, "\n")


.. warning::

   The number of unassigned Booleans is fundamental for computing the
   count/integral. It will always be 0 (and therefore it can be ignored) for
   enumerators returning *total* TAs, such as ``TotalEnumerator``.


Enumerators can be used as stand-alone components. For instance, the
code below uses ``wmpy`` for implementing a procedure that turns
arbitrary SMT-LRA formulas in disjunctive normal form (DNF),
i.e. disjunctions of conjunctions of literals (atoms or their
negation).
   
.. code-block:: python

   from pysmt.shortcuts import *
   from wmpy.enumeration import SAEnumerator

   def to_dnf(formula, smt_env):
       partial_enumerator = SAEnumerator(formula, Real(1), smt_env)
       disjuncts = []
       for ta, _ in partial_enumerator.enumerate(Bool(True)):
           conj = And(*[atom if is_true else Not(atom) for atom, is_true in ta.items()])
           disjuncts.append(conj)

       return Or(*disjuncts)

Polytopes and  Polynomials
""""""""""""""""""""""""""

For some applications, the output of an enumerator is already in the
ideal format.

For all other use cases, ``wmpy`` leverages intermediate internal
representations for polytopes and polynomials. The classes
``Polytope`` and ``Polynomial`` are meant to implement all the useful
function for manipulating these algebraic objects.

``AssignmentConverter`` implements a wrapper around enumerators that
converts TAs into pairs ``(Polytope, Polynomial)``:

.. code-block:: python

   from wmpy.core import AssignmentConverter

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

The submodule ``wmpy.integration`` contains a number of integrators,
which can be divided into *base* integrators and *wrappers*.

Base integrators implement an ``integrate`` method that takes as input
a pair ``(Polytope, Polynomial)``, respectively encoding the
integration bounds and the integrand. Additionally, an
``integrate_batch`` method is also provided, solving collections of
integral at once.

.. literalinclude :: ../examples/integration.py
    :language: python

Wrappers are objects that add some functionality to integrators, which
are passed as argument to their constructor. Once instantiated, these
implement the same ``integrate`` and ``integrate_batch`` functionality
as baseline integrators.

Some useful wrappers include:

* ``AxisAlignedWrapper`` computes in linear time (in :math:`|\mathbf{x}|`) the integral if the integration domain is an axis-aligned bounding box and the integrand is constant. Otherwise, the enclosed integrator is called.

* ``ParallelWrapper`` uses multiprocessing for parallelizing ``integrate_batch`` calls using the enclosed integration method.

* ``CacheWrapper`` implements a caching mechanism, possibly retrieving pre-computed results.

Wrappers can be combined:

.. code-block:: python

   ...

   from pysmt.integration import *

   integrator = CacheWrapper(ParallelWrapper(LattEIntegrator()))

augments an the exact integrator based on `LattE Integrale
<https://www.math.ucdavis.edu/~latte/>`__ with both caching and
multiprocessing.


Solvers
"""""""

Different modules can be combined into more advanced solvers.

These solvers can be found in ``wmpy.solvers``.  Currently, the only
available solver is a WMI meta-solver ``WMISolver``, which can be
instantiated with any ``enumerator`` and ``integrator``.

For instance, the following lines implement the state-of-the-art WMI solver
SAE4WMI [:ref:`3 <bib-sae4wmi>`]:

.. literalinclude :: ../examples/sae4wmi.py
    :language: python

