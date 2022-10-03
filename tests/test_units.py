# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Unicode tests
# :Author:    John Anderson <sontek@gmail.com>
# :License:   MIT License
# :Copyright: © 2015 John Anderson
# :Copyright: © 2016, 2017, 2018, 2020 Lele Gaifax
#

import pytest
import numpy as np

from rapidjson import units


compat_param = [
    ("cm", "m", True),
    ("cm", "s", False),
    ("hr", "d", True),
    ("d", "hr", True)
]
equal_param = [
    ('m', 'meter', True),
    ('m', 'cm', False),
    ('', 'n/a', True)
]


@pytest.mark.parametrize('u,uStr', [
    ("kg", "kg"),
    ("°C", "degC"),
    ("g**2", "g**2"),
    ("km", "km"),
    ("s", "s"),
    ("km*s", "km*s")
])
def test_Units(u, uStr):
    assert str(units.Units(u)) == uStr


@pytest.mark.parametrize('u', [
    'invalid'
])
def test_Units_error(u):
    with pytest.raises(units.UnitsError):
        units.Units(u)


@pytest.mark.parametrize('u', [
    "", "n/a"
])
def test_Units_empty(u):
    x = units.Units(u)
    assert x.is_dimensionless()


@pytest.mark.parametrize('u1,u2,eq', equal_param)
def test_Units_equality(u1, u2, eq):
    x1 = units.Units(u1)
    x2 = units.Units(u2)
    assert (x1 == x2) == eq


@pytest.mark.parametrize('u1,u2,compat', compat_param)
def test_Units_is_compatible(u1, u2, compat):
    units1 = units.Units(u1)
    units2 = units.Units(u2)
    assert units1.is_compatible(units2) == compat
    assert units2.is_compatible(units1) == compat


# //////////////
# // Quantity //
# //////////////

@pytest.mark.parametrize('v,u', [
    (1.0, 'cm'),
    (int(3), 'g')
])
def test_Quantity(v, u):
    str(units.Quantity(v, u))


def test_Quantity_no_units():
    str(units.Quantity(1.0))


@pytest.mark.parametrize('u1,u2,compat', compat_param)
def test_Quantity_is_compatible(u1, u2, compat):
    q1 = units.Quantity(1, u1)
    q2 = units.Quantity(1, u2)
    units2 = units.Units(u2)
    assert q1.is_compatible(units2) == compat
    assert q1.is_compatible(q2) == compat
    assert q2.is_compatible(q1) == compat


@pytest.mark.parametrize('u1,u2,eq', equal_param)
def test_Quantity_equality(u1, u2, eq):
    x1 = units.Quantity(1, u1)
    x2 = units.Quantity(1, u2)
    assert (x1 == x2) == eq


