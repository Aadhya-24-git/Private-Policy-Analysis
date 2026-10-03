import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class AutoRenewalDetector(BaseRiskDetector):
    """
    Detector for automatic renewal and recurring billing mechanisms.
    Identifies clauses where subscriptions continue without requiring
    affirmative opt-in at each renewal period.
    """

    @property
    def category_name(self) -> str:
        return "auto_renewal"

    PATTERNS = [
        (re.compile(r"\bautomatically\s+renew(s|ed|ing)?\b", re.IGNORECASE), "automatically renews"),
        (re.compile(r"\bautomatic(ally)?\s+renewal\b", re.IGNORECASE), "automatic renewal"),
        (re.compile(r"\brenew(s|ed|ing)?\s+automatically\b", re.IGNORECASE), "renews automatically"),
        (re.compile(r"\brenews\s+for\s+successive\s+(periods|terms|months|years)\b", re.IGNORECASE), "renews for successive terms"),
        (re.compile(r"\bcontinuous\s+subscription\b", re.IGNORECASE), "continuous subscription"),
        (re.compile(r"\brecurring\s+(subscription|billing|charge|fee|basis)\b", re.IGNORECASE), "recurring billing"),
        (re.compile(r"\bauto-renew(al|s|ing)?\b", re.IGNORECASE), "auto-renew"),
        (re.compile(r"\bconverted\s+to\s+a\s+paid\s+subscription\b", re.IGNORECASE), "converted to paid subscription"),
        (re.compile(r"\brenews\s+each\s+(month|year|period)\s+until\s+(you\s+)?cancel\b", re.IGNORECASE), "renews until cancelled"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\b(does\s+not|do\s+not|will\s+not|never)\s+automatically\s+renew\b", re.IGNORECASE),
        re.compile(r"\bno\s+automatic\s+renewal\b", re.IGNORECASE),
        re.compile(r"\bnot\s+subject\s+to\s+automatic\s+renewal\b", re.IGNORECASE),
    ]

    def detect(self, clause_text: str) -> Optional[DetectionResult]:
        if not clause_text:
            return None

        # Check for explicit negation
        for neg in self.NEGATION_PATTERNS:
            if neg.search(clause_text):
                return None

        matched: List[str] = []
        for pattern, label in self.PATTERNS:
            if pattern.search(clause_text):
                matched.append(label)

        if not matched:
            return None

        # Higher risk if successive renewal or recurring billing without explicit advance notice
        is_successive = any("successive" in m or "converted" in m for m in matched)
        risk = RiskLevel.HIGH if is_successive else RiskLevel.MEDIUM

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause indicates that subscriptions or services renew automatically on a recurring "
                "basis without requiring affirmative manual consent at each renewal period."
            ),
            matched_patterns=matched,
        )
