from app.config import MATCHER_TYPE
from matching.base import BaseMatcher, MatchResult
from matching.rule_based import RuleBasedMatcher
from matching.ml_matcher import MLMatcher

def get_matcher() -> BaseMatcher:
    """
    Returns matcher instance based on config MATCHER:
    - 'rule_based': weighted scoring algorithm
    - 'ml': loads models/matcher.pkl with rule-based fallback
    """
    if MATCHER_TYPE == "ml":
        return MLMatcher()
    return RuleBasedMatcher()

__all__ = ["BaseMatcher", "MatchResult", "RuleBasedMatcher", "MLMatcher", "get_matcher"]
