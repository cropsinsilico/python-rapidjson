# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Unicode tests
# :Author:    John Anderson <sontek@gmail.com>
# :License:   MIT License
# :Copyright: © 2015 John Anderson
# :Copyright: © 2016, 2017, 2018, 2020 Lele Gaifax
#

import pytest

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
