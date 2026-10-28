from collections import defaultdict

from app.models.scheme_rule import SchemeRule


MATCH = "MATCH"
NO_MATCH = "NO_MATCH"
MISSING = "MISSING"


FIELD_LABELS = {
    "age": "Age",
    "monthly_income": "Monthly income",
    "epfo_status": "EPFO enrollment",
    "esic_status": "ESIC enrollment",
    "nps_status": "NPS enrollment",
    "income_tax_payer": "Income-tax payer status",
    "state": "State",
    "district": "District",
    "worker_type": "Worker type",
    "employment_type": "Employment type",
}

OPERATOR_LABELS = {
    "==": "must equal",
    "!=": "must not equal",
    ">": "must be greater than",
    "<": "must be less than",
    ">=": "must be at least",
    "<=": "must be at most",
}


def normalize_value(value) -> str:
    if isinstance(value, bool):
        return str(value).lower()

    return str(value).strip().lower()


def format_value(field: str, value) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"

    if field == "monthly_income":
        try:
            return f"₹{float(value):,.0f}"
        except (TypeError, ValueError):
            pass

    return str(value)


def evaluate_rule(profile_data: dict, rule: SchemeRule) -> str:
    actual_value = profile_data.get(rule.field)

    if actual_value is None:
        return MISSING

    expected_value = rule.value

    if rule.operator == "==":
        return (
            MATCH
            if normalize_value(actual_value)
            == normalize_value(expected_value)
            else NO_MATCH
        )

    if rule.operator == "!=":
        return (
            MATCH
            if normalize_value(actual_value)
            != normalize_value(expected_value)
            else NO_MATCH
        )

    if rule.operator in {">", "<", ">=", "<="}:
        try:
            actual = float(actual_value)
            expected = float(expected_value)
        except (TypeError, ValueError):
            return MISSING

        comparisons = {
            ">": actual > expected,
            "<": actual < expected,
            ">=": actual >= expected,
            "<=": actual <= expected,
        }

        return MATCH if comparisons[rule.operator] else NO_MATCH

    raise ValueError(f"Unsupported operator: {rule.operator}")


def combine_results(results: list[str], operator: str) -> str:
    """Combine tri-state results using AND or OR logic."""
    if not results:
        return MISSING

    operator = operator.upper()

    if operator == "AND":
        if NO_MATCH in results:
            return NO_MATCH

        if MISSING in results:
            return MISSING

        return MATCH

    if operator == "OR":
        if MATCH in results:
            return MATCH

        if MISSING in results:
            return MISSING

        return NO_MATCH

    raise ValueError(f"Unsupported logical operator: {operator}")


def group_rules(rules: list[SchemeRule]) -> dict[int, list[SchemeRule]]:
    """Group rules by logical_group and validate each group's operator."""
    groups = defaultdict(list)

    for rule in rules:
        group_id = getattr(rule, "logical_group", 1)
        groups[group_id].append(rule)

    for group_id, group in groups.items():
        operators = {
            getattr(rule, "logical_operator", "AND").upper()
            for rule in group
        }

        if len(operators) != 1:
            raise ValueError(
                f"Rules in group {group_id} must use the same "
                "logical_operator."
            )

        operator = next(iter(operators))

        if operator not in {"AND", "OR"}:
            raise ValueError(f"Unsupported logical operator: {operator}")

    return dict(groups)


def get_group_operator(rules: list[SchemeRule]) -> str:
    return getattr(rules[0], "logical_operator", "AND").upper()


def evaluate_scheme(profile_data: dict, rules: list[SchemeRule]) -> str:
    if not rules:
        return MISSING

    groups = group_rules(rules)
    group_results = []

    for group in groups.values():
        rule_results = [
            evaluate_rule(profile_data, rule)
            for rule in group
        ]

        group_results.append(
            combine_results(rule_results, get_group_operator(group))
        )

    # Different groups are alternative eligibility paths (OR).
    return combine_results(group_results, "OR")


def get_missing_fields(
    profile_data: dict,
    rules: list[SchemeRule],
) -> list[str]:
    if evaluate_scheme(profile_data, rules) != MISSING:
        return []

    missing_fields = []

    for group in group_rules(rules).values():
        results = [
            evaluate_rule(profile_data, rule)
            for rule in group
        ]

        group_result = combine_results(
            results,
            get_group_operator(group),
        )

        if group_result != MISSING:
            continue

        for rule in group:
            if (
                evaluate_rule(profile_data, rule) == MISSING
                and rule.field not in missing_fields
            ):
                missing_fields.append(rule.field)

    return missing_fields


def get_rule_reasons(
    profile_data: dict,
    rules: list[SchemeRule],
) -> list[str]:
    if not rules:
        return ["No eligibility rules are configured for this scheme."]

    groups = group_rules(rules)
    overall_result = evaluate_scheme(profile_data, rules)
    reasons = []

    if overall_result == MATCH:
        matched_groups = [
            (group_id, group)
            for group_id, group in groups.items()
            if combine_results(
                [
                    evaluate_rule(profile_data, rule)
                    for rule in group
                ],
                get_group_operator(group),
            ) == MATCH
        ]

        for group_id, group in matched_groups:
            operator = get_group_operator(group)

            if operator == "AND":
                reasons.append(
                    f"Eligibility group {group_id}: all configured "
                    "conditions matched."
                )
            else:
                reasons.append(
                    f"Eligibility group {group_id}: at least one "
                    "configured condition matched."
                )

        reasons.append(
            "This is a preliminary result, not an official approval."
        )

        return reasons

    for group_id, group in groups.items():
        results = [
            evaluate_rule(profile_data, rule)
            for rule in group
        ]

        group_result = combine_results(
            results,
            get_group_operator(group),
        )

        # Don't report irrelevant failures from an alternative group.
        if overall_result == MISSING and group_result != MISSING:
            continue

        for rule, result in zip(group, results):
            label = FIELD_LABELS.get(
                rule.field,
                rule.field.replace("_", " ").capitalize(),
            )

            if result == MISSING:
                reasons.append(
                    f"{label} is missing, so this condition "
                    "could not be checked."
                )

            elif result == NO_MATCH:
                # In an OR group, one failed condition is not
                # a group failure if another condition matches.
                if (
                    get_group_operator(group) == "OR"
                    and group_result == MATCH
                ):
                    continue

                operator_label = OPERATOR_LABELS.get(rule.operator)

                if operator_label is None:
                    raise ValueError(
                        f"Unsupported operator: {rule.operator}"
                    )

                expected = format_value(rule.field, rule.value)
                actual = format_value(
                    rule.field,
                    profile_data[rule.field],
                )

                reasons.append(
                    f"{label} {operator_label} {expected}; "
                    f"your recorded value is {actual}."
                )

    if not reasons:
        reasons.append(
            "More information is needed to evaluate eligibility."
        )

    return reasons