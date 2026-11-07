"""
Safe SQLite schema migrations for TeamUp by ACE.
Adds any missing columns to existing tables without data loss.
"""

import sqlite3
from pathlib import Path
from app.config import DATABASE_URL, BASE_DIR
from app.database import engine, Base

def run_migrations():
    # 1. First ensure all models are registered on Base, then create new tables
    import app.models
    Base.metadata.create_all(bind=engine)

    # 2. Extract database file path for SQLite
    if not DATABASE_URL.startswith("sqlite"):
        return

    db_path = DATABASE_URL.replace("sqlite:///", "")
    if not Path(db_path).is_absolute():
        db_path = str(BASE_DIR / db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    def get_existing_columns(table_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in cursor.fetchall()}

    # --- Migrate `users` table ---
    users_existing = get_existing_columns("users")
    user_columns_to_add = [
        ("student_id", "TEXT"),
        ("skill_proficiency_json", "TEXT DEFAULT '{}'"),
        ("project_experience_json", "TEXT DEFAULT '[]'"),
        ("preferred_roles_json", "TEXT DEFAULT '[]'"),
        ("preferred_team_size", "INTEGER DEFAULT 4"),
        ("collaboration_preference", "TEXT DEFAULT ''"),
        ("bio", "TEXT DEFAULT ''"),
        ("role", "TEXT DEFAULT 'student'"),
        ("roles_json", "TEXT DEFAULT '[\"student\"]'"),
        ("username", "TEXT"),
        ("headline", "TEXT DEFAULT ''"),
        ("company_name", "TEXT DEFAULT ''"),
        ("points", "INTEGER DEFAULT 0")
    ]
    for col_name, col_def in user_columns_to_add:
        if col_name not in users_existing:
            print(f"[Migration] Adding column users.{col_name}...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

    # Add indexes for users if missing
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_student_id ON users (student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_college ON users (college)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_experience_level ON users (experience_level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_availability ON users (availability)")

    # --- Migrate `teams` table ---
    teams_existing = get_existing_columns("teams")
    team_columns_to_add = [
        ("team_id", "TEXT"),
        ("team_name", "TEXT"),
        ("college", "TEXT DEFAULT 'Riverdale College of Technology'"),
        ("current_members_json", "TEXT DEFAULT '[]'"),
        ("current_team_size", "INTEGER DEFAULT 1"),
        ("vacancies", "INTEGER DEFAULT 3"),
        ("current_skills_json", "TEXT DEFAULT '{}'"),
        ("required_skills_json", "TEXT DEFAULT '[]'"),
        ("preferred_skills_json", "TEXT DEFAULT '[]'"),
        ("skill_requirements_json", "TEXT DEFAULT '{}'"),
        ("interests_json", "TEXT DEFAULT '[]'"),
        ("preferred_experience", "TEXT DEFAULT 'Intermediate'"),
        ("availability", "TEXT DEFAULT 'Full-time'"),
        ("preferred_roles_json", "TEXT DEFAULT '[]'"),
        ("team_description", "TEXT DEFAULT ''"),
        ("collaboration_preference", "TEXT DEFAULT ''")
    ]
    for col_name, col_def in team_columns_to_add:
        if col_name not in teams_existing:
            print(f"[Migration] Adding column teams.{col_name}...")
            cursor.execute(f"ALTER TABLE teams ADD COLUMN {col_name} {col_def}")

    # Add indexes for teams if missing
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_teams_team_id ON teams (team_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_teams_college ON teams (college)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_teams_vacancies ON teams (vacancies)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_teams_preferred_experience ON teams (preferred_experience)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_teams_availability ON teams (availability)")

    conn.commit()
    conn.close()
    print("[Migration] Safe schema migration completed successfully.")

if __name__ == "__main__":
    run_migrations()
