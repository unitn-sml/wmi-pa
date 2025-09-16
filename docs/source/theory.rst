
.. _theory:

Theory
======

Theoretical background
----------------------


Satisfiability Modulo Theories
""""""""""""""""""""""""""""""

Satisfiability Modulo Theories (SMT) [:ref:`1 <bib-smt>`] is concerned
with determining the satisfiability of formulas containing both
propositional and *theory* atoms. In this sense, it is a strict
generalization of propositional satisfiability (SAT) to formulas that
not only contain Boolean variables (as known as propositions),
i.e. variables that evaluates to true (:math:`\top`) or false
(:math:`\bot`).

As in SAT, :math:`SMT(\Delta)` is a binary decision problem: the
formula :math:`\Delta` is either **sat**\ isfiable or **unsat**\
isfiable.

:math:`\Delta` is **sat** if there exists a *satisfying truth
assignment* (TA) to the formula's atoms.

* A TA is a mapping:

  .. math::

     \mu: \text{Atoms}(\Delta) \rightarrow \{ \top, \bot\}
	
* A TA *propositionally satisfies* :math:`\Delta` if the formula
  obtained by substituting the atoms with their respective truth
  values evaluates to :math:`\top`.
* In contrast with SAT, in SMT a TA can be *theory unsatisfiable*.
* A *satisfying* TA in SMT both *propositionally satisfies* :math:`\Delta` and is *theory-satisfiable* (denoted :math:`\mu \models \Delta` ).

The existence of a satisfying TA implies that there exist at
least a value assignment to the variables of the formula that satisfy
it. An assignment to the variables of a formula is called a *model*.

.. warning::

   In SAT, there is a 1-to-1 correspondence between satisfying TA and
   models, since propositions (i.e. Boolean variables) are the only
   kind of atoms in propositional logic. The distinction, however, is
   important in SMT, where atoms can contain non-Boolean variables.

This library focuses on SMT with the theory of *linear algebra over
reals* (SMT-LRA), which enables joint logical / algebraic reasoning.
LRA atoms are linear (in)equalities over real variables:

.. math::
   (\sum_i a_i x_i \: \{<, \le, >, \ge, =\} \: b)

SMT-LRA formulas combine LRA atoms with propositional variables using
the standard logical connectives (:math:`\land, \lor, \rightarrow,
\leftrightarrow, \oplus, ...`), resulting in a flexible formalism for
encoding *non-convex* sets over hybrid discrete/continuous spaces.

For example:

.. math::
   ((2x + y \le 3) \lor A) \rightarrow ((z < y) \land B)

is a SMT-LRA formula having:

* 3 real variables in 2 LRA atoms
* 2 propositional variables / atoms

.. warning::

   For ease of exposition, in the following we restrict to SMT-LRA
   formulas containing LRA atoms only (i.e. Boolean variables).  The
   extension of the definitions to formulas with propositional
   variables is straightforward and can be found in the cited papers.

SMT is a centerpiece in automated reasoning and has found many
practical applications, in particular in the formal verification of
software and hardware systems. More recently, SMT has been applied to
the verification of machine learning models.

.. _ex1:
.. admonition:: Example 1
	   
   Let :math:`w_1, ..., w_N` be the parameters of a rectified
   linear unit (ReLU) over inputs :math:`x_1, ... , x_N`. The unit can
   be encoded with the following SMT-LRA formula:

   .. math::
      Unit \equiv (h = \sum_i w_i \cdot x_i) \land (h > 0 \rightarrow y = h) \land (\neg h > 0 \rightarrow y = 0)

   where :math:`h` denotes the pre-activation value of the unit.

   SMT solvers are widely used for reasoning on a trained neural network,
   therefore the parameters :math:`w_i` are real *constants*.

   A ReLU unit is said to be firing if it propagates a signal, i.e.:

   .. math::
      Firing \equiv (y > 0)
	      
   For a given subset of its inputs, a ReLU unit can be:

   * *inactive* if it never fires
   * *active* if it always fires
   * *unstable* otherwise

   Using SMT, it is possible to determine if the unit is *inactive* given an interval:

   .. math::
      I \equiv \bigwedge_i (l_i \le x_i) \land (x_i \le u_i)

   The unit is inactive in :math:`I` if and only if the following SMT calls

   .. math::
      SMT(Unit \land Firing \land I)

   returns **unsat**, indicating that there doesn't exist an assignment
   to :math:`x_1, ..., x_N` for which the formula evaluates to true.


