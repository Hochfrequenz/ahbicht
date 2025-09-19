"""
This script is run in the tox 'json_schemas' environment.
It creates json schema files as described in the README.md in the same directory.
"""

import json
import pathlib
from typing import Any, Type

from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema  # type:ignore[import]
from pydantic import BaseModel

from ahbicht.json_serialization.tree_schema import TokenSchema  # , TreeSchema
from ahbicht.models.categorized_key_extract import CategorizedKeyExtract
from ahbicht.models.condition_nodes import EvaluatedFormatConstraintSchema
from ahbicht.models.content_evaluation_result import ContentEvaluationResultSchema
from ahbicht.models.evaluation_results import (
    AhbExpressionEvaluationResultSchema,
    FormatConstraintEvaluationResultSchema,
    RequirementConstraintEvaluationResultSchema,
)
from ahbicht.models.mapping_results import (
    ConditionKeyConditionTextMappingSchema,
    PackageKeyConditionExpressionMappingSchema,
)

schema_types: list[Type[Schema] | Type[BaseModel]] = [
    RequirementConstraintEvaluationResultSchema,  # marshmallow
    FormatConstraintEvaluationResultSchema,  # marshmallow
    EvaluatedFormatConstraintSchema,  # marshmallow
    AhbExpressionEvaluationResultSchema,  # marshmallow
    ConditionKeyConditionTextMappingSchema,  # marshmallow
    PackageKeyConditionExpressionMappingSchema,  #  marshmallow
    ContentEvaluationResultSchema,  # marshmallow
    TokenSchema,  #  marshmallow
    CategorizedKeyExtract,  # pydantic
    # TreeSchema
    # As of 2021-11 the TreeSchema fails, probably because of recursion or the lambda:
    # (<class 'AttributeError'>, AttributeError("'function' object has no attribute 'fields'"), ....)
]
json_schema = JSONSchema()
for schema_type in schema_types:
    this_directory = pathlib.Path(__file__).parent.absolute()
    file_name: str
    json_schema_dict: dict[str, Any]
    try:  # marshmallow json schema approach (deprecated - to be phased out one after another)
        file_name = schema_type.__name__ + ".json"  # pylint:disable=invalid-name
        schema_instance = schema_type()
        if "requirement_indicator" in schema_instance.fields:  # type:ignore[union-attr]
            # raises attribute error for pydantic classes
            # workaround for marshmallow: in the schemas we want the requirement indicator to appear as simple string
            # the schema used internally is just a workaround
            assert hasattr(schema_instance, "fields")
            assert hasattr(schema_instance, "load_fields")
            assert hasattr(schema_instance, "dump_fields")
            assert hasattr(schema_instance, "declared_fields")
            for field_dict in [
                schema_instance.fields,
                schema_instance.load_fields,
                schema_instance.dump_fields,
                schema_instance.declared_fields,
            ]:
                field_dict["requirement_indicator"] = fields.String(name="requirement_indicator")
        json_schema_dict = json_schema.dump(schema_instance)
    except AttributeError:  # means, we're creating a json schema from a pydantic class
        instance = schema_type()
        file_name = schema_type.__name__ + "Schema.json"  # other than for the marshmallow classes, we add 'Schema' here
        assert hasattr(instance, "model_json_schema")
        json_schema_dict = instance.model_json_schema()
    file_path = this_directory / file_name
    # We want our JSON schemas to be compatible with a typescript code generator:
    # https://github.com/bcherny/json-schema-to-typescript/
    # However there's an unresolved bug: The root level of the schema must not contain any '$ref' key.
    # https://github.com/bcherny/json-schema-to-typescript/issues/132
    # The workaround goes like this:
    result = json_schema_dict.copy()
    result["type"] = "object"
    result["title"] = schema_type.__name__
    if "$ref" in result:
        result["properties"] = {"$ref": result["$ref"] + "/properties"}
        del result["$ref"]
    with open(file_path, "w", encoding="utf-8") as json_schema_file:
        json.dump(result, json_schema_file, ensure_ascii=False, sort_keys=True, indent=4)
