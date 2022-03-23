# type:ignore
# MyPy will (reproducible) run in an infinite loop if you remove the type ignore in the test! We literally killed it 💀
"""
Tests that the parsed trees are JSON serializable
"""

import pytest  # type:ignore[import]
from lark import Token, Tree

from ahbicht.expressions.ahb_expression_parser import parse_ahb_expression_to_single_requirement_indicator_expressions
from ahbicht.expressions.condition_expression_parser import parse_condition_expression_to_tree
from ahbicht.expressions.expression_resolver import parse_expression_including_unresolved_subexpressions
from ahbicht.json_serialization.concise_condition_key_tree_schema import ConciseConditionKeyTreeSchema
from ahbicht.json_serialization.concise_tree_schema import ConciseTreeSchema
from ahbicht.json_serialization.tree_schema import TreeSchema
from unittests.test_json_serialization import _test_serialization_roundtrip  # type:ignore[import]

pytestmark = pytest.mark.asyncio


class TestTreeSchemas:
    """
    This class tests the serialization of trees (because there are multiple schemas for it).
    All the other (non tree) serialization tests happen in :class:`TestJsonSerialization`.
    """

    @pytest.mark.parametrize(
        "tree, expected_json_dict",
        [
            pytest.param(
                Tree(
                    "or_composition",
                    [
                        Tree("condition_key", [Token("INT", "53")]),
                        Tree(
                            "and_composition",
                            [Tree("condition_key", [Token("INT", "1")]), Tree("condition_key", [Token("INT", "2")])],
                        ),
                    ],
                ),
                {
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "children": [{"token": {"type": "INT", "value": "53"}, "tree": None}],
                                "type": "condition_key",
                            },
                        },
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {
                                        "token": None,
                                        "tree": {
                                            "children": [{"token": {"type": "INT", "value": "1"}, "tree": None}],
                                            "type": "condition_key",
                                        },
                                    },
                                    {
                                        "token": None,
                                        "tree": {
                                            "children": [{"token": {"type": "INT", "value": "2"}, "tree": None}],
                                            "type": "condition_key",
                                        },
                                    },
                                ],
                                "type": "and_composition",
                            },
                        },
                    ],
                    "type": "or_composition",
                },
            )
        ],
    )
    def test_tree_serialization(self, tree: Tree, expected_json_dict: dict):
        _test_serialization_roundtrip(tree, TreeSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "condition_string, expected_json_dict",
        [
            pytest.param(
                "Muss [2] U ([3] O [4])[901] U [555]",
                {
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {"token": {"type": "MODAL_MARK", "value": "Muss"}, "tree": None},
                                    {
                                        "token": {
                                            "type": "CONDITION_EXPRESSION",
                                            "value": " [2] U ([3] O [4])[901] U [555]",
                                        },
                                        "tree": None,
                                    },
                                ],
                                "type": "single_requirement_indicator_expression",
                            },
                        }
                    ],
                    "type": "ahb_expression",
                },
            )
        ],
    )
    def test_single_requirement_indicator_expression_serialization(
        self, condition_string: str, expected_json_dict: dict
    ):
        tree = parse_ahb_expression_to_single_requirement_indicator_expressions(condition_string)
        _test_serialization_roundtrip(tree, TreeSchema(), expected_json_dict)

    @pytest.mark.parametrize(
        "condition_expression, expected_compact_json_dict",
        [
            pytest.param(
                "[1] U ([2] O [3])[901]",
                {"and_composition": ["1", {"then_also_composition": [{"or_composition": ["2", "3"]}, "901"]}]},
            ),
            pytest.param(
                "[3] U ([2] O [3] U [77] X [99][502])[901]",
                {
                    "and_composition": [
                        "3",
                        {
                            "then_also_composition": [
                                {
                                    "or_composition": [
                                        "2",
                                        {
                                            "xor_composition": [
                                                {"and_composition": ["3", "77"]},
                                                {"then_also_composition": ["99", "502"]},
                                            ]
                                        },
                                    ]
                                },
                                "901",
                            ]
                        },
                    ]
                },
            ),
        ],
    )
    def test_concise_tree_serialization_behaviour_for_condition_expressions(
        self, condition_expression: str, expected_compact_json_dict: dict
    ):
        tree = parse_condition_expression_to_tree(condition_expression)
        json_dict = ConciseTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict

    @pytest.mark.parametrize(
        "ahb_expression, expected_compact_json_dict",
        [
            pytest.param(
                "Muss [1] U ([2] O [3])[901]",
                {
                    "ahb_expression": [
                        {
                            "single_requirement_indicator_expression": [
                                "Muss",
                                {
                                    "and_composition": [
                                        "1",
                                        {"then_also_composition": [{"or_composition": ["2", "3"]}, "901"]},
                                    ]
                                },
                            ]
                        }
                    ]
                },
            ),
            pytest.param(
                "Soll [3] U ([2] O [3] U [77] X [99][502])[901] Kann [43]",
                {
                    "ahb_expression": [
                        {
                            "single_requirement_indicator_expression": [
                                "Soll",
                                {
                                    "and_composition": [
                                        "3",
                                        {
                                            "then_also_composition": [
                                                {
                                                    "or_composition": [
                                                        "2",
                                                        {
                                                            "xor_composition": [
                                                                {"and_composition": ["3", "77"]},
                                                                {"then_also_composition": ["99", "502"]},
                                                            ]
                                                        },
                                                    ]
                                                },
                                                "901",
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                        {"single_requirement_indicator_expression": ["Kann", "43"]},
                    ]
                },
            ),
        ],
    )
    async def test_concise_tree_serialization_behaviour_for_ahb_expressions(
        self, ahb_expression: str, expected_compact_json_dict: dict
    ):
        tree = await parse_expression_including_unresolved_subexpressions(ahb_expression)
        json_dict = ConciseTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict

    @pytest.mark.parametrize(
        "expression, expected_compact_json_dict",
        [
            pytest.param(
                "[53] O ([1] U [2])",
                {
                    "children": [
                        {
                            "token": {
                                "value": "53",
                                "type": "condition_key",
                            },
                            "tree": None,
                        },
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {
                                        "token": {
                                            "value": "1",
                                            "type": "condition_key",
                                        },
                                        "tree": None,
                                    },
                                    {
                                        "token": {
                                            "value": "2",
                                            "type": "condition_key",
                                        },
                                        "tree": None,
                                    },
                                ],
                                "type": "and_composition",
                            },
                        },
                    ],
                    "type": "or_composition",
                },
            )
        ],
    )
    def test_concise_condition_key_tree_serialization_behaviour_for_condition_expressions(
        self, expression: str, expected_compact_json_dict: dict
    ):
        tree = parse_condition_expression_to_tree(expression)
        json_dict = ConciseConditionKeyTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict

    @pytest.mark.parametrize(
        "expression, expected_compact_json_dict",
        [
            pytest.param(
                "Muss [1] U ([2] O [3])[901]",
                {
                    "type": "ahb_expression",
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "type": "Muss",
                                "children": [
                                    {
                                        "token": None,
                                        "tree": {
                                            "type": "and_composition",
                                            "children": [
                                                {"token": {"value": "1", "type": "condition_key"}, "tree": None},
                                                {
                                                    "token": None,
                                                    "tree": {
                                                        "type": "then_also_composition",
                                                        "children": [
                                                            {
                                                                "token": None,
                                                                "tree": {
                                                                    "type": "or_composition",
                                                                    "children": [
                                                                        {
                                                                            "token": {
                                                                                "value": "2",
                                                                                "type": "condition_key",
                                                                            },
                                                                            "tree": None,
                                                                        },
                                                                        {
                                                                            "token": {
                                                                                "value": "3",
                                                                                "type": "condition_key",
                                                                            },
                                                                            "tree": None,
                                                                        },
                                                                    ],
                                                                },
                                                            },
                                                            {
                                                                "token": {"value": "901", "type": "condition_key"},
                                                                "tree": None,
                                                            },
                                                        ],
                                                    },
                                                },
                                            ],
                                        },
                                    },
                                ],
                            },
                        }
                    ],
                },
            ),
            pytest.param(
                "Soll [3] U ([2] O [3] U [77] X [99][502])[901] Kann [43]",
                {
                    "children": [
                        {
                            "token": None,
                            "tree": {
                                "children": [
                                    {
                                        "token": None,
                                        "tree": {
                                            "children": [
                                                {"token": {"value": "3", "type": "condition_key"}, "tree": None},
                                                {
                                                    "token": None,
                                                    "tree": {
                                                        "children": [
                                                            {
                                                                "token": None,
                                                                "tree": {
                                                                    "children": [
                                                                        {
                                                                            "token": {
                                                                                "value": "2",
                                                                                "type": "condition_key",
                                                                            },
                                                                            "tree": None,
                                                                        },
                                                                        {
                                                                            "token": None,
                                                                            "tree": {
                                                                                "children": [
                                                                                    {
                                                                                        "token": None,
                                                                                        "tree": {
                                                                                            "children": [
                                                                                                {
                                                                                                    "token": {
                                                                                                        "value": "3",
                                                                                                        "type": "condition_key",
                                                                                                    },
                                                                                                    "tree": None,
                                                                                                },
                                                                                                {
                                                                                                    "token": {
                                                                                                        "value": "77",
                                                                                                        "type": "condition_key",
                                                                                                    },
                                                                                                    "tree": None,
                                                                                                },
                                                                                            ],
                                                                                            "type": "and_composition",
                                                                                        },
                                                                                    },
                                                                                    {
                                                                                        "token": None,
                                                                                        "tree": {
                                                                                            "children": [
                                                                                                {
                                                                                                    "token": {
                                                                                                        "value": "99",
                                                                                                        "type": "condition_key",
                                                                                                    },
                                                                                                    "tree": None,
                                                                                                },
                                                                                                {
                                                                                                    "token": {
                                                                                                        "value": "502",
                                                                                                        "type": "condition_key",
                                                                                                    },
                                                                                                    "tree": None,
                                                                                                },
                                                                                            ],
                                                                                            "type": "then_also_composition",
                                                                                        },
                                                                                    },
                                                                                ],
                                                                                "type": "xor_composition",
                                                                            },
                                                                        },
                                                                    ],
                                                                    "type": "or_composition",
                                                                },
                                                            },
                                                            {
                                                                "token": {"value": "901", "type": "condition_key"},
                                                                "tree": None,
                                                            },
                                                        ],
                                                        "type": "then_also_composition",
                                                    },
                                                },
                                            ],
                                            "type": "and_composition",
                                        },
                                    },
                                ],
                                "type": "Soll",
                            },
                        },
                        {
                            "token": None,
                            "tree": {
                                "children": [{"token": {"value": "43", "type": "condition_key"}, "tree": None}],
                                "type": "Kann",
                            },
                        },
                    ],
                    "type": "ahb_expression",
                },
            ),
        ],
    )
    async def test_concise_condition_key_tree_serialization_behaviour_for_ahb_expressions(
        self, expression: str, expected_compact_json_dict: dict
    ):
        tree = await parse_expression_including_unresolved_subexpressions(expression)
        json_dict = ConciseConditionKeyTreeSchema().dump(tree)
        assert json_dict == expected_compact_json_dict