Our library builds upon ``pysmt`` for defining SMT-LRA formulas.

.. cex1:
.. admonition:: Code Example 1

   The following code implements :ref:`Example 1 <ex1>` for a toy scenario with 2 input variables.
   The parameters are set to :math:`\mathbf{w} = [1,1]` for simplicity in the following examples.

   .. literalinclude :: ../examples/theory1.py
       :language: python


Check the ``pysmt`` `documentation
<https://pysmt.readthedocs.io/en/latest/>`__ for more examples and an in-depth discussion on SMT.

From qualitative to quantitative reasoning
""""""""""""""""""""""""""""""""""""""""""


SMT-LRA enables **qualitative** algebraic / logical reasoning, for
instance, it can be used to decide whether a certain property is
satisfied by a neural network or not.  What it *can't* be used for is
**quantitative** analysis on the satisfaction of a formula (e.g. the
*probability* of satisfaction).

In order to enable quantitative reasoning on top of SMT, a few aspects
have to be addressed.

First, instead of searching for a single satisfying TA, we need to
**enumerate** them all, i.e., compute a set :math:`M` such that:

* :math:`\forall \mu \in M \:.\: \mu \models \Delta` (they satisfy the formula)
* :math:`\forall \mu_i, \mu_j \in M \:.\: i \neq j \implies \mu_i \land \mu_j \models \bot` (they are mutually disjoint)
* :math:`\cup_{\mu \in M} \equiv \Delta` (they form a complete partitioning of the formula)

.. _ex2:
.. admonition:: Example 2
		
   Consider the ReLU encoding in :ref:`Example 1 <ex1>`. The formula :math:`Unit` defines two
   convex regions of the input space:

   .. math::
      (h = \sum_i w_i \cdot x_i) \land \textcolor{blue}{\phantom{\neg}(h > 0)} \land \textcolor{red}{\neg (y = 0)} \land \textcolor{blue}{\phantom{\neg}(y = h)} \\\\
      (h = \sum_i w_i \cdot x_i) \land \textcolor{red}{\neg(h > 0)} \land \textcolor{blue}{\phantom{\neg} (y = 0)} \land \textcolor{red}{\neg(y = h)}


Second, we need to be able to quantify the number of models for each
satisfying TA. In LRA, models are typically uncountable. We can,
however, compute the volume of a satisfying TA:

.. math::
   vol(\mu) \equiv \int_\mu 1 \quad d\mathbf{x}

where :math:`\int_\mu` denotes an integral restricted to
:math:`\mu`. :math:`vol(\mu)` is finite if :math:`\mu` is a closed
polytope.

.. _ex3:
.. admonition:: Example 3
		
   Consider the formula
   
   .. math::
      \Delta \equiv (0 \le x) \land (0 \le y) \land ((x + y \le 1) \lor ((x \ge y) \land (x \le 1)))

   .. image:: images/example3.png
      :scale: 50 %
      :alt: example3 plot
      :align: center
  
   The set of satisfying TAs is (omitting always true atoms :math:`(0 \le x), (0 \le y), (x \le 1)`):
   
   .. math::

      \mu_1 = \phantom{\neg} (x + y \le 1) \land \neg (x \ge y) \\\\
      \mu_2 = \phantom{\neg}(x + y \le 1) \land \phantom{\neg} (x \ge y) \\\\
      \mu_3 = \neg (x + y \le 1) \land \phantom{\neg} (x \ge y) \\\\

   each having equal volume :math:`vol(\mu_i) = \int_{\mu_i} 1 \: dx dy = 1/4`.

