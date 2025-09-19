import pytest
from itertools import product
import numpy as np
import sys

"""
This module mixtures for numerical constants of general interest.
"""

# floating point numbers

floats_pos = [
    #sys.float_info.min,
    1e-8,
    #1/2,
    1.0,
    1e8,
    #1e10,
    #sys.float_info.max/2,
]
floats_neg = [-c for c in floats_pos]
floats = floats_pos + floats_neg + [0.0]


@pytest.fixture(params=floats)
def f_const(request):
    return request.param


@pytest.fixture(params=floats_pos)
def fp_const(request):
    return request.param


@pytest.fixture(params=floats_neg)
def fn_const(request):
    return request.param


@pytest.fixture(params=product(floats, repeat=2))
def f_vec2(request):
    return request.param


@pytest.fixture(params=product(floats_pos, repeat=2))
def fp_vec2(request):
    return request.param


@pytest.fixture(params=product(floats_neg, repeat=2))
def fn_vec2(request):
    return request.param


@pytest.fixture(params=product(floats, repeat=3))
def f_vec3(request):
    return request.param


@pytest.fixture(params=product(floats_pos, repeat=3))
def fp_vec3(request):
    return request.param


@pytest.fixture(params=product(floats_neg, repeat=3))
def fn_vec3(request):
    return request.param


@pytest.fixture(params=product(floats, repeat=4))
def f_vec4(request):
    return request.param


@pytest.fixture(params=product(floats_pos, repeat=4))
def fp_vec4(request):
    return request.param


@pytest.fixture(params=product(floats_neg, repeat=4))
def fn_vec4(request):
    return request.param


# integer numbers

ints_pos = [int(c) for c in floats_pos]
ints_neg = [-c for c in ints_pos]
ints = ints_pos + ints_neg + [0]


@pytest.fixture(params=ints)
def i_const(request):
    return request.param


@pytest.fixture(params=ints_pos)
def ip_const(request):
    return request.param


@pytest.fixture(params=ints_neg)
def in_const(request):
    return request.param


@pytest.fixture(params=product(ints, repeat=2))
def i_vec2(request):
    return request.param


@pytest.fixture(params=product(ints_pos, repeat=2))
def ip_vec2(request):
    return request.param


@pytest.fixture(params=product(ints_neg, repeat=2))
def in_vec2(request):
    return request.param


@pytest.fixture(params=product(ints, repeat=3))
def i_vec3(request):
    return request.param


@pytest.fixture(params=product(ints_pos, repeat=3))
def ip_vec3(request):
    return request.param


@pytest.fixture(params=product(ints_neg, repeat=3))
def in_vec3(request):
    return request.param


@pytest.fixture(params=product(ints, repeat=4))
def i_vec4(request):
    return request.param


@pytest.fixture(params=product(ints_pos, repeat=4))
def ip_vec4(request):
    return request.param


@pytest.fixture(params=product(ints_neg, repeat=4))
def in_vec4(request):
    return request.param


# exponents

exps = [0, 1, 2, 10]


@pytest.fixture(params=exps)
def exp_const(request):
    return request.param


@pytest.fixture(params=product(exps, repeat=2))
def exp_vec2(request):
    return request.param


@pytest.fixture(params=product(exps, repeat=3))
def exp_vec3(request):
    return request.param


@pytest.fixture(params=product(exps, repeat=4))
def exp_vec4(request):
    return request.param


@pytest.fixture(params=product(exps, repeat=5))
def exp_vec5(request):
    return request.param