@pytest.mark.parametrize('v1,u1,v2,u2', [
    (1.0, "m", 100.0, "cm"),
    (1.0, "kg", 1000.0, "g"),
    (int(1), "mol", int(1e6), "umol")
])
def test_Quantity_conversion(v1, u1, v2, u2):
    x1 = units.Quantity(v1, u1)
    x2 = x1.to(u2)
    exp = units.Quantity(v2, u2)
    assert x2 == exp


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 100.0, "cm", 2.0, "m"),
    (100.0, "cm", 1.0, "m", 200.0, "cm"),
])
def test_Quantity_add(v1, u1, v2, u2, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x2 = units.Quantity(v2, u2)
    exp = units.Quantity(vExp, uExp)
    assert (x1 + x2) == exp
    assert (x2 + x1).is_equivalent(exp)
    with pytest.raises(units.UnitsError):
        x1 + 1
    with pytest.raises(units.UnitsError):
        1 + x1
    x1 += x2
    assert x1 == exp


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "cm", 0.5, "m"),
    (100.0, "cm", 0.5, "m", 50.0, "cm"),
])
def test_Quantity_subtract(v1, u1, v2, u2, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x2 = units.Quantity(v2, u2)
    exp = units.Quantity(vExp, uExp)
    assert (x1 - x2) == exp
    with pytest.raises(units.UnitsError):
        x1 - 1
    with pytest.raises(units.UnitsError):
        1 - x1
    x1 -= x2
    assert x1 == exp


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "s", 50.0, "m*s"),
    (100.0, "cm", 0.5, "m", 5000.0, "cm**2"),
    (0.5, "m", 100.0, "cm", 0.5, "m**2"),
])
def test_Quantity_multiply(v1, u1, v2, u2, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x2 = units.Quantity(v2, u2)
    exp = units.Quantity(vExp, uExp)
    assert (x1 * x2) == exp
    assert (x2 * x1).is_equivalent(exp)
    exp_scalar = units.Quantity(v1 * 2, u1)
    assert (2 * x1) == exp_scalar
    assert exp_scalar == (x1 * 2)
    x1 *= x2
    assert x1 == exp


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "s", 0.02, "m/s"),
    (100.0, "cm", 0.5, "m", 2.0, ""),
    (0.5, "m", 100.0, "cm", 0.5, ""),
])
def test_Quantity_divide(v1, u1, v2, u2, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x2 = units.Quantity(v2, u2)
    exp = units.Quantity(vExp, uExp)
    assert (x1 / x2) == exp
    exp_scalar = units.Quantity(v1 / 2, u1)
    assert (x1 / 2) == exp_scalar
    assert exp_scalar == (x1 / 2)
    x1 /= x2
    assert x1 == exp


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (100.0, "cm", 0.4, "m", 20.0, "cm"),
    (0.5, "m", 100.0, "cm", 0.5, "m"),
    (0.402, "m**2", 100.0, "cm**2", 0.002, "m**2"),
])
def test_Quantity_modulus(v1, u1, v2, u2, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x2 = units.Quantity(v2, u2)
    exp = units.Quantity(vExp, uExp)
    assert (x1 % x2) == exp
    exp_scalar = units.Quantity(v1 % 7, u1)
    assert (x1 % 7) == exp_scalar
    assert exp_scalar == (x1 % 7)
    x1 %= x2
    assert x1 == exp


@pytest.mark.parametrize('v1,u1,u,vExp,uExp', [
    (1.0, "m", "cm", 100.0, "cm"),
    (int(1), "mol", "umol", int(1e6), "umol")
])
def test_Quantity_set_get_units(v1, u1, u, vExp, uExp):
    x0 = units.Quantity(v1)
    assert x0.units.is_dimensionless()
    x1 = units.Quantity(v1, u1)
    uSet = units.Units(u)
    x1.units = uSet
    exp = units.Quantity(vExp, uExp)
    assert x1 == exp
    assert x1.units == uSet


@pytest.mark.parametrize('v1,u1,v,vExp,uExp', [
    (1.0, "m", 100.0, 100.0, "m"),
    (int(1), "mol", int(1e6), int(1e6), "mol")
])
def test_Quantity_set_get_value(v1, u1, v, vExp, uExp):
    x1 = units.Quantity(v1, u1)
    x1.value = v
    exp = units.Quantity(vExp, uExp)
    assert x1 == exp
    assert x1.value == v


@pytest.mark.parametrize('v1,u1', (
    (100.0, "cm"),
    ))
def test_Quantity_serialize(loads, dumps, v1, u1):
    value = units.Quantity(v1, u1)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded == value and type(loaded) is type(value)


# ///////////////////
# // QuantityArray //
# ///////////////////

@pytest.mark.parametrize('v,u', [
    ([0, 1, 2], 'cm'),
    (np.arange(3, dtype=np.float32), 'cm'),
    (np.arange(4, dtype=np.int8), 'g'),
    (np.int32(3), 'degC'),
])
def test_QuantityArray(v, u):
    x = units.QuantityArray(v, u)
    print(str(x))
    print(repr(x))


def test_QuantityArray_no_units():
    str(units.QuantityArray(np.arange(3)))


@pytest.mark.parametrize('u1,u2,compat', compat_param)
def test_QuantityArray_is_compatible(u1, u2, compat):
    arr = np.arange(3)
    q1 = units.QuantityArray(arr, u1)
    q2 = units.QuantityArray(arr, u2)
    units2 = units.Units(u2)
    assert q1.is_compatible(units2) == compat
    assert q1.is_compatible(q2) == compat
    assert q2.is_compatible(q1) == compat
    assert q1.dtype == arr.dtype
    assert q1.dtype == q2.dtype
    assert q1.ndim == arr.ndim
    assert q1.ndim == q2.ndim
    assert q1.shape == arr.shape
    assert q1.shape == q2.shape


@pytest.mark.parametrize('u1,u2,eq', equal_param)
def test_QuantityArray_equality(u1, u2, eq):
    x1 = units.QuantityArray(np.arange(3), u1)
    x2 = units.QuantityArray(np.arange(3), u2)
    assert np.array_equal(x1, x2) == eq
    assert np.allclose(x1, x2) == eq


@pytest.mark.parametrize('v1,u1,v2,u2', [
    (np.arange(3, dtype=np.float32), "m",
     np.float32(100.0) * np.arange(3, dtype=np.float32), "cm"),
    (np.arange(3, dtype=np.float64), "kg",
     np.float64(1000.0) * np.arange(3, dtype=np.float64), "g"),
    (np.arange(4, dtype=int), "mol",
     1e6 * np.arange(4, dtype=int), "umol")
])
def test_QuantityArray_conversion(v1, u1, v2, u2):
    x1 = units.QuantityArray(v1, u1)
    x2 = x1.to(u2)
    exp = units.QuantityArray(v2, u2)
    assert np.array_equal(x2, exp)


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 100.0, "cm", 2.0, "m"),
    (100.0, "cm", 1.0, "m", 200.0, "cm"),
])
def test_QuantityArray_add(v1, u1, v2, u2, vExp, uExp):
    arr = np.arange(6).reshape((3, 2))
    arrAlt = np.arange(6)
    x1 = units.QuantityArray(v1 * arr, u1)
    x2 = units.QuantityArray(v2 * arr, u2)
    exp = units.QuantityArray(vExp * arr, uExp)
    xAlt = units.QuantityArray(v2 * arrAlt, u2)
    assert np.array_equal((x1 + x2), exp)
    assert (x2 + x1).is_equivalent(exp)
    with pytest.raises(units.UnitsError):
        x1 + 1
    with pytest.raises(units.UnitsError):
        1 + x1
    with pytest.raises(ValueError):
        x1 + xAlt
    with pytest.raises(ValueError):
        xAlt + x1
    x1 += x2
    assert np.array_equal(x1, exp)


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "cm", 0.5, "m"),
    (100.0, "cm", 0.5, "m", 50.0, "cm"),
])
def test_QuantityArray_subtract(v1, u1, v2, u2, vExp, uExp):
    arr = np.arange(6).reshape((3, 2))
    arrAlt = np.arange(6)
    x1 = units.QuantityArray(v1 * arr, u1)
    x2 = units.QuantityArray(v2 * arr, u2)
    exp = units.QuantityArray(vExp * arr, uExp)
    xAlt = units.QuantityArray(v2 * arrAlt, u2)
    assert np.array_equal((x1 - x2), exp)
    with pytest.raises(units.UnitsError):
        x1 - 1
    with pytest.raises(units.UnitsError):
        1 - x1
    with pytest.raises(ValueError):
        x1 - xAlt
    with pytest.raises(ValueError):
        xAlt - x1
    x1 -= x2
    assert np.array_equal(x1, exp)


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "s", 50.0, "m*s"),
    (100.0, "cm", 0.5, "m", 5000.0, "cm**2"),
    (0.5, "m", 100.0, "cm", 0.5, "m**2"),
])
def test_QuantityArray_multiply(v1, u1, v2, u2, vExp, uExp):
    arr = np.arange(6).reshape((3, 2))
    arrAlt = np.arange(6)
    x1 = units.QuantityArray(v1 * arr, u1)
    x2 = units.QuantityArray(v2 * arr, u2)
    exp = units.QuantityArray(vExp * arr * arr, uExp)
    xAlt = units.QuantityArray(v2 * arrAlt, u2)
    assert np.array_equal((x1 * x2), exp)
    assert (x2 * x1).is_equivalent(exp)
    exp_scalar = units.QuantityArray(2 * v1 * arr, u1)
    assert np.array_equal((2 * x1), exp_scalar)
    assert np.array_equal(exp_scalar, (x1 * 2))
    x1 *= x2
    assert np.array_equal(x1, exp)
    with pytest.raises(ValueError):
        x1 * xAlt
    with pytest.raises(ValueError):
        xAlt * x1


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (1.0, "m", 50.0, "s", 0.02, "m/s"),
    (100.0, "cm", 0.5, "m", 2.0, ""),
    (0.5, "m", 100.0, "cm", 0.5, ""),
])
def test_QuantityArray_divide(v1, u1, v2, u2, vExp, uExp):
    arr = np.arange(1, 7).reshape((3, 2))
    arrAlt = np.arange(1, 7)
    x1 = units.QuantityArray(v1 * arr, u1)
    x2 = units.QuantityArray(v2 * arr, u2)
    exp = units.QuantityArray(vExp * np.ones(arr.shape), uExp)
    xAlt = units.QuantityArray(v2 * arrAlt, u2)
    assert np.array_equal((x1 / x2), exp)
    exp_scalar = units.QuantityArray(v1 * arr / 2, u1)
    assert np.array_equal((x1 / 2), exp_scalar)
    assert np.array_equal(exp_scalar, (x1 / 2))
    x1 /= x2
    assert np.array_equal(x1, exp)
    with pytest.raises(ValueError):
        x1 / xAlt
    with pytest.raises(ValueError):
        xAlt / x1


@pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
    (100.0, "cm", 0.4, "m", 20.0, "cm"),
    (0.5, "m", 100.0, "cm", 0.5, "m"),
    (0.402, "m**2", 100.0, "cm**2", 0.002, "m**2"),
])
def test_QuantityArray_modulus(v1, u1, v2, u2, vExp, uExp):
    arr = np.arange(1, 7).reshape((3, 2))
    arrAlt = np.arange(1, 7)
    x1 = units.QuantityArray(v1 * arr, u1)
    x2 = units.QuantityArray(v2 * arr, u2)
    exp = units.QuantityArray(vExp * arr, uExp)
    xAlt = units.QuantityArray(v2 * arrAlt, u2)
    res = x1 % x2
    assert np.allclose(res, exp)
    assert np.allclose((x1 % x2), exp)
    exp_scalar = units.QuantityArray((v1 * arr) % 7, u1)
    assert np.allclose((x1 % 7), exp_scalar)
    assert np.allclose(exp_scalar, (x1 % 7))
    x1 %= x2
    assert np.allclose(x1, exp)
    with pytest.raises(ValueError):
        x1 % xAlt
    with pytest.raises(ValueError):
        xAlt % x1


@pytest.mark.parametrize('v1,u1,u,vExp,uExp', [
    (1.0, "m", "cm", 100.0, "cm"),
    (int(1), "mol", "umol", int(1e6), "umol")
])
def test_QuantityArray_set_get_units(v1, u1, u, vExp, uExp):
    arr = np.arange(6).reshape((3, 2))
    x0 = units.QuantityArray(arr)
    assert x0.units.is_dimensionless()
    x1 = units.QuantityArray(v1 * arr, u1)
    uSet = units.Units(u)
    x1.units = uSet
    exp = units.QuantityArray(vExp * arr, uExp)
    assert np.array_equal(x1, exp)
    assert x1.units == uSet


