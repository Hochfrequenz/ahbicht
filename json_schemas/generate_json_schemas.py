"""
This script is run in the tox 'json_schemas' environment.
It creates json schema files as described in the README.md in the same directory.
"""

import json
import pathlib
from typing import List, Type

from marshmallow import Schema, fields
from marshmallow_jsonschema import JSONSchema  # type:ignore[import]

from ahbicht.content_evaluation.categorized_key_extract import CategorizedKeyExtractSchema
from ahbicht.content_evaluation.content_evaluation_result import ContentEvaluationResultSchema
from ahbicht.evaluation_results import (
    AhbExpressionEvaluationResultSchema,
    FormatConstraintEvaluationResultSchema,
    RequirementConstraintEvaluationResultSchema,
)
from ahbicht.expressions.condition_nodes import EvaluatedFormatConstraintSchema
from ahbicht.json_serialization.tree_schema import TokenSchema  # , TreeSchema
from ahbicht.mapping_results import ConditionKeyConditionTextMappingSchema, PackageKeyConditionExpressionMappingSchema

schema_types: List[Type[Schema]] = [
    RequirementConstraintEvaluationResultSchema,
    FormatConstraintEvaluationResultSchema,
    EvaluatedFormatConstraintSchema,
    AhbExpressionEvaluationResultSchema,
    ConditionKeyConditionTextMappingSchema,
    PackageKeyConditionExpressionMappingSchema,
    ContentEvaluationResultSchema,
    TokenSchema,
    CategorizedKeyExtractSchema,
    # TreeSchema
    # As of 2021-11 the TreeSchema fails, probably because of recursion or the lambda:
    # (<class 'AttributeError'>, AttributeError("'function' object has no attribute 'fields'"), ....)
]
json_schema = JSONSchema()
for schema_type in schema_types:
    this_directory = pathlib.Path(__file__).parent.absolute()
    file_name = schema_type.__name__ + ".json"  # pylint:disable=invalid-name
    file_path = this_directory / file_name
    schema_instance = schema_type()
    if "requirement_indicator" in schema_instance.fields:
        # workaround: in the schemas we want the requirement indicator to appear as simple string
        # the schema used internally is just a workaround
        for field_dict in [
            schema_instance.fields,
            schema_instance.load_fields,
            schema_instance.dump_fields,
            schema_instance.declared_fields,
        ]:
            field_dict["requirement_indicator"] = fields.String(name="requirement_indicator")

    json_schema_dict = json_schema.dump(schema_instance)
    # We want our JSON schemas to be compatible with a typescript code generator:
    # https://github.com/bcherny/json-schema-to-typescript/
    # However there's an unresolved bug: The root level of the schema must not contain any '$ref' key.
    # https://github.com/bcherny/json-schema-to-typescript/issues/132
    # The workaround goes like this:
    result = json_schema_dict.copy()
    result["type"] = "object"
    result["title"] = schema_type.__name__
    result["properties"] = {"$ref": result["$ref"] + "/properties"}
    del result["$ref"]

    with open(file_path, "w", encoding="utf-8") as json_schema_file:
        json.dump(result, json_schema_file, ensure_ascii=False, sort_keys=True, indent=4)
