
import json
from datetime import datetime
from pathlib import Path

from app.db.database import SessionLocal
from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from app.models.state import State
from app.models.worker_type import WorkerType


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SEED_DIR = BASE_DIR / "data" / "seed"


SUPPORTED_FIELDS = {
    "age",
    "monthly_income",
    "epfo_status",
    "esic_status",
    "nps_status",
    "income_tax_payer",
    "state",
    "district",
    "worker_type",
    "employment_type",
}

SUPPORTED_OPERATORS = {"==", "!=", ">", "<", ">=", "<="}
SUPPORTED_LOGICAL_OPERATORS = {"AND", "OR"}

NUMERIC_FIELDS = {"age", "monthly_income"}

BOOLEAN_FIELDS = {
    "epfo_status",
    "esic_status",
    "nps_status",
    "income_tax_payer",
}


def load_json(filename: str):
    file_path = SEED_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def validate_scheme_rules(rules):
    """Validate scheme-rule configuration before database insertion."""

    group_operators = {}

    required_fields = {
        "scheme_name",
        "field",
        "operator",
        "value",
        "logical_group",
        "logical_operator",
    }

    for index, rule in enumerate(rules, start=1):
        prefix = f"Rule #{index}"

        if not isinstance(rule, dict):
            raise ValueError(f"{prefix}: Each rule must be a JSON object.")

        missing_keys = required_fields - rule.keys()

        if missing_keys:
            raise ValueError(
                f"{prefix}: Missing keys: "
                f"{', '.join(sorted(missing_keys))}"
            )

        scheme_name = rule["scheme_name"]
        field = rule["field"]
        operator = rule["operator"]
        value = rule["value"]
        logical_group = rule["logical_group"]
        logical_operator = rule["logical_operator"]

        if not isinstance(scheme_name, str) or not scheme_name.strip():
            raise ValueError(
                f"{prefix}: scheme_name must be a non-empty string."
            )

        if field not in SUPPORTED_FIELDS:
            raise ValueError(
                f"{prefix}: Unsupported field '{field}' "
                f"for scheme '{scheme_name}'."
            )

        if operator not in SUPPORTED_OPERATORS:
            raise ValueError(
                f"{prefix}: Unsupported operator '{operator}'."
            )

        if (
            isinstance(logical_group, bool)
            or not isinstance(logical_group, int)
            or logical_group < 1
        ):
            raise ValueError(
                f"{prefix}: logical_group must be a positive integer."
            )

        if (
            not isinstance(logical_operator, str)
            or logical_operator.upper() not in SUPPORTED_LOGICAL_OPERATORS
        ):
            raise ValueError(
                f"{prefix}: logical_operator must be AND or OR."
            )

        logical_operator = logical_operator.upper()
        group_key = (scheme_name, logical_group)
        previous_operator = group_operators.get(group_key)

        if (
            previous_operator is not None
            and previous_operator != logical_operator
        ):
            raise ValueError(
                f"Scheme '{scheme_name}', group {logical_group}: "
                "all rules must use the same logical_operator."
            )

        group_operators[group_key] = logical_operator

        # Boolean fields only support equality comparisons.
        if field in BOOLEAN_FIELDS:
            if operator not in {"==", "!="}:
                raise ValueError(
                    f"{prefix}: Boolean field '{field}' "
                    "only supports == and !=."
                )

            if (
                not isinstance(value, (str, bool))
                or str(value).lower() not in {"true", "false"}
            ):
                raise ValueError(
                    f"{prefix}: Value for '{field}' must be true or false."
                )

        # Numeric fields must have numeric values.
        if field in NUMERIC_FIELDS:
            if isinstance(value, bool) or not isinstance(
                value, (str, int, float)
            ):
                raise ValueError(
                    f"{prefix}: Value for '{field}' must be numeric."
                )

            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"{prefix}: Value for '{field}' must be numeric."
                ) from None

            if not __import__("math").isfinite(numeric_value):
                raise ValueError(
                    f"{prefix}: Value for '{field}' must be finite."
                )

            if field == "age" and not numeric_value.is_integer():
                raise ValueError(
                    f"{prefix}: Value for 'age' must be a whole number."
                )

        # Numeric comparison operators are not valid for text/boolean fields.
        if operator in {">", "<", ">=", "<="}:
            if field not in NUMERIC_FIELDS:
                raise ValueError(
                    f"{prefix}: Numeric operator '{operator}' "
                    f"cannot be used with field '{field}'."
                )

        # Text fields require a non-empty string value.
        if field not in NUMERIC_FIELDS | BOOLEAN_FIELDS:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"{prefix}: Value for '{field}' "
                    "must be a non-empty string."
                )


def seed_states(db):
    states = load_json("states.json")

    for state_data in states:
        existing_state = (
            db.query(State)
            .filter(State.code == state_data["code"])
            .first()
        )

        if existing_state:
            continue

        db.add(
            State(
                name=state_data["name"],
                code=state_data["code"],
            )
        )


def seed_worker_types(db):
    worker_types = load_json("worker_types.json")

    for worker_type_data in worker_types:
        existing_worker_type = (
            db.query(WorkerType)
            .filter(WorkerType.code == worker_type_data["code"])
            .first()
        )

        if existing_worker_type:
            continue

        db.add(
            WorkerType(
                name=worker_type_data["name"],
                code=worker_type_data["code"],
            )
        )


def seed_schemes(db):
    schemes = load_json("schemes.json")

    for scheme_data in schemes:
        existing_scheme = (
            db.query(Scheme)
            .filter(Scheme.name == scheme_data["name"])
            .first()
        )

        if existing_scheme:
            continue

        db.add(
            Scheme(
                name=scheme_data["name"],
                description=scheme_data["description"],
                category=scheme_data["category"],
                level=scheme_data["level"],
                source_url=scheme_data["source_url"],
                verification_status=scheme_data["verification_status"],
                last_verified_at=datetime.fromisoformat(
                    scheme_data["last_verified_at"]
                ),
                version=scheme_data["version"],
                status=scheme_data["status"],
            )
        )


def seed_scheme_rules(db):
    rules = load_json("scheme_rules.json")
    validate_scheme_rules(rules)

    for rule_data in rules:
        scheme = (
            db.query(Scheme)
            .filter(Scheme.name == rule_data["scheme_name"])
            .first()
        )

        if not scheme:
            raise ValueError(
                f"Scheme not found: {rule_data['scheme_name']}"
            )

        existing_rule = (
            db.query(SchemeRule)
            .filter(
                SchemeRule.scheme_id == scheme.id,
                SchemeRule.field == rule_data["field"],
                SchemeRule.operator == rule_data["operator"],
                SchemeRule.value == str(rule_data["value"]),
                SchemeRule.logical_group == rule_data["logical_group"],
            )
            .first()
        )

        if existing_rule:
            continue

        db.add(
            SchemeRule(
                scheme_id=scheme.id,
                field=rule_data["field"],
                operator=rule_data["operator"],
                value=str(rule_data["value"]),
                logical_group=rule_data["logical_group"],
                logical_operator=rule_data["logical_operator"].upper(),
            )
        )


def main():
    db = SessionLocal()

    try:
        seed_states(db)
        seed_worker_types(db)
        seed_schemes(db)

        db.flush()

        seed_scheme_rules(db)

        db.commit()
        print("Seed data inserted successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
