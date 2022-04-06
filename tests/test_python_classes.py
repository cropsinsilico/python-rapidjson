# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Meagan Lang <langmm.astro@gmail.com>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest

import rapidjson as rj


@pytest.mark.parametrize(
    'value_str', (
        'example_function',
        'example_class',
        'example_instance',
    ))
def test_python_objects(dumps, loads, value_str, request):
    value = request.getfixturevalue(value_str)
    dumped = dumps(value)
    loaded = loads(dumped)
    assert loaded == value and type(loaded) is type(value)


@pytest.mark.parametrize('schema', (
    '{ "type": "instance", "class": "-YGG-eyJ0eXBlIjoiY2xhc3MifQ=='
    '-YGG-ZXhhbXBsZV9weXRob246RXhhbXBsZUNsYXNz-YGG-" }',
    {"type": "instance",
     "class": ("-YGG-eyJ0eXBlIjoiY2xhc3MifQ==-YGG-ZXhhbXBsZV9weXRob246RX"
               "hhbXBsZUNsYXNz-YGG-")}
))
def test_check_python_schema(schema, rapidjson_test_module_on_path):
    rj.Validator.check_schema(schema)
