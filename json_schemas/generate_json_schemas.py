"""
This script is run in the tox 'json_schemas' environment.
It creates json schema files as described in the README.md in the same directory.
"""

import json
import pathlib
from typing import Any, Type

from pydantic import BaseModel, TypeAdapter

from ahbicht.models.categorized_key_extract import CategorizedKeyExtract
from ahbicht.models.condition_nodes import EvaluatedFormatConstraint
from ahbicht.models.content_evaluation_result import ContentEvaluationResult
from ahbicht.models.evaluation_results import (
    AhbExpressionEvaluationResult,
    FormatConstraintEvaluationResult,
    RequirementConstraintEvaluationResult,
)
from ahbicht.models.mapping_results import ConditionKeyConditionTextMapping, PackageKeyConditionExpressionMapping

schema_types: list[Type[TypeAdapter] | Type[BaseModel]] = [
    RequirementConstraintEvaluationResult,  # pydantic
    FormatConstraintEvaluationResult,  # pydantic
    EvaluatedFormatConstraint,  # pydantic
    AhbExpressionEvaluationResult,  # pydantic
    ConditionKeyConditionTextMapping,  # pydantic
    PackageKeyConditionExpressionMapping,  #  pydantic
    CategorizedKeyExtract,  # pydantic
    ContentEvaluationResult,  # pydantic
]
for schema_type in schema_types:
    this_directory = pathlib.Path(__file__).parent.absolute()
    file_name: str
    json_schema_dict: dict[str, Any]
    file_name = schema_type.__name__ + "Schema.json"
    assert hasattr(schema_type, "model_json_schema")
    json_schema_dict = schema_type.model_json_schema()
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
