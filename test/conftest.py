import pytest

from wmipa.enumeration import *
from wmipa.integration import *

from numerical import *


@pytest.fixture
def exact_integrators():
    return [
        (LattEIntegrator, {}),
        (AxisAlignedWrapper, {"integrator": LattEIntegrator()}),
        (CacheWrapper, {"integrator": LattEIntegrator()}),
        (ParallelWrapper, {"integrator": LattEIntegrator()}),
        (AxisAlignedWrapper, {"integrator": CacheWrapper(LattEIntegrator())}),
        (AxisAlignedWrapper, {"integrator": ParallelWrapper(LattEIntegrator())}),
        (CacheWrapper, {"integrator": ParallelWrapper(LattEIntegrator())}),
        (
            AxisAlignedWrapper,
            {"integrator": CacheWrapper(ParallelWrapper(LattEIntegrator()))},
        ),
    ]


@pytest.fixture
def integration_wrappers():
    return [AxisAlignedWrapper, CacheWrapper, ParallelWrapper]


@pytest.fixture
def enumerators():
    return [
        (Z3Enumerator, {}),
        (SAEnumerator, {"max_queue_size": 1}),
        (SAEnumerator, {"max_queue_size": 0}),
        (AsyncWrapper, {"enumerator": SAEnumerator(), "max_queue_size": 0}),
        (AsyncWrapper, {"enumerator": SAEnumerator(), "max_queue_size": 1}),
        (AsyncWrapper, {"enumerator": Z3Enumerator()}),
    ]
