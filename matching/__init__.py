from app.config import MATCHER_TYPE
from matching.base import BaseMatcher, MatchResult
from matching.rule_based import RuleBasedMatcher
from matching.ml_matcher import MLMatcher

def get_matcher() -> BaseMatcher:
    """
    Returns matcher instance based on MATCHER env var:
    - 'rule_based': weighted scoring algorithm (default)
    - 'ml': sentence-transformers model with rule-based fallback
    """
    if MATCHER_TYPE == "ml":
        return MLMatcher()
    return RuleBasedMatcher()

__all__ = ["BaseMatcher", "MatchResult", "RuleBasedMatcher", "MLMatcher", "get_matcher"]
