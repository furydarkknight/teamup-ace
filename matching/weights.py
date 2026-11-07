"""
Matching weight configuration.
Adjust these values to tune the rule-based matcher without touching logic.
"""

# Student -> Team matching weights (must sum to 1.0)
SKILL_GAP_COVERAGE_WEIGHT = 0.35   # Student skills vs team skill_requirements levels
INTEREST_OVERLAP_WEIGHT   = 0.15   # Jaccard similarity on interests lists
ROLE_FIT_WEIGHT           = 0.15   # Student preferred_roles vs team preferred_roles
EXPERIENCE_FIT_WEIGHT     = 0.10   # Exact=1.0, adjacent=0.5
AVAILABILITY_WEIGHT       = 0.10   # Exact=1.0, else 0.3
COLLABORATION_WEIGHT      = 0.10   # Exact=1.0, partial if "comfortable" in either
TEAM_SIZE_FIT_WEIGHT      = 0.05   # abs(student.preferred_team_size - team total size) scaled

# Score scaling
MIN_SCORE = 30
MAX_SCORE = 98
