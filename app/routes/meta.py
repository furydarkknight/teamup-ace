from fastapi import APIRouter
from app.schemas import CategoriesMetaResponse
from app.config.categories import (
    SKILLS, SKILL_GROUPS, PROFICIENCY_LEVELS, PROFICIENCY_LABELS,
    INTERESTS, EXPERIENCE_LEVELS, AVAILABILITY_OPTIONS,
    PREFERRED_TEAM_SIZES, PREFERRED_ROLES, COLLABORATION_PREFERENCES, COLLEGES
)

router = APIRouter(prefix="/api/meta", tags=["Meta"])

@router.get("/categories", response_model=CategoriesMetaResponse)
def get_categories():
    """Returns all category lists derived from the real dataset. Use for frontend dropdowns and backend validation."""
    return CategoriesMetaResponse(
        skills=SKILLS,
        skill_groups=SKILL_GROUPS,
        proficiency_levels=PROFICIENCY_LEVELS,
        proficiency_labels=PROFICIENCY_LABELS,
        interests=INTERESTS,
        experience_levels=EXPERIENCE_LEVELS,
        availability=AVAILABILITY_OPTIONS,
        preferred_team_sizes=PREFERRED_TEAM_SIZES,
        preferred_roles=PREFERRED_ROLES,
        collaboration_preferences=COLLABORATION_PREFERENCES,
        colleges=COLLEGES,
    )