@pytest.mark.parametrize('v1,u1,v,vExp,uExp', [
    (1.0, "m", 100.0, 100.0, "m"),
    (int(1), "mol", int(1e6), int(1e6), "mol")
])
def test_QuantityArray_set_get_value(v1, u1, v, vExp, uExp):
    arr = np.arange(6).reshape((3, 2))
    x1 = units.QuantityArray(v1 * arr, u1)
    x1.value = v * arr
    exp = units.QuantityArray(vExp * arr, uExp)
    assert np.array_equal(x1, exp)
    assert np.array_equal(x1.value, (v * arr))
    np.testing.assert_equal(x1, exp)
    np.testing.assert_equal(x1.value, (v * arr))


def test_QuantityArray_set_get_item():
    arr = np.ones((3, 2))
    sub = np.ones(3)
    x1 = units.QuantityArray(arr, 'cm')
    xsub = units.QuantityArray(sub, 'cm')
    print(x1[:, 0], xsub)
    assert np.array_equal(x1[:, 0], xsub)
    assert x1[0, 0] == units.Quantity(1, 'cm')
    x1[0, 0] = 3
    x1[0, 1] = units.Quantity(0.03, 'm')
    arr[0, 0] = 3
    arr[0, 1] = 3
    x2 = units.QuantityArray(arr, 'cm')
    assert np.array_equal(x1, x2)
    assert x1[0, 0] == units.Quantity(3, 'cm')


@pytest.mark.parametrize('func,finv,x_in,x_out', (
    (np.sin, np.arcsin, [-np.pi/2, 0, np.pi/2], [-1, 0, 1]),
    (np.cos, np.arccos, [0, np.pi/2, np.pi], [1, 0, -1]),
    (np.tan, np.arctan, [-np.pi/4, 0, np.pi/4], [-1, 0, 1]),
    (np.sinh, np.arcsinh, [-np.pi/2, 0, np.pi/2],
     [-2.30129890231, 0, 2.30129890231]),
    (np.cosh, np.arccosh, [0, np.pi/2, np.pi],
     [1, 2.50917847866, 11.5919532755]),
    (np.tanh, np.arctanh, [-np.pi/4, 0, np.pi/4],
     [-0.65579420263, 0, 0.65579420263])
))
def test_QuantityArray_trig(func, finv, x_in, x_out):
    arr_rad = np.asarray(x_in)
    arr_out = np.asarray(x_out)
    x_rad = units.QuantityArray(x_in, "radians")
    x_deg = units.QuantityArray(np.rad2deg(arr_rad), "degrees")
    x_res = units.QuantityArray(x_out)
    assert np.allclose(np.rad2deg(x_rad), x_deg)
    assert np.allclose(np.deg2rad(x_deg), x_rad)
    assert np.allclose(func(x_rad), arr_out)
    assert np.allclose(func(x_deg), arr_out)
    assert np.allclose(finv(x_res), x_rad)


@pytest.mark.parametrize('v1,u1', (
    (100.0, "cm"),
    ))
def test_QuantityArray_serialize(loads, dumps, v1, u1):
    arr = np.arange(6).reshape((3, 2))
    value = units.QuantityArray(v1 * arr, u1)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert np.array_equal(loaded, value) and type(loaded) is type(value)
