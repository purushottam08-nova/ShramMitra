from app.models.scheme_rule import SchemeRule


MATCH = "MATCH"
NO_MATCH = "NO_MATCH"
MISSING = "MISSING"


def normalize_value(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()

    return str(value)


def evaluate_rule(profile_data: dict, rule: SchemeRule) -> str:
    actual_value = profile_data.get(rule.field)

    if actual_value is None:
        return MISSING

    expected_value = rule.value

    if rule.operator == "==":
        return (
            MATCH
            if normalize_value(actual_value) == expected_value.lower()
            else NO_MATCH
        )

    if rule.operator == "!=":
        return (
            MATCH
            if normalize_value(actual_value) != expected_value.lower()
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

    raise ValueError(f"Unsupported operator: {rule.operator}")


def evaluate_scheme(profile_data: dict, rules: list[SchemeRule]) -> str:
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


def get_missing_fields(
    profile_data: dict,
    rules: list[SchemeRule],
) -> list[str]:

    missing_fields = []

    for rule in rules:
        result = evaluate_rule(profile_data, rule)

        if result == MISSING and rule.field not in missing_fields:
            missing_fields.append(rule.field)

    return missing_fields