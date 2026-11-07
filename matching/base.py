from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class MatchResult:
    user_id: int
    score: int  # 0 to 100
    reasons: List[str] = field(default_factory=list)
    complementary_skills: List[str] = field(default_factory=list)
    shared_interests: List[str] = field(default_factory=list)
    workstyle_compatibility: int = 75
    is_mentor_match: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "score": self.score,
            "reasons": self.reasons,
            "complementary_skills": self.complementary_skills,
            "shared_interests": self.shared_interests,
            "workstyle_compatibility": self.workstyle_compatibility,
            "is_mentor_match": self.is_mentor_match,
            "notes": self.notes
        }

class BaseMatcher(ABC):
    """
    Abstract Base Matcher interface for TeamUp.
    Any custom rule or ML-based matcher must inherit from this class
    and implement the match() method.
    """

    @abstractmethod
    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        """
        Calculates match scores and explanations between a user and a list of candidate users
        for a specific hackathon event.

        :param user: The current User model instance.
        :param event: The Event model instance being matched for.
        :param candidates: List of candidate User instances.
        :return: List of MatchResult objects sorted in descending order of score.
        """
        pass
