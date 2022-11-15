# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Meagan Lang <langmm.astro@gmail.com>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest
import numpy as np
import rapidjson as rj


@pytest.mark.parametrize(
    'np_type', (
        np.float16, np.float32,
        np.int8, np.int16,
        np.uint8, np.uint16,
        np.complex64, np.complex128,
    ))
def test_scalars(dumps, loads, np_type):
    value = np_type(3)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded.dtype == value.dtype
    assert (loaded == value and type(loaded) is type(value)
            and loaded.dtype == value.dtype)


@pytest.mark.parametrize(
    'np_type,result', [
        (np.float16, 3.0),
        (np.float32, 3.0),
        (np.int8, 3),
        (np.int16, 3),
        (np.uint8, 3),
        (np.uint16, 3),
        (np.complex64, [3.0, 0.0]),
        (np.complex128, [3.0, 0.0]),
    ])
def test_scalars_as_pure_json(dumps, loads, np_type, result):
    value = np_type(3)
    dumped = dumps(value, yggdrasil_mode=rj.YM_READABLE)
    loaded = loads(dumped)
    assert loaded == result
    assert rj.as_pure_json(value) == result


@pytest.mark.parametrize('type_str,values', [
    ('S1', [b'1', b'2']),
    ('U5', ['hello', 'world']),
])
def test_strings(dumps, loads, type_str, values):
    value = np.array(values, dtype=type_str)
    dumped = dumps(value)
    loaded = loads(dumped)
    np.testing.assert_equal(loaded, value)


@pytest.mark.parametrize(
    'np_type', (
        np.float64,
        np.int32, np.int64,
        np.uint32, np.uint64,
    ))
def test_scalars_castable(dumps, loads, np_type):
    value = np_type(3)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded == value


@pytest.mark.parametrize(
    'np_type', (
        np.float16, np.float32, np.float64,
        np.int8, np.int16, np.int32, np.int64,
        np.uint8, np.uint16, np.uint32, np.uint64,
        np.complex64, np.complex128,
    ))
def test_arrays(dumps, loads, np_type):
    value = np.arange(3, dtype=np_type)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert type(loaded) is type(value) and loaded.dtype == value.dtype
    np.testing.assert_equal(loaded, value)


@pytest.mark.parametrize(
    'np_type,result', [
        (np.float16, [0.0, 1.0, 2.0]),
        (np.float32, [0.0, 1.0, 2.0]),
        (np.float64, [0.0, 1.0, 2.0]),
        (np.int8, [0, 1, 2]),
        (np.int16, [0, 1, 2]),
        (np.int32, [0, 1, 2]),
        (np.int64, [0, 1, 2]),
        (np.uint8, [0, 1, 2]),
        (np.uint16, [0, 1, 2]),
        (np.uint32, [0, 1, 2]),
        (np.uint64, [0, 1, 2]),
        (np.complex64, [[0, 0], [1, 0], [2, 0]]),
        (np.complex128, [[0, 0], [1, 0], [2, 0]]),
    ])
def test_arrays_as_pure_json(dumps, loads, np_type, result):
    value = np.arange(3, dtype=np_type)
    dumped = dumps(value, yggdrasil_mode=rj.YM_READABLE)
    loaded = loads(dumped)
    assert loaded == result
    assert rj.as_pure_json(value) == result


def test_structured_array(dumps, loads):
    value = np.array([('Rex', 9, 81.0), ('Fido', 3, 27.0)],
                     dtype=[('name', 'U10'), ('age', 'i4'), ('weight', 'f4')])
    dumped = dumps(value)
    loaded = loads(dumped)
    assert type(loaded) is type(value) and loaded.dtype == value.dtype
    np.testing.assert_equal(loaded, value)


def test_pandas(dumps, loads):
    try:
        import pandas as pd
    except ImportError:
        pytest.skip("requires pandas")
    value = np.array([('Rex', 9, 81.0, b'red'), ('Fido', 3, 27.0, b'green')],
                     dtype=[('name', 'U4'), ('age', 'i4'),
                            ('weight', 'f4'), ('color', 'S5')])
    value_pd = pd.DataFrame(value)
    dumped = dumps(value_pd)
    loaded = loads(dumped)
    assert type(loaded) is type(value) and loaded.dtype == value.dtype
    np.testing.assert_equal(loaded, value)
