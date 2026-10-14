
import pytest

from scripts.seed_database import validate_scheme_rules


def make_rule(**overrides):
    rule = {
        "scheme_name": "Test Scheme",
        "field": "age",
        "operator": ">=",
        "value": "18",
        "logical_group": 1,
        "logical_operator": "AND",
    }
    rule.update(overrides)
    return rule


def test_valid_rule_configuration_passes():
    rules = [
        make_rule(field="age", operator=">=", value="18"),
        make_rule(field="age", operator="<=", value="40"),
        make_rule(
            field="epfo_status",
            operator="==",
            value="false",
        ),
    ]

    validate_scheme_rules(rules)


def test_empty_rules_are_valid_configuration():
    validate_scheme_rules([])


def test_unsupported_field_is_rejected():
    with pytest.raises(ValueError, match="Unsupported field"):
        validate_scheme_rules([make_rule(field="unknown_field")])


def test_unsupported_operator_is_rejected():
    with pytest.raises(ValueError, match="Unsupported operator"):
        validate_scheme_rules([make_rule(operator="LIKE")])


def test_non_numeric_field_cannot_use_numeric_operator():
    rule = make_rule(
        field="state",
        operator=">=",
        value="18",
    )

    with pytest.raises(ValueError, match="Numeric operator"):
        validate_scheme_rules([rule])


def test_non_numeric_comparison_value_is_rejected():
    rule = make_rule(value="eighteen")

    with pytest.raises(ValueError, match="must be numeric"):
        validate_scheme_rules([rule])


def test_invalid_boolean_value_is_rejected():
    rule = make_rule(
        field="epfo_status",
        operator="==",
        value="maybe",
    )

    with pytest.raises(ValueError, match="true or false"):
        validate_scheme_rules([rule])


def test_invalid_logical_operator_is_rejected():
    rule = make_rule(logical_operator="XOR")

    with pytest.raises(ValueError, match="must be AND or OR"):
        validate_scheme_rules([rule])


def test_mixed_operators_in_same_group_are_rejected():
    rules = [
        make_rule(logical_group=1, logical_operator="AND"),
        make_rule(
            field="monthly_income",
            operator="<=",
            value="15000",
            logical_group=1,
            logical_operator="OR",
        ),
    ]

    with pytest.raises(ValueError, match="same logical_operator"):
        validate_scheme_rules(rules)


def test_different_groups_can_use_different_operators():
    rules = [
        make_rule(logical_group=1, logical_operator="AND"),
        make_rule(
            field="monthly_income",
            operator="<=",
            value="15000",
            logical_group=2,
            logical_operator="OR",
        ),
    ]

    validate_scheme_rules(rules)


def test_missing_required_key_is_rejected():
    rule = make_rule()
    del rule["scheme_name"]

    with pytest.raises(ValueError, match="Missing keys"):
        validate_scheme_rules([rule])


def test_logical_group_must_be_positive_integer():
    with pytest.raises(ValueError, match="positive integer"):
        validate_scheme_rules([make_rule(logical_group=0)])




def test_age_must_be_a_whole_number():
    with pytest.raises(ValueError, match="whole number"):
        validate_scheme_rules([
            make_rule(value="18.5")
        ])


def test_boolean_field_rejects_numeric_operator():
    with pytest.raises(ValueError, match="only supports"):
        validate_scheme_rules([
            make_rule(
                field="epfo_status",
                operator=">=",
                value="1",
            )
        ])


def test_numeric_field_rejects_boolean_value():
    with pytest.raises(ValueError, match="must be numeric"):
        validate_scheme_rules([
            make_rule(value=True)
        ])
