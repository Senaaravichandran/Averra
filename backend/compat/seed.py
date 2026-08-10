"""Backward-compatible demo seeding entrypoint."""

from config import DATABASE_PATH
from backend.averra.seed import STUDENTS, seed_demo_data


def seed():
    seed_demo_data(DATABASE_PATH)


if __name__ == "__main__":
    seed()
    print("Averra demo data is ready.")
