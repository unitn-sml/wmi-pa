..
   Note: Items in this toctree form the top-level navigation. See `api.rst` for the `autosummary` directive, and for why `api.rst` isn't called directly.

.. toctree::
   :hidden:
   :maxdepth: 0

   Home page <self>
   Introduction <introduction>
   Installation <installation>
   Jupyter tutorials <tutorials>
   API reference <_autosummary/wmipa>
   Development <development>

.. autosummary::
   :hidden:
   :recursive:

   wmipa


Welcome to the wmipy documentation
==================================

The ``wmipy`` library is a ``python3`` library for reasoning over *weighted* algebraic and logical constraints.

The main use case is solving **Weighted Model Integration** (WMI), a
computational task that is akin to **probabilistic inference** over
**algebraic** and **logical constraints**.

The wmipy library is meant to:

* facilitate the use of state-of-the-art WMI solvers
* provide a modular framework for the development of novel reasoning techniques


If you are unfamiliar with WMI, check our :ref:`introduction <introduction>`,
which contains a primer on the theoretical groundwork and showcases a
number of use cases for the library.


