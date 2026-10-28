from app.rules.evaluator import (
    MATCH,
    MISSING,
    NO_MATCH,
    evaluate_rule,
    evaluate_scheme,
    format_value,
)


class FakeRule:
    def __init__(
        self,
        field,
        operator,
        value,
        logical_group=1,
        logical_operator="AND",
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.logical_group = logical_group
        self.logical_operator = logical_operator


def test_age_rule_matches():
    rule = FakeRule("age", ">=", "18")

    assert evaluate_rule({"age": 25}, rule) == MATCH


def test_age_rule_does_not_match():
    rule = FakeRule("age", ">=", "18")

    assert evaluate_rule({"age": 16}, rule) == NO_MATCH


def test_missing_profile_field():
    rule = FakeRule("age", ">=", "18")

    assert evaluate_rule({}, rule) == MISSING


def test_boolean_rule_matches():
    rule = FakeRule("epfo_status", "==", "false")

    assert evaluate_rule({"epfo_status": False}, rule) == MATCH


def test_boolean_rule_normalizes_whitespace_and_case():
    rule = FakeRule("worker_type", "==", "  DRIVER ")

    assert evaluate_rule({"worker_type": "driver"}, rule) == MATCH


def test_invalid_numeric_value_returns_missing():
    rule = FakeRule("age", ">=", "18")

    assert evaluate_rule({"age": "unknown"}, rule) == MISSING


def test_scheme_matches_all_rules():
    rules = [
        FakeRule("age", ">=", "18"),
        FakeRule("age", "<=", "40"),
        FakeRule("monthly_income", "<=", "15000"),
        FakeRule("epfo_status", "==", "false"),
    ]

    profile = {
        "age": 25,
        "monthly_income": 12000,
        "epfo_status": False,
    }

    assert evaluate_scheme(profile, rules) == MATCH


def test_scheme_does_not_match():
    rules = [
        FakeRule("age", ">=", "18"),
        FakeRule("monthly_income", "<=", "15000"),
    ]

    profile = {
        "age": 25,
        "monthly_income": 20000,
    }

    assert evaluate_scheme(profile, rules) == NO_MATCH


def test_scheme_has_missing_information():
    rules = [
        FakeRule("age", ">=", "18"),
        FakeRule("monthly_income", "<=", "15000"),
    ]

    assert evaluate_scheme({"age": 25}, rules) == MISSING


def test_alternative_eligibility_groups():
    rules = [
        FakeRule(
            "age",
            ">=",
            "60",
            logical_group=1,
            logical_operator="AND",
        ),
        FakeRule(
            "age",
            ">=",
            "18",
            logical_group=2,
            logical_operator="AND",
        ),
    ]

    assert evaluate_scheme({"age": 25}, rules) == MATCH


def test_format_income_uses_rupee_symbol():
    assert format_value("monthly_income", 12000) == "₹12,000"