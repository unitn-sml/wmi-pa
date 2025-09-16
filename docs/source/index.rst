..
   Note: Items in this toctree form the top-level navigation. See `api.rst` for the `autosummary` directive, and for why `api.rst` isn't called directly.

.. toctree::
   :hidden:
   :maxdepth: 0

   Home page <self>
   Theory <theory>
   Get started <getstarted>
   Jupyter tutorials <tutorials>
   API reference <_autosummary/wmipa>
   Development <development>

.. autosummary::
   :hidden:
   :recursive:

   wmipa


Welcome to the wmipy documentation
==================================

.. centered::
   ``wmipy`` :math:`=` **quantitative reasoning** over **algebraic** and
   **logical constraints** in ``python3``

.. math::

   P(x \ge y \:|\: y / 2 \le \pi) = ??

.. image:: images/intro-cropped.png
   :scale: 30 %
   :align: center

.. centered::
   ... ``pip install wmipy`` !


``wmipy`` is a modular library for solving **Weighted Model
Integration** (WMI) and related quantitative reasoning tasks over
mixed continuous / logical domains.

Our goals:

* Facilitating the integration of state-of-the-art WMI technology into your project
* Providing a flexible framework for the development of novel solvers

**Unfamiliar with WMI or SMT?** :ref:`Read <theory>` our theory primer first.

**Eager to code?** :ref:`Get started <getstarted>` now!

**Curious about advanced use cases?** :ref:`Check out <tutorials>` our Jupiter notebooks.

**Want to be part of** ``wmipy`` **?** :ref:`Learn <development>` how to contribute.
