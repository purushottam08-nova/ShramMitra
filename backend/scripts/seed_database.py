import json
from pathlib import Path
from datetime import datetime

from app.db.database import SessionLocal
from app.models.state import State
from app.models.worker_type import WorkerType
from app.models.scheme import Scheme


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SEED_DIR = BASE_DIR / "data" / "seed"


def load_json(filename: str):
    file_path = SEED_DIR / filename

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


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

        state = State(
            name=state_data["name"],
            code=state_data["code"],
        )

        db.add(state)


def seed_worker_types(db):
    worker_types = load_json("worker_types.json")

    for worker_type_data in worker_types:
        existing_worker_type = (
            db.query(WorkerType)
            .filter(
                WorkerType.code == worker_type_data["code"]
            )
            .first()
        )

        if existing_worker_type:
            continue

        worker_type = WorkerType(
            name=worker_type_data["name"],
            code=worker_type_data["code"],
        )

        db.add(worker_type)



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

        scheme = Scheme(
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

        db.add(scheme)


def main():
    db = SessionLocal()

    try:
        seed_states(db)
        seed_worker_types(db)
        seed_schemes(db)

        db.commit()

        print("Seed data inserted successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()