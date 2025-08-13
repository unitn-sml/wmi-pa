import pytest

from wmipa.enumeration import *
from wmipa.integration import *

from numerical import *


exact_integrators = [
    ("latte", lambda: LattEIntegrator()),
    ("axisaligned-latte", lambda: AxisAlignedWrapper(LattEIntegrator())),
    ("cache-latte", lambda: CacheWrapper(LattEIntegrator())),
    ("parallel-latte", lambda: ParallelWrapper(LattEIntegrator())),
    (
        "axisaligned-cache-latte",
        lambda: AxisAlignedWrapper(CacheWrapper(LattEIntegrator())),
    ),
    (
        "axisaligned-parallel-latte",
        lambda: AxisAlignedWrapper(ParallelWrapper(LattEIntegrator())),
    ),
    ("cache-parallel-latte", lambda: CacheWrapper(ParallelWrapper(LattEIntegrator()))),
    (
        "cache-axisaligned-parallel-latte",
        lambda: CacheWrapper(AxisAlignedWrapper(ParallelWrapper(LattEIntegrator()))),
    ),
]


@pytest.fixture(params=exact_integrators, ids=lambda x: x[0])
def exact_integrator(request):
    return request.param[1]


enumerators = [
    (
        "total",
        lambda support, weights, env: TotalEnumerator(support, weights, env),
    ),
    (
        "sae_q0",
        lambda support, weights, env: SAEnumerator(
            support, weights, env, max_queue_size=0
        ),
    ),
    (
        "sae_q1",
        lambda support, weights, env: SAEnumerator(
            support, weights, env, max_queue_size=1
        ),
    ),
    (
        "async-total",
        lambda support, weights, env: AsyncWrapper(
            TotalEnumerator(support, weights, env)
        ),
    ),
    (
        "async-sae_q0",
        lambda support, weights, env: AsyncWrapper(
            SAEnumerator(support, weights, env, max_queue_size=0)
        ),
    ),
    (
        "async-sae_q1",
        lambda support, weights, env: AsyncWrapper(
            SAEnumerator(support, weights, env, max_queue_size=1)
        ),
    ),
]


@pytest.fixture(params=enumerators, ids=lambda x: x[0])
def enumerator(request):
    return request.param[1]
