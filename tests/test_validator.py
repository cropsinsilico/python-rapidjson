# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Validator class tests
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest

import rapidjson as rj


def test_invalid_schema():
    pytest.raises(rj.JSONDecodeError, rj.Validator, '')
    pytest.raises(rj.JSONDecodeError, rj.Validator, '"')


def test_invalid_json():
    validate = rj.Validator('""')
    pytest.raises(rj.JSONDecodeError, validate, '')
    pytest.raises(rj.JSONDecodeError, validate, '"')
    pytest.raises(rj.JSONDecodeError, validate.validate, '')
    pytest.raises(rj.JSONDecodeError, validate.validate, '"')


@pytest.mark.parametrize('schema,json', (
    ('{ "type": ["number", "string"] }', '42'),
    ('{ "type": ["number", "string"] }',
     '"Life, the universe, and everything"'),
    ({"type": ["number", "string"]}, 42),
    ({"type": ["number", "string"]}, "Life, the universe, and everything"),
))
def test_valid(schema, json):
    validate = rj.Validator(schema)
    validate(json)
    validate.validate(json)
    rj.validate(json, schema)


@pytest.mark.parametrize('schema,json,details', (
    ('{ "type": ["number", "string"] }',
     '["Life", "the universe", "and everything"]',
     ('type', '#', '#'),
     ),
))
def test_invalid(schema, json, details):
    validate = rj.Validator(schema)
    with pytest.raises(ValueError) as error:
        validate(json)
    assert error.value.args == details
    with pytest.raises(ValueError) as error:
        validate.validate(json)
    assert error.value.args == details
    with pytest.raises(ValueError) as error:
        rj.validate(json, schema)
    assert error.value.args == details


# See: https://spacetelescope.github.io/understanding-json-schema/
#   reference/object.html#pattern-properties
@pytest.mark.parametrize('schema', [
    rj.dumps({
        "type": "object",
        "patternProperties": {
            "^S_": {"type": "string"},
            "^I_": {"type": "integer"}
        },
        "additionalProperties": False
    }),
])
@pytest.mark.parametrize('json', [
     '{"I_0": 23}',
     '{"S_1": "the quick brown fox jumps over the lazy dog"}',
     pytest.param('{"I_2": "A string"}', marks=pytest.mark.xfail),
     pytest.param('{"keyword": "value"}', marks=pytest.mark.xfail),
])
def test_additional_and_pattern_properties_valid(schema, json):
    validate = rj.Validator(schema)
    validate(json)
    validate.validate(json)
    rj.validate(json, schema)


@pytest.mark.parametrize('schema,standard', (
    ('{ "type": ["number", "string"] }', True),
    ({"type": ["number", "string"]}, True),
    ('{ "type": "instance" }', False),
    ({"type": "instance"}, False)
))
def test_check_schema(schema, standard):
    rj.Validator.check_schema(schema)
    if standard:
        rj.Validator.check_schema(schema, json_standard=True)
    else:
        with pytest.raises(rj.ValidationError):
            rj.Validator.check_schema(schema, json_standard=True)


@pytest.mark.parametrize('schema,details', (
    ('{ "type": 3 }', ('schema', '#', '#')),
    ({"type": 3}, ('schema', '#', '#')),
))
def test_check_schema_invalid(schema, details):
    with pytest.raises(ValueError) as error:
        rj.Validator.check_schema(schema)
    assert error.value.args == details


def test_get_metaschema():
    rj.get_metaschema()
