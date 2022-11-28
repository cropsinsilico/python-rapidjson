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


# ///////////
# // Units //
# ///////////

class TestUnits:
    @pytest.fixture(scope="class", params=[
        ("kg", "kg"),
        ("°C", "degC"),
        ("g**2", "g**2"),
        ("km", "km"),
        ("s", "s"),
        ("km*s", "km*s")
    ])
    def options(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def x(self, options):
        return units.Units(options[0])

    def test_str(self, x, options):
        assert str(x) == options[1]

    @pytest.mark.parametrize('u', [
        'invalid'
    ])
    def test_error(self, u):
        with pytest.raises(units.UnitsError):
            units.Units(u)

    @pytest.mark.parametrize('u', [
        "", "n/a", None,
    ])
    def test_empty(self, u):
        x = units.Units(u)
        assert x.is_dimensionless()

    @pytest.mark.parametrize('u1,u2,eq', [
        ('m', 'meter', True),
        ('m', 'cm', False),
        ('', 'n/a', True)
    ])
    def test_equality(self, u1, u2, eq):
        x1 = units.Units(u1)
        x2 = units.Units(u2)
        assert (x1 == x2) == eq

    @pytest.mark.parametrize('u1,u2,compat', [
        ("cm", "m", True),
        ("cm", "s", False),
        ("hr", "d", True),
        ("d", "hr", True)
    ])
    def test_is_compatible(self, u1, u2, compat):
        units1 = units.Units(u1)
        units2 = units.Units(u2)
        assert units1.is_compatible(units2) == compat
        assert units2.is_compatible(units1) == compat


# //////////////
# // Quantity //
# //////////////

class TestQuantity:
    @pytest.fixture(scope="class")
    def cls(self):
        return units.Quantity

    @pytest.fixture(scope="class", params=[
        ({'args': (5.5, ),
          'units_equiv': 'n/a',
          'units_incompat': 'g'}),
        ({'args': (1.5, 'm'),
          'args_compat': (150.0, 'cm'),
          'units_equiv': 'meter',
          'units_incompat': 's'}),
        ({'args': (int(3), 'g'),
          'args_compat': (0.003, 'kg'),
          'units_equiv': 'grams',
          'units_incompat': 'radians'}),
        ({'args': (2, 'd'),
          'args_compat': (48, 'hr'),
          'units_equiv': 'days',
          'units_incompat': 'cm'}),
        ({'args': (int(1), "mol"),
          'args_compat': (int(1e6), "umol")}),
    ])
    def options(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def value(self):
        return 3

    @pytest.fixture(scope="class")
    def equals(self):
        def wrapped_equals(x, y):
            return (x == y)
        return wrapped_equals

    @pytest.fixture(scope="class")
    def assert_equal(self):
        def wrapped_assert_equal(x, y):
            assert x == y
        return wrapped_assert_equal

    @pytest.fixture(scope="class")
    def assert_close(self):
        def wrapped_assert_close(x, y):
            return np.isclose(x, y)
        return wrapped_assert_close

    @pytest.fixture(scope="class")
    def args(self, options):
        return options['args']

    @pytest.fixture(scope="class")
    def args_equiv(self, options):
        if 'units_equiv' not in options:
            pytest.skip("requires args_equiv")
        return (options['args'][0], options['units_equiv'])

    @pytest.fixture(scope="class")
    def args_compat(self, options):
        if 'args_compat' not in options:
            pytest.skip("requires args_compat")
        return options['args_compat']

    @pytest.fixture(scope="class")
    def units_compat(self, options):
        if 'args_compat' not in options:
            pytest.skip("requires args_compat")
        return options['args_compat'][1]

    @pytest.fixture(scope="class")
    def units_incompat(self, options):
        if 'units_incompat' not in options:
            pytest.skip("requires units_incompat")
        return options['units_incompat']

    @pytest.fixture(scope="class")
    def x(self, cls, args):
        return cls(*args)

    @pytest.fixture(scope="class")
    def x_equiv(self, cls, args_equiv):
        return cls(*args_equiv)

    @pytest.fixture(scope="class")
    def x_compat(self, cls, args_compat):
        return cls(*args_compat)

    @pytest.fixture(scope="class")
    def x_incompat(self, cls, args, units_incompat):
        return cls(args[0], units_incompat)

    def test_str(self, x):
        print(str(x))
        print(repr(x))
        print(np.array_repr(x))

    def test_format(self, x):
        print('{:f}'.format(x))
        print('%f' % (x))

    def test_pickle(self, x, assert_equal):
        import pickle
        dumped = pickle.dumps(x)
        loaded = pickle.loads(dumped)
        assert_equal(loaded, x)

    def test_is_compatible(self, x, x_equiv, x_compat, x_incompat,
                           units_compat, units_incompat):
        assert x.is_compatible(x)
        assert x.is_compatible(x_equiv)
        assert x.is_compatible(units_compat)
        assert x.is_compatible(x_compat)
        assert not x.is_compatible(x_incompat)
        assert not x.is_compatible(units_incompat)

    def test_equality(self, cls, x, x_equiv, x_incompat,
                      assert_equal, assert_close, equals):
        assert_equal(x, x)
        assert_close(x, x)
        assert_equal(x, x_equiv)
        assert_close(x, x_equiv)
        assert not equals(x, x_incompat)

    def test_conversion(self, assert_close, x, x_compat, units_compat):
        x2 = x.to(units_compat)
        assert_close(x2, x_compat)

    @pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
        (1.0, "m", 100.0, "cm", 2.0, "m"),
        (100.0, "cm", 1.0, "m", 200.0, "cm"),
    ])
    def test_add(self, cls, assert_equal, value,
                 v1, u1, v2, u2, vExp, uExp):
        v1 *= value
        v2 *= value
        vExp *= value
        x1 = cls(v1, u1)
        x2 = cls(v2, u2)
        exp = cls(vExp, uExp)
        assert_equal(x1 + x2, exp)
        assert (x2 + x1).is_equivalent(exp)
        with pytest.raises(units.UnitsError):
            x1 + 1
        with pytest.raises(units.UnitsError):
            1 + x1
        x1 += x2
        assert_equal(x1, exp)

    @pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
        (1.0, "m", 50.0, "cm", 0.5, "m"),
        (100.0, "cm", 0.5, "m", 50.0, "cm"),
    ])
    def test_subtract(self, cls, assert_equal, value,
                      v1, u1, v2, u2, vExp, uExp):
        v1 *= value
        v2 *= value
        vExp *= value
        x1 = cls(v1, u1)
        x2 = cls(v2, u2)
        exp = cls(vExp, uExp)
        assert_equal(x1 - x2, exp)
        with pytest.raises(units.UnitsError):
            x1 - 1
        with pytest.raises(units.UnitsError):
            1 - x1
        x1 -= x2
        assert_equal(x1, exp)

    @pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
        (1.0, "m", 50.0, "s", 50.0, "m*s"),
        (100.0, "cm", 0.5, "m", 5000.0, "cm**2"),
        (0.5, "m", 100.0, "cm", 0.5, "m**2"),
    ])
    def test_multiply(self, cls, assert_equal, value,
                      v1, u1, v2, u2, vExp, uExp):
        v1 *= value
        v2 *= value
        vExp *= value * value
        x1 = cls(v1, u1)
        x2 = cls(v2, u2)
        exp = cls(vExp, uExp)
        assert_equal(x1 * x2, exp)
        assert (x2 * x1).is_equivalent(exp)
        exp_scalar = cls(v1 * int(2), u1)
        assert_equal(int(2) * x1, exp_scalar)
        assert_equal(exp_scalar, x1 * int(2))
        x1 *= x2
        assert_equal(x1, exp)

    @pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
        (1.0, "m", 50.0, "s", 0.02, "m/s"),
        (100.0, "cm", 0.5, "m", 2.0, ""),
        (0.5, "m", 100.0, "cm", 0.5, ""),
        (24.0, "hr", 1.0, "day", 1, "n/a"),
    ])
    def test_divide(self, cls, assert_equal, value,
                    v1, u1, v2, u2, vExp, uExp):
        v1 *= value
        v2 *= value
        if isinstance(value, np.ndarray):
            vExp *= np.ones(value.shape, value.dtype)
        x1 = cls(v1, u1)
        x2 = cls(v2, u2)
        exp = cls(vExp, uExp)
        assert_equal(x1 / x2, exp)
        exp_scalar = cls(v1 / 2, u1)
        assert_equal(x1 / 2, exp_scalar)
        assert_equal(exp_scalar, x1 / 2)
        x1 /= x2
        assert_equal(x1, exp)

    @pytest.mark.parametrize('v1,u1,v2,u2,vExp,uExp', [
        (100.0, "cm", 0.4, "m", 20.0, "cm"),
        (0.5, "m", 100.0, "cm", 0.5, "m"),
        (0.402, "m**2", 100.0, "cm**2", 0.002, "m**2"),
    ])
    def test_modulus(self, cls, assert_equal, assert_close, value,
                     v1, u1, v2, u2, vExp, uExp):
        v1 *= value
        v2 *= value
        vExp *= value
        x1 = cls(v1, u1)
        x2 = cls(v2, u2)
        exp = cls(vExp, uExp)
        res = (x1 % x2)
        assert_close(res, exp)
        assert_close(x1 % x2, exp)
        exp_scalar = cls(v1 % 7, u1)
        assert_equal(x1 % 7, exp_scalar)
        assert_equal(exp_scalar, x1 % 7)
        x1 %= x2
        assert_close(x1, exp)

    def test_set_get_units(self, cls, args, units_compat, x_compat,
                           assert_close):
        x0 = cls(args[0])
        x1 = cls(*args)
        assert x0.units.is_dimensionless()
        uSet = units.Units(units_compat)
        x1.units = units_compat
        assert_close(x1, x_compat)
        assert x1.units == uSet

    def test_set_get_value(self, cls, assert_equal, x, args):
        v = args[0] * 100
        x1 = cls(*args)
        x1.value = v
        if len(args) == 1:
            exp = cls(v)
        else:
            exp = cls(v, args[1])
        assert_equal(x1, exp)
        assert_equal(x1.value, v)
        assert np.array(x1.value).dtype == np.array(v).dtype

    def test_serialize(self, x, assert_equal, loads, dumps):
        dumped = dumps(x)
        loaded = loads(dumped)
        assert_equal(loaded, x)


# ///////////////////
# // QuantityArray //
# ///////////////////

class TestQuantityArray(TestQuantity):
    @pytest.fixture(scope="class")
    def cls(self):
        return units.QuantityArray

    @pytest.fixture(scope="class", params=[
        ({'args': ([0, 1, 2], 'cm'),
          'args_compat': ([0.0, 0.01, 0.02], 'm'),
          'units_equiv': 'centimeter',
          'units_incompat': '°C'}),
        ({'args': (np.arange(3, dtype=np.float32), 'cm'),
          'args_compat': (np.float32(0.01) * np.arange(3, dtype=np.float32),
                          'm'),
          'units_equiv': 'centimeter',
          'units_incompat': '°F'}),
        ({'args': (np.arange(3, dtype=np.float64), 'kg'),
          'args_compat': (np.float64(1000.0) * np.arange(3, dtype=np.float64),
                          'g'),
          'units_equiv': 'kilogram',
          'units_incompat': '°F'}),
        ({'args': (np.arange(4, dtype=np.int8), 'g'),
          'args_compat': (0.001 * np.arange(4, dtype=np.int8), 'kg'),
          'units_equiv': 'grams',
          'units_incompat': 'seconds'}),
        ({'args': (np.int32(3), 'degC'),
          'args_compat': (37.4, '°F'),
          'units_equiv': '°C',
          'units_incompat': 'g'}),
        ({'args': (np.arange(4, dtype=int), "mol"),
          'args_compat': (int(1e6) * np.arange(4, dtype=int), "umol"),
          'units_equiv': 'mole',
          'units_incompat': 'cm'}),
    ])
    def options(self, request):
        return request.param

    @pytest.fixture(scope="class")
    def value(self):
        return np.arange(1, 11, dtype=np.float32).reshape((2, 5))

    @pytest.fixture(scope="class")
    def equals(self):
        def wrapped_equals(x, y):
            return np.array_equal(x, y)
        return wrapped_equals

    @pytest.fixture(scope="class")
    def assert_equal(self):
        def wrapped_assert_equal(x, y):
            if x.shape or y.shape:
                assert np.array_equal(x, y)
            else:
                assert x == y
        return wrapped_assert_equal

    @pytest.fixture(scope="class")
    def assert_close(self):
        def wrapped_assert_close(x, y):
            return np.allclose(x, y)
        return wrapped_assert_close

    def test_format(self):
        pytest.skip("no format for array")

    def test_array_properties(self, x, x_equiv, args):
        assert x.dtype == np.array(args[0]).dtype
        assert x.dtype == x_equiv.dtype
        assert x.ndim == np.array(args[0]).ndim
        assert x.ndim == x_equiv.ndim
        assert x.shape == np.array(args[0]).shape
        assert x.shape == x_equiv.shape

    def test_add_shape_mismatch(self, cls, assert_equal):
        x1 = cls(np.arange(6).reshape((3, 2)), 'cm')
        x2 = cls(np.arange(6), 'cm')
        with pytest.raises(ValueError):
            x1 + x2
        with pytest.raises(ValueError):
            x2 + x1

    def test_subtract_shape_mismatch(self, cls, assert_equal):
        x1 = cls(np.arange(6).reshape((3, 2)), 'cm')
        x2 = cls(np.arange(6), 'cm')
        with pytest.raises(ValueError):
            x1 - x2
        with pytest.raises(ValueError):
            x2 - x1

    def test_multiply_shape_mismatch(self, cls, assert_equal):
        x1 = cls(np.arange(6).reshape((3, 2)), 'cm')
        x2 = cls(np.arange(6), 'cm')
        with pytest.raises(ValueError):
            x1 * x2
        with pytest.raises(ValueError):
            x2 * x1

    def test_divide_shape_mismatch(self, cls, assert_equal):
        x1 = cls(np.arange(6).reshape((3, 2)), 'cm')
        x2 = cls(np.arange(6), 'cm')
        with pytest.raises(ValueError):
            x1 / x2
        with pytest.raises(ValueError):
            x2 / x1

    def test_modulus_shape_mismatch(self, cls, assert_equal):
        x1 = cls(np.arange(6).reshape((3, 2)), 'cm')
        x2 = cls(np.arange(6), 'cm')
        with pytest.raises(ValueError):
            x1 % x2
        with pytest.raises(ValueError):
            x2 % x1

    def test_set_get_item(self):
        arr = np.ones((3, 2))
        sub = np.ones(3)
        x1 = units.QuantityArray(arr, 'cm')
        xsub = units.QuantityArray(sub, 'cm')
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
    def test_trig(self, func, finv, x_in, x_out):
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

    @pytest.mark.parametrize('args,exp', [
        ((units.QuantityArray(np.arange(3), "m"), ),
         units.QuantityArray(np.arange(3), "m")),
        ((units.QuantityArray(np.arange(3), "m"), 1.0),
         [units.QuantityArray(np.arange(3), "m"), np.array([1.0])]),
    ])
    def test_atleast_1d(self, args, exp):
        res = np.atleast_1d(*args)
        if isinstance(exp, list):
            assert isinstance(res, list)
            assert len(res) == len(exp)
            for x, y in zip(res, exp):
                assert np.array_equal(x, y)
        else:
            assert np.array_equal(res, exp)

    @pytest.mark.parametrize('method', [
        'concatenate',
        'hstack',
        'vstack'
    ])
    @pytest.mark.parametrize('u1,u2,uExp,factor', [
        ("m", "m", "m", 1.0),
        ("m", "cm", "m", 0.01),
        ("cm", "m", "cm", 100.0),
    ])
    def test_concat(self, method, u1, u2, uExp, factor):
        arr1 = np.arange(3)
        arr2 = np.arange(3, 6)
        arr_exp = getattr(np, method)([arr1, factor * arr2])
        x1 = units.QuantityArray(arr1, u1)
        x2 = units.QuantityArray(arr2, u2)
        exp = units.QuantityArray(arr_exp, uExp)
        if method == 'vstack':
            exp = exp.reshape((2, 3))
        res = getattr(np, method)([x1, x2])
        assert np.array_equal(res, exp)
        assert res.units == exp.units
