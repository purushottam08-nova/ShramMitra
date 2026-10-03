from app.rules.evaluator import (
    MATCH,
    MISSING,
    NO_MATCH,
    evaluate_rule,
    evaluate_scheme,
)


class FakeRule:
    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value


def test_age_rule_matches():
    rule = FakeRule("age", ">=", "18")

    profile = {
        "age": 25,
    }

    assert evaluate_rule(profile, rule) == MATCH


def test_age_rule_does_not_match():
    rule = FakeRule("age", ">=", "18")

    profile = {
        "age": 16,
    }

    assert evaluate_rule(profile, rule) == NO_MATCH


def test_missing_profile_field():
    rule = FakeRule("age", ">=", "18")

    profile = {}

    assert evaluate_rule(profile, rule) == MISSING


def test_boolean_rule_matches():
    rule = FakeRule("epfo_status", "==", "false")

    profile = {
        "epfo_status": False,
    }

    assert evaluate_rule(profile, rule) == MATCH


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

    profile = {
        "age": 25,
    }

    assert evaluate_scheme(profile, rules) == MISSING