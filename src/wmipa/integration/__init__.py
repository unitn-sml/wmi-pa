"""The wmipy.integration submodule handles anything related to the integration of weight functions over convex polytopes.

It exposes the following base integrators:

- RejectionIntegrator: an approximate integrator based on rejection sampling
- LattEIntegrator: an exact integrator based on the LattE Integrale software

It also exposes the following integration wrappers:

- AxisAlignedWrapper
- CacheWrapper
- ParallelWrapper

Finally, it exposes Integrator, a generic integration protocol.
"""

from .axisaligned import AxisAlignedWrapper
from .cache import CacheWrapper
from .latte import LattEIntegrator
from .parallel import ParallelWrapper
from .rejection import RejectionIntegrator
from .integrator import Integrator
