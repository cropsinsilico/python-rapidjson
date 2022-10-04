# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Meagan Lang <langmm.astro@gmail.com>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest
import numpy as np


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


@pytest.mark.parametrize('type_str,values', [
    ('S1', [b'1', b'2']),
    ('U5', ['hello', 'world']),
])
def test_strings(dumps, loads, type_str, values):
    value = np.array(values, dtype=type_str)
    import gc
    gc.collect()
    print('HERE1')
    dumped = dumps(value)
    gc.collect()
    print('HERE2')
    print(dumped)
    loaded = loads(dumped)
    gc.collect()
    print('HERE3')
    print(loaded)
    assert np.array_equal(loaded, value)


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
