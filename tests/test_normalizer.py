# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Normalizer class tests
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest

import rapidjson as rj


def test_invalid_schema():
    pytest.raises(rj.JSONDecodeError, rj.Normalizer, '')
    pytest.raises(rj.JSONDecodeError, rj.Normalizer, '"')


def test_invalid_json():
    normalizer = rj.Normalizer('""')
    pytest.raises(rj.JSONDecodeError, normalizer, '')
    pytest.raises(rj.JSONDecodeError, normalizer, '"')
    pytest.raises(rj.JSONDecodeError, normalizer.normalize, '')
    pytest.raises(rj.JSONDecodeError, normalizer.normalize, '"')
    pytest.raises(rj.JSONDecodeError, normalizer.validate, '')
    pytest.raises(rj.JSONDecodeError, normalizer.validate, '"')


@pytest.mark.parametrize('schema,json,normalized', (
    ('{ "type": "object", '
     '  "properties": { "color": { "default": "purple"} },'
     '  "required": ["color"] }', '{}', {"color": "purple"}),
    ({"type": "object",
      "properties": {"color": {"default": "purple"}},
      "required": ["color"]}, {}, {"color": "purple"}),
))
def test_normalize(schema, json, normalized):
    normalizer = rj.Normalizer(schema)
    assert(normalizer(json) == normalized)
    assert(normalizer.normalize(json) == normalized)
    normalizer.validate(json)


@pytest.mark.parametrize('schema,json,details', (
    ('{ "type": ["number", "string"] }',
     '["Life", "the universe", "and everything"]',
     ('type', '#', '#'),
     ),
))
def test_invalid(schema, json, details):
    normalizer = rj.Normalizer(schema)
    with pytest.raises(ValueError) as error:
        normalizer(json)
    assert error.value.args == details
    with pytest.raises(ValueError) as error:
        normalizer.normalize(json)
    assert error.value.args == details
    with pytest.raises(ValueError) as error:
        normalizer.validate(json)
    assert error.value.args == details
