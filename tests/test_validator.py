# -*- coding: utf-8 -*-
# :Project:   python-rapidjson -- Validator class tests
# :Author:    Lele Gaifax <lele@metapensiero.it>
# :License:   MIT License
# :Copyright: © 2017, 2019, 2020 Lele Gaifax
#

import pytest

import rapidjson as rj
import numpy as np


def test_invalid_schema():
    pytest.raises(rj.JSONDecodeError, rj.Validator, '')
    pytest.raises(rj.JSONDecodeError, rj.Validator, '"')


def test_invalid_json():
    validate = rj.Validator('{"type": "number"}')
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
    ({"type": "string"}, '0000000'),
))
def test_valid(schema, json):
    validate = rj.Validator(schema)
    validate(json)
    validate.validate(json)
    rj.validate(json, schema)


@pytest.mark.parametrize('schema,json,details', (
    ('{ "type": ["number", "string"] }',
     '["Life", "the universe", "and everything"]',
     ('{\n'
      + '    "message": "Property has a type \'array\' that is not in the'
      + ' following list: \'[\\"string\\",\\"number\\"]\'.",\n'
      + '    "instanceRef": "#",\n'
      + '    "schemaRef": "#"\n'
      + '}', )
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


@pytest.mark.parametrize('schema,json,details', (
    ({"type": "object",
      "properties": {"a": {"type": "string"},
                     "b": {"type": "string",
                           "deprecated": True}}},
     {"a": "foo", "b": "bar"},
     ('{\n'
      + '    "message": "Property is being deprecated.",\n'
      + '    "instanceRef": "#/b",\n'
      + '    "schemaRef": "#/properties/b"\n'
      + '}', )
     ),
))
def test_warning(schema, json, details):
    validate = rj.Validator(schema)
    with pytest.warns(rj.ValidationWarning) as record:
        validate(json)
    print(dir(record))
    assert len(record) == 1
    assert record[0].message.args == details
    with pytest.warns(rj.ValidationWarning) as record:
        validate.validate(json)
    assert len(record) == 1
    assert record[0].message.args == details
    with pytest.warns(rj.ValidationWarning) as record:
        rj.validate(json, schema)
    assert len(record) == 1
    assert record[0].message.args == details


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
    ('{ "type": 3 }',
     ('{\n'
      '    "message": "Property did not match any of the sub-schemas'
      ' specified by \'anyOf\', refer to following errors.",\n'
      '    "instanceRef": "#/type",\n'
      '    "schemaRef": "#/properties/type",\n'
      '    "errors": [\n'
      '        {\n'
      '            "message": "Property has a value that is not one of its'
      ' allowed enumerated values: [\\"array\\",\\"boolean\\",'
      '\\"integer\\",\\"null\\",\\"number\\",\\"object\\",\\"string\\",'
      '\\"1darray\\",\\"any\\",\\"bytes\\",\\"class\\",\\"complex\\",'
      '\\"float\\",\\"function\\",\\"instance\\",\\"int\\",\\"ndarray\\",'
      '\\"obj\\",\\"ply\\",\\"scalar\\",\\"schema\\",\\"uint\\",'
      '\\"unicode\\"].",\n'
      '            "instanceRef": "#/type",\n'
      '            "schemaRef": "#/definitions/simpleTypes"\n'
      '        },\n'
      '        {\n'
      '            "message": "Property has a type \'integer\' that is not'
      ' in the following list: \'[\\"array\\"]\'.",\n'
      '            "instanceRef": "#/type",\n'
      '            "schemaRef": "#/properties/type/anyOf/1"\n'
      '        }\n'
      '    ]\n'
      '}', )),
    ({"type": 3},
     ('{\n'
      '    "message": "Property did not match any of the sub-schemas'
      ' specified by \'anyOf\', refer to following errors.",\n'
      '    "instanceRef": "#/type",\n'
      '    "schemaRef": "#/properties/type",\n'
      '    "errors": [\n'
      '        {\n'
      '            "message": "Property has a value that is not one of its'
      ' allowed enumerated values: [\\"array\\",\\"boolean\\",\\"integer\\",'
      '\\"null\\",\\"number\\",\\"object\\",\\"string\\",\\"1darray\\",'
      '\\"any\\",\\"bytes\\",\\"class\\",\\"complex\\",\\"float\\",'
      '\\"function\\",\\"instance\\",\\"int\\",\\"ndarray\\",\\"obj\\",'
      '\\"ply\\",\\"scalar\\",\\"schema\\",\\"uint\\",\\"unicode\\"].",\n'
      '            "instanceRef": "#/type",\n'
      '            "schemaRef": "#/definitions/simpleTypes"\n'
      '        },\n'
      '        {\n'
      '            "message": "Property has a type \'integer\' that is not'
      ' in the following list: \'[\\"array\\"]\'.",\n'
      '            "instanceRef": "#/type",\n'
      '            "schemaRef": "#/properties/type/anyOf/1"\n'
      '        }\n'
      '    ]\n'
      '}', )),
))
def test_check_schema_invalid(schema, details):
    with pytest.raises(ValueError) as error:
        rj.Validator.check_schema(schema)
    assert error.value.args[0] == details[0]


def test_get_metaschema():
    rj.get_metaschema()


@pytest.mark.parametrize('schemaA,schemaB,details', (
    ('{"type": "number"}', '{"type": ["number", "schema"]}', None),
    ('{"type": "number"}', '{"type": "schema"}',
     ('{\n'
      '    "message": "Incompatible schema property \'type\': [\\"number\\"] '
      'vs [\\"schema\\"].",\n'
      '    "instanceRef": "#",\n'
      '    "schemaRef": "#"\n'
      '}', )),
))
def test_compare_schemas(schemaA, schemaB, details):
    assert rj.compare_schemas(schemaA, schemaA)
    if details is None:
        assert rj.compare_schemas(schemaA, schemaB)
    else:
        assert not rj.compare_schemas(schemaA, schemaB, dont_raise=True)
        with pytest.raises(rj.ComparisonError) as error:
            rj.compare_schemas(schemaA, schemaB)
        assert error.value.args == details


@pytest.mark.parametrize('schema,result,details', (
    ({"type": "number"}, 0.0, None),
    ({"type": "integer"}, 0, None),
    ({"type": "boolean"}, True, None),
    ({"type": "object"}, {}, None),
    ({"type": "object",
      "properties": {
          "a": {"type": "integer"}
      }},
     {"a": 0}, None),
    ({"type": "object",
      "additionalProperties": {
          "type": "integer"
      },
      "minProperties": 3},
     {"a": 0, "b": 0, "c": 0, "d": 0}, None),
    ({"type": "array"}, [], None),
    ({"type": "array",
      "items": [
          {"type": "integer"}
      ]},
     [0], None),
    ({"type": "array",
      "items": {
          "type": "integer"
      },
      "minItems": 3},
     [0, 0, 0, 0], None),
    ({"type": "1darray"},
     np.zeros((2, ), dtype=np.int32), None)
))
def test_generate_data(schema, result, details):
    if details is None:
        if isinstance(result, np.ndarray):
            np.testing.assert_array_equal(rj.generate_data(schema),
                                          result)
        else:
            assert rj.generate_data(schema) == result
    else:
        with pytest.raises(rj.GenerateError) as error:
            rj.generate_data(schema)
        assert error.value.args == details
