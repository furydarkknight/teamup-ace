import json
from pathlib import Path
from typing import List, Any
from app.config.categories import (
    SKILLS, INTERESTS, PREFERRED_ROLES, AVAILABILITY_OPTIONS,
    COLLABORATION_PREFERENCES, EXPERIENCE_LEVELS
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "models" / "feature_schema.json"

EXP_MAP = {"beginner": 0.0, "intermediate": 1.0, "advanced": 2.0}

def build_features(student: Any, team: Any) -> List[float]:
    """
    Constructs a 229-dimensional numerical feature vector for (student, team) pair
    matching the schema in models/feature_schema.json.

    ========================================================================
    TODO FOR ML ENGINEER:
    If your model training code uses a different feature transformation,
    you can adjust the feature logic below or paste your training vector code.
    ========================================================================
    """
    features: List[float] = []

    # 1. Student Skills: proficiency values (0-5)
    s_prof = student.skill_proficiency if hasattr(student, "skill_proficiency") and student.skill_proficiency else {}
    for skill in SKILLS:
        level = s_prof.get(skill, 0)
        features.append(float(level))

    # 2. Team Skill Requirements: minimum level (0-5)
    t_reqs = team.skill_requirements if hasattr(team, "skill_requirements") and team.skill_requirements else {}
    for skill in SKILLS:
        req_level = t_reqs.get(skill, 0)
        features.append(float(req_level))

    # 3. Skill Gap Vector: max(required - student_level, 0)
    for skill in SKILLS:
        s_level = s_prof.get(skill, 0)
        t_level = t_reqs.get(skill, 0)
        gap = max(0, t_level - s_level)
        features.append(float(gap))

    # 4. Student Interests: Multi-hot (0/1)
    s_interests = set(student.interests or [])
    for interest in INTERESTS:
        features.append(1.0 if interest in s_interests else 0.0)

    # 5. Team Interests: Multi-hot (0/1)
    t_interests = set(team.interests or [])
    for interest in INTERESTS:
        features.append(1.0 if interest in t_interests else 0.0)

    # 6. Student Preferred Roles: Multi-hot (0/1)
    s_roles = set(student.preferred_roles or [])
    for role in PREFERRED_ROLES:
        features.append(1.0 if role in s_roles else 0.0)

    # 7. Team Preferred Roles: Multi-hot (0/1)
    t_roles = set(team.preferred_roles or [])
    for role in PREFERRED_ROLES:
        features.append(1.0 if role in t_roles else 0.0)

    # 8. Experience Ordinal (0, 1, 2)
    s_exp = EXP_MAP.get(str(student.experience_level).lower(), 1.0)
    t_exp = EXP_MAP.get(str(team.preferred_experience).lower(), 1.0)
    features.append(s_exp)
    features.append(t_exp)

    # 9. Availability One-Hot
    s_avail = str(student.availability).strip()
    t_avail = str(team.availability).strip()
    for a in AVAILABILITY_OPTIONS:
        features.append(1.0 if s_avail == a else 0.0)
    for a in AVAILABILITY_OPTIONS:
        features.append(1.0 if t_avail == a else 0.0)

    # 10. Collaboration Preference One-Hot (10 sentences)
    s_collab = str(student.collaboration_preference).strip()
    t_collab = str(team.collaboration_preference).strip()
    for pref in COLLABORATION_PREFERENCES:
        features.append(1.0 if s_collab == pref else 0.0)
    for pref in COLLABORATION_PREFERENCES:
        features.append(1.0 if t_collab == pref else 0.0)

    # 11. Sizes and Vacancies
    s_pref_size = float(student.preferred_team_size or 4)
    t_curr_size = float(team.current_team_size or len(team.current_members or []))
    t_vacancies = float(team.vacancies if team.vacancies is not None else 1)
    t_final_size = t_curr_size + t_vacancies

    features.append(s_pref_size)
    features.append(t_curr_size)
    features.append(t_vacancies)
    features.append(t_final_size)

    return features
