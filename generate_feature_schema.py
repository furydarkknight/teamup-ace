import json
from pathlib import Path
from app.config.categories import (
    SKILLS, INTERESTS, PREFERRED_ROLES, AVAILABILITY_OPTIONS,
    COLLABORATION_PREFERENCES
)

def generate_schema():
    features = []

    # 1. Student Skills (Proficiency 0-5)
    for s in SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("+", "p")
        features.append(f"student_skill_{s_clean}")

    # 2. Team Skill Requirements (Minimum Level 0-5)
    for s in SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("+", "p")
        features.append(f"team_skill_req_{s_clean}")

    # 3. Skill Gap Vector (max(required - student_level, 0))
    for s in SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("+", "p")
        features.append(f"skill_gap_{s_clean}")

    # 4. Student Interests (Multi-hot 0/1)
    for i in INTERESTS:
        i_clean = i.lower().replace(" ", "_").replace("/", "_").replace("&", "and").replace("-", "_")
        features.append(f"student_interest_{i_clean}")

    # 5. Team Interests (Multi-hot 0/1)
    for i in INTERESTS:
        i_clean = i.lower().replace(" ", "_").replace("/", "_").replace("&", "and").replace("-", "_")
        features.append(f"team_interest_{i_clean}")

    # 6. Student Preferred Roles (Multi-hot 0/1)
    for r in PREFERRED_ROLES:
        r_clean = r.lower().replace(" ", "_").replace("/", "_")
        features.append(f"student_role_{r_clean}")

    # 7. Team Preferred Roles (Multi-hot 0/1)
    for r in PREFERRED_ROLES:
        r_clean = r.lower().replace(" ", "_").replace("/", "_")
        features.append(f"team_role_{r_clean}")

    # 8. Experience Ordinal
    features.append("student_experience_ordinal")
    features.append("team_experience_ordinal")

    # 9. Availability One-Hot
    for a in AVAILABILITY_OPTIONS:
        a_clean = a.lower().replace("-", "_").replace(" ", "_")
        features.append(f"student_avail_{a_clean}")
    for a in AVAILABILITY_OPTIONS:
        a_clean = a.lower().replace("-", "_").replace(" ", "_")
        features.append(f"team_avail_{a_clean}")

    # 10. Collaboration Preferences One-Hot
    for idx in range(len(COLLABORATION_PREFERENCES)):
        features.append(f"student_collab_pref_{idx}")
    for idx in range(len(COLLABORATION_PREFERENCES)):
        features.append(f"team_collab_pref_{idx}")

    # 11. Size & Vacancies
    features.append("student_preferred_team_size")
    features.append("team_current_size")
    features.append("team_vacancies")
    features.append("team_final_size")

    out_file = Path("models/feature_schema.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_features": len(features),
            "feature_names": features
        }, f, indent=2)
    print(f"[OK] Generated {len(features)} feature schema in {out_file}")

if __name__ == "__main__":
    generate_schema()
