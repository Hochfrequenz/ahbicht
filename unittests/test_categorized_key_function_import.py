def test_extract_categorized_keys_is_callable():
    # pylint:disable=import-outside-toplevel
    from ahbicht.expressions.condition_expression_parser import extract_categorized_keys

    # must not fail because of cyclic imports
    _ = extract_categorized_keys("Muss [1] U [2]")
