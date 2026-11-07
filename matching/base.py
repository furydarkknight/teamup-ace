from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class MatchResult:
    user_id: int            # candidate user id (or student id)
    team_id: Optional[int] = None  # filled for student->team matches
    score: int = 50         # 0 to 100
    reasons: List[str] = field(default_factory=list)
    complementary_skills: List[str] = field(default_factory=list)
    shared_interests: List[str] = field(default_factory=list)
    missing_skills_covered: List[str] = field(default_factory=list)
    workstyle_compatibility: int = 75
    is_mentor_match: bool = False
    notes: Optional[str] = None
    breakdown: Dict[str, Any] = field(default_factory=dict)
    engine: str = "Rule-based engine"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "team_id": self.team_id,
            "score": self.score,
            "reasons": self.reasons,
            "complementary_skills": self.complementary_skills,
            "shared_interests": self.shared_interests,
            "missing_skills_covered": self.missing_skills_covered,
            "workstyle_compatibility": self.workstyle_compatibility,
            "is_mentor_match": self.is_mentor_match,
            "notes": self.notes,
            "breakdown": self.breakdown,
            "engine": self.engine
        }

class BaseMatcher(ABC):
    """
    Abstract Base Matcher for TeamUp.
    Implementations must provide both match directions:
    1. match() - user vs candidate users (original event-based matching)
    2. match_student_to_teams() - student->teams bi-directional
    3. match_team_to_students() - team->students bi-directional
    """

    @abstractmethod
    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        """Original event-based student<->student matching."""
        pass

    @abstractmethod
    def match_student_to_teams(self, student: Any, teams: List[Any]) -> List[MatchResult]:
        """
        Score each team for a given student.
        Returns MatchResult with team_id set, user_id = student.id.
        Sorted descending by score.
        """
        pass

    @abstractmethod
    def match_team_to_students(self, team: Any, students: List[Any]) -> List[MatchResult]:
        """
        Score each student for a given team.
        Returns MatchResult with user_id = student.id, team_id = team.id.
        Sorted descending by score.
        """
        pass
