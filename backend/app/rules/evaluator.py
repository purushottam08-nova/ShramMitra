from app.models.scheme_rule import SchemeRule


MATCH = "MATCH"
NO_MATCH = "NO_MATCH"
MISSING = "MISSING"


def evaluate_rule(
    profile_data: dict,
    rule: SchemeRule,
) -> str:

    actual_value = profile_data.get(rule.field)

    if actual_value is None:
        return MISSING

    expected_value = rule.value

    if rule.operator == "==":
        return (
            MATCH
            if str(actual_value) == expected_value
            else NO_MATCH
        )

    if rule.operator == "!=":
        return (
            MATCH
            if str(actual_value) != expected_value
            else NO_MATCH
        )

    if rule.operator == ">":
        return (
            MATCH
            if float(actual_value) > float(expected_value)
            else NO_MATCH
        )

    if rule.operator == "<":
        return (
            MATCH
            if float(actual_value) < float(expected_value)
            else NO_MATCH
        )

    if rule.operator == ">=":
        return (
            MATCH
            if float(actual_value) >= float(expected_value)
            else NO_MATCH
        )

    if rule.operator == "<=":
        return (
            MATCH
            if float(actual_value) <= float(expected_value)
            else NO_MATCH
        )

    raise ValueError(
        f"Unsupported operator: {rule.operator}"
    )


def evaluate_scheme(
    profile_data: dict,
    rules: list[SchemeRule],
) -> str:

    has_missing = False

    for rule in rules:
        result = evaluate_rule(profile_data, rule)

        if result == NO_MATCH:
            return NO_MATCH

        if result == MISSING:
            has_missing = True

    if has_missing:
        return MISSING

    return MATCH