We can easily generalize the concept of volume from TAs to arbitrary formulas:

   .. math::

      vol(\Delta) \equiv \sum_{\mu \models \Delta} vol(\mu)

This is useful when we want to compute *ratios of satisfaction*. In
:ref:`Example 3 <ex3>`, we can conclude that :math:`x \ge y` is
satisfied by 2/3 of the models of :math:`\Delta`.

Notice that, so far, each model has the same "importance" in our
quantitative calculations. In probabilistic terms, we would say that
models are *uniformly* distributed.

Weighted Model Integration
""""""""""""""""""""""""""

Weighted Model Integration (WMI) [:ref:`2 <bib-wmi>`] is a formalism
introduced in the context of probabilistic inference with logical and
algebraic constraints.


Simply put, quantitative SMT-LRA reasoning is complemented with a
notion of *weight*.  A weight is defined by two ingredients:

* a weight function :math:`w`, which associates a non-negative value to models
* a weight support :math:`\chi`, which restricts the domain of :math:`w`


The *weighted model integral* of a weighted SMT-LRA formula
:math:`\langle \chi, w \rangle` is defined as:

.. math::
   WMI(\chi, w) \equiv \sum_{\mu \models \chi} \int_\mu w(\mathbf{x}) \: d\mathbf{x}

In theory, the only prerequisite for :math:`w` (aside from
non-negativity) is to be integrable over convex polytopes.  In
practice, most approaches in WMI consider *piecewise polynomial
weights*.  The reason is twofold:

* They are arbitrary approximators (`Stone-Weierstrass theorem <https://en.wikipedia.org/wiki/Stone%E2%80%93Weierstrass_theorem>`__)
* They are easy to work with, being closed under the following operations: :math:`+, \cdot, \int_\mu`


``wmipy`` uses the ``pysmt`` formulas for defining the weight.  In
practice, while the support is a standard SMT-LRA formula, the weight
function is an LRA term, i.e. an expression that does not evaluate to
true or false.

.. cex2:
.. admonition:: Code Example 2

   The following code implements the quantitative analysis introduced
   in :ref:`Example 3 <ex3>` with two different weight functions:

   * constant 1 (i.e. unweighted)
   * the quadratic polynomial :math:`x^2 + 1`

   .. literalinclude :: ../examples/theory2.py
       :language: python

More complex weight functions can be defined by combining valid weight
terms by means of If-Then-Else expressions.

For instance, the following code defines a univariate triangular
distribution with domain :math:`[-l, u]` and mode :math:`m`:

.. code-block:: python

   from pysmt.shortcuts import *

   x = Symbol("x", REAL)

   height = 2 / (u - l) # ensures a normalized distribution

   a1 = height / (m - l)
   b1 = -a1 * l

   a2 = height / (m - u)
   b2 = -a2 * u

   support = And(LE(Real(l), x), LE(x, Real(u)))

   linear = lambda a, b : Plus(Times(Real(a), x), Real(b))

   w = Ite(LE(x, Real(m)), linear(a1, b1), linear(a2, b2))


Bibliography
------------

.. _bib-smt:

| [1] **Satisfiability Modulo Theories**
| Clark Barrett, Roberto Sebastiani, Sanjit A. Seshia and Cesare Tinelli
| `book chapter <https://escholarship.org/content/qt11n7z852/qt11n7z852.pdf>`__

.. _bib-wmi:

| [2] **Probabilistic inference in hybrid domains by weighted model integration**
| Vaishak Belle, Andrea Passerini and Guy Van den Broeck
| `conference paper <https://www.ijcai.org/Proceedings/15/Papers/392.pdf>`__

.. _bib-sae4wmi:

| [3] **Enhancing SMT-based Weighted Model Integration by structure awareness**
| Giuseppe Spallitta, Gabriele Masina, Paolo Morettin, Andrea Passerini and Roberto Sebastiani
| `journal paper <https://disi.unitn.it/rseba/papers/AIJ24.pdf>`__

