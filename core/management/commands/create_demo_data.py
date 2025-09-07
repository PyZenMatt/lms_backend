"""
DEPRECATED: create_demo_data

This module was a small demo script that created only courses. The project now
has richer seeders and management commands (see `seed_db.py`, `create_test_data.py`,
`setup_teacher_data.py`, `setup_student1_test.py`, etc.).

To avoid accidental execution, the original script was replaced with this stub.
If you need a full seeder, use `core/management/commands/seed_db.py` or
`create_test_data.py`, or tell me which data shape you want and I will add a
new command to generate students, teachers, courses, lessons, and exercises.
"""

def create_demo_data(*args, **kwargs):
    raise RuntimeError(
        "create_demo_data has been removed. Use 'seed_db' or 'create_test_data' instead."
    )


if __name__ == "__main__":
    print("create_demo_data is deprecated and has been disabled. See the module docstring.")
