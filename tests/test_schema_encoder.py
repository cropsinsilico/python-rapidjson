# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Meagan Lang <langmm.astro@gmail.com>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest
import numpy as np

import rapidjson as rj


@pytest.mark.parametrize('value,schema', (
    (True, {"type": "boolean"}),
    (None, {"type": "null"}),
    (int(42), {"type": "integer"}),
    (42.0, {"type": "number"}),
    ("hello", {"type": "string"}),
    ([int(1), "hello"], {"type": "array",
                         "items": [{"type": "integer"},
                                   {"type": "string"}]}),
    ({"a": int(3), "b": "hello"},
     {"type": "object", "properties": {
         "a": {"type": "integer"},
         "b": {"type": "string"}}})
))
def test_encode_schema(value, schema):
    assert rj.encode_schema(value) == schema


@pytest.mark.parametrize('value_str,schema', (
    ('example_function', {"type": "function"}),
    ('example_class', {"type": "class"}),
    ('example_instance', {"type": "instance"})
))
def test_encode_schema_python(value_str, schema, request):
    value = request.getfixturevalue(value_str)
    assert rj.encode_schema(value) == schema


@pytest.mark.parametrize('np_type,schema', (
    (np.float16, {"subtype": "float", "precision": 2}),
    (np.float32, {"subtype": "float", "precision": 4}),
    (np.int8, {"subtype": "int", "precision": 1}),
    (np.int16, {"subtype": "int", "precision": 2}),
    (np.int32, {"subtype": "int", "precision": 4}),
    (np.int64, {"subtype": "int", "precision": 8}),
    (np.uint8, {"subtype": "uint", "precision": 1}),
    (np.uint16, {"subtype": "uint", "precision": 2}),
    (np.uint32, {"subtype": "uint", "precision": 4}),
    (np.uint64, {"subtype": "uint", "precision": 8}),
    (np.complex64, {"subtype": "complex", "precision": 8}),
    (np.complex128, {"subtype": "complex", "precision": 16})
))
def test_encode_schema_scalars(np_type, schema):
    schema["type"] = "scalar"
    value = np_type(3)
    assert rj.encode_schema(value) == schema


@pytest.mark.parametrize('np_type,schema', (
    (np.float64, {"type": "number"}),
    # (np.int32, {"type": "integer"}),
    # (np.int64, {"type": "integer"}),
    # (np.uint32, {"type": "integer"}),
    # (np.uint64, {"type": "integer"}),
))
def test_encode_schema_castable(np_type, schema):
    value = np_type(3)
    assert rj.encode_schema(value) == schema


@pytest.mark.parametrize('np_type,schema', (
    (np.float16, {"subtype": "float", "precision": 2}),
    (np.float32, {"subtype": "float", "precision": 4}),
    (np.float64, {"subtype": "float", "precision": 8}),
    (np.int8, {"subtype": "int", "precision": 1}),
    (np.int16, {"subtype": "int", "precision": 2}),
    (np.int32, {"subtype": "int", "precision": 4}),
    (np.int64, {"subtype": "int", "precision": 8}),
    (np.uint8, {"subtype": "uint", "precision": 1}),
    (np.uint16, {"subtype": "uint", "precision": 2}),
    (np.uint32, {"subtype": "uint", "precision": 4}),
    (np.uint64, {"subtype": "uint", "precision": 8}),
    (np.complex64, {"subtype": "complex", "precision": 8}),
    (np.complex128, {"subtype": "complex", "precision": 16})
))
def test_encode_schema_arrays(np_type, schema):
    schema.update({"type": "ndarray", "shape": [3, 4]})
    value = np.ones((3, 4), dtype=np_type)
    assert rj.encode_schema(value) == schema
