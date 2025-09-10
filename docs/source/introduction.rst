

.. _introduction:

Getting started
===============

Check our installation guide for setting up ``wmipy`` on your system.

This section also includes a brief theoretical background for those
unfamiliar with SMT and WMI.


Installation
------------

The library currently supports `python 3.9+` on Linux and MacOS systems.

TODO

Theoretical background
----------------------

Satisfiability Modulo Theory
""""""""""""""""""""""""""""

`Satisfiability Modulo Theory
<https://escholarship.org/content/qt11n7z852/qt11n7z852.pdf>`__ (SMT)
is concerned with determining the satisfiability of formulas
containing both propositional and *theory* atoms. In this sense, it is
a strict generalization of propositional satisfiability (SAT) to
formulas that not only contain Boolean variables.

As in SAT, the outcome of SMT is either **sat**\ isfiable or
**unsat**\ isfiable. In the former case, typically a satisfying *truth
assignment* (TA) to the formula's atoms is also returned by the SMT
solver. In the following, :math:`\mu \models \Delta` denotes that the TA
:math:`\mu` satisfies the formula :math:`\Delta`.


The existence of a satisfying TA implies that there exist at
least a value assignment to the variables of the formula that satisfy
it. An assignment to the variables of a formula is called a *model*.

.. note::

   In SAT, there is a 1-to-1 correspondence between satisfying TA and
   models, since propositions (i.e. Boolean variables) in the formula
   are the only kind of atoms. The distinction is important in SMT,
   where atoms can contain non-Boolean variables.

This library focuses on SMT with the theory of *linear algebra over
reals* (SMT-LRA), which enables joint logical / algebraic reasoning.
LRA atoms are linear (in)equalities over real variables:

.. math::
   (\sum_i a_i x_i \: \{<, \le, >, \ge, =\} \: b)

SMT-LRA formulas combine LRA atoms with propositional variables using
the standard logical connectives (:math:`\land, \lor, \rightarrow,
\leftrightarrow, \oplus, ...`), resulting in a flexible formalism for
encoding *non-convex* sets over hybrid discrete/continuous spaces.

SMT is a centerpiece in automated reasoning and formal methods of
software and hardware systems.  Recently, SMT has found applications
in the verification of machine learning models.

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

.. admonition:: Example 1 (python)

   The following code implements the example above for a toy scenario with 2 input variables.
   The parameters are set to :math:`\mathbf{w} = [1,1]` for simplicity in the following examples.

   .. literalinclude :: ../examples/example1.py
       :language: python


Check the ``pysmt`` `documentation
<https://pysmt.readthedocs.io/en/latest/>`__ for more examples and an in-depth discussion on SMT.


Weighted Model Integration
""""""""""""""""""""""""""

SMT-LRA enables **qualitative** algebraic / logical reasoning, for
instance, it can be used to decide whether a certain property is
satisfied by a neural network or not.  What it *can't* be used for is
answering **quantitative** questions, such as computing the number of
models that satisfy a formula or the *probability* of satisfaction.

`Weighted Model Integration
<https://www.ijcai.org/Proceedings/15/Papers/392.pdf>`__ (WMI) is a
formalism introduced in the context of probabilistic inference with
logical and algebraic constraints.

In order to enable quantitative reasoning, a few aspects have to be addressed.

First, instead of searching for a single satisfying TA, we need to
**enumerate** them all, i.e., compute the set :math:`\{\mu \:|\: \mu
\models \Delta \}`.

.. admonition:: Example 2.1
		
   Consider the ReLU encoding in Example 1. The formula defines two
   convex regions of the input space:

   .. math::
      (h = \sum_i w_i \cdot x_i) \land \textcolor{blue}{\phantom{\neg}(h > 0)} \land \textcolor{red}{\neg (y = 0)} \land \textcolor{blue}{\phantom{\neg}(y = h)} \\\\
      (h = \sum_i w_i \cdot x_i) \land \textcolor{red}{\neg(h > 0)} \land \textcolor{blue}{\phantom{\neg} (y = 0)} \land \textcolor{red}{\neg(y = h)}


Second, we need to be able to quantify the number of models for each
satisfying TA. In LRA the number of models for each TA is often
infinite. We can, however, compute the volume of a TA:

.. math::
   vol(\mu) \equiv \int_\mu 1 \quad d\mathbf{x}

where :math:`\int_\mu` denotes an integral restricted to (the LRA
subset of) :math:`\mu` and :math:`\mathbf{x}` denotes the set of real
variables in the formula.



In WMI, SMT-LRA is complemented with a notion of *weight*.  A weight
is defined by two ingredients:

* a weight function :math:`w`, which associates a value to models
* a weight support :math:`\chi`, which restricts the domain of :math:`w`


The *weighted model integral* of a weighted SMT formula :math:`\langle \chi, w \rangle` is defined as:

.. math::
   WMI(\chi, w) \equiv \sum_{\mu \models \chi} \int_\mu w(x) dx


In SMT terminology, the former is a term while the latter is a formula.

``wmipy`` uses the ``pysmt`` formulas for defining the weight.
Importantly, the weight function doesn't need to be linear.

.. admonition:: Example 2.1

   Let the weight be a univariate triangular distribution centered in the origin with domain :math:`[-1, 1]`.
   
