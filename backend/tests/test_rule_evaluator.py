
from types import SimpleNamespace
from app.rules.evaluator import get_rule_reasons
from app.models.scheme_rule import SchemeRule
import pytest

from app.rules.evaluator import (
    MATCH,
    MISSING,
    NO_MATCH,
    evaluate_rule,
    evaluate_scheme,
    get_missing_fields,
    get_rule_reasons,
)


def make_rule(
    field,
    operator,
    value,
    logical_group=1,
    logical_operator="AND",
):
    return SchemeRule(
        field=field,
        operator=operator,
        value=value,
        logical_group=logical_group,
        logical_operator=logical_operator,
    )


def test_income_at_limit_matches():
    profile = {"monthly_income": 15000}
    rule = make_rule("monthly_income", "<=", "15000")

    assert evaluate_rule(profile, rule) == MATCH


def test_income_above_limit_does_not_match():
    profile = {"monthly_income": 30000}
    rule = make_rule("monthly_income", "<=", "15000")

    assert evaluate_rule(profile, rule) == NO_MATCH


def test_missing_age_returns_missing():
    profile = {"age": None}
    rule = make_rule("age", ">=", "18")

    assert evaluate_rule(profile, rule) == MISSING


def test_all_rules_match():
    profile = {
        "age": 30,
        "monthly_income": 12000,
        "epfo_status": False,
    }
    rules = [
        make_rule("age", ">=", "18"),
        make_rule("age", "<=", "40"),
        make_rule("monthly_income", "<=", "15000"),
        make_rule("epfo_status", "==", "false"),
    ]

    assert evaluate_scheme(profile, rules) == MATCH


def test_one_failed_rule_means_no_match():
    profile = {
        "age": 30,
        "monthly_income": 30000,
        "epfo_status": False,
    }
    rules = [
        make_rule("age", ">=", "18"),
        make_rule("monthly_income", "<=", "15000"),
        make_rule("epfo_status", "==", "false"),
    ]

    assert evaluate_scheme(profile, rules) == NO_MATCH


def test_missing_fields_are_reported():
    profile = {
        "age": None,
        "monthly_income": 12000,
    }
    rules = [
        make_rule("age", ">=", "18"),
        make_rule("monthly_income", "<=", "15000"),
    ]

    assert evaluate_scheme(profile, rules) == MISSING
    assert get_missing_fields(profile, rules) == ["age"]




def test_failed_rule_has_human_readable_reason():
    profile = {"monthly_income": 30000}
    rules = [
        make_rule("monthly_income", "<=", "15000"),
    ]

    reasons = get_rule_reasons(profile, rules)

    assert len(reasons) == 1
    assert "Monthly income" in reasons[0]
    assert "₹15,000" in reasons[0]
    assert "₹30,000" in reasons[0]


def test_missing_rule_has_explanation():
    profile = {"age": None}
    rules = [make_rule("age", ">=", "18")]

    reasons = get_rule_reasons(profile, rules)

    assert reasons == [
        "Age is missing, so this condition could not be checked."
    ]



def test_all_matching_rules_have_preliminary_note():
    profile = {"age": 30}
    rules = [make_rule("age", ">=", "18")]

    reasons = get_rule_reasons(profile, rules)

    assert any(
        "all configured conditions matched" in reason
        for reason in reasons
    )
    assert any(
        "not an official approval" in reason
        for reason in reasons
    )



def test_and_group_fails_when_one_rule_fails():
    profile = {"age": 30, "monthly_income": 20000}
    rules = [
        make_rule("age", ">=", "18"),
        make_rule("monthly_income", "<=", "15000"),
    ]

    assert evaluate_scheme(profile, rules) == NO_MATCH


def test_or_group_matches_when_one_rule_matches():
    profile = {"age": 30, "monthly_income": 20000}
    rules = [
        make_rule(
            "age", ">=", "18",
            logical_group=1, logical_operator="OR",
        ),
        make_rule(
            "monthly_income", "<=", "15000",
            logical_group=1, logical_operator="OR",
        ),
    ]

    assert evaluate_scheme(profile, rules) == MATCH


def test_alternative_group_can_match():
    profile = {"age": 16, "monthly_income": 10000}
    rules = [
        make_rule(
            "age", ">=", "18",
            logical_group=1, logical_operator="AND",
        ),
        make_rule(
            "monthly_income", "<=", "15000",
            logical_group=2, logical_operator="AND",
        ),
    ]

    assert evaluate_scheme(profile, rules) == MATCH


def test_and_group_returns_missing_when_no_rule_fails():
    profile = {"age": 30, "monthly_income": None}
    rules = [
        make_rule("age", ">=", "18"),
        make_rule("monthly_income", "<=", "15000"),
    ]

    assert evaluate_scheme(profile, rules) == MISSING


def test_or_group_returns_missing_when_no_rule_matches():
    profile = {"age": None, "monthly_income": 20000}
    rules = [
        make_rule(
            "age", ">=", "18",
            logical_group=1, logical_operator="OR",
        ),
        make_rule(
            "monthly_income", "<=", "15000",
            logical_group=1, logical_operator="OR",
        ),
    ]

    assert evaluate_scheme(profile, rules) == MISSING



def test_empty_rules_return_missing():
    assert evaluate_scheme({}, []) == MISSING


def test_invalid_logical_operator_raises_error():
    rule = make_rule(
        "age",
        ">=",
        "18",
        logical_group=1,
        logical_operator="XOR",
    )

    with pytest.raises(ValueError, match="Unsupported logical operator"):
        evaluate_scheme({"age": 30}, [rule])


def test_mixed_operators_in_same_group_raise_error():
    rules = [
        make_rule(
            "age",
            ">=",
            "18",
            logical_group=1,
            logical_operator="AND",
        ),
        make_rule(
            "monthly_income",
            "<=",
            "15000",
            logical_group=1,
            logical_operator="OR",
        ),
    ]

    with pytest.raises(ValueError, match="same logical_operator"):
        evaluate_scheme(
            {"age": 30, "monthly_income": 10000},
            rules,
        )
