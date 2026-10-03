import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class DataRetentionDetector(BaseRiskDetector):
    """
    Detector for extended, indefinite, or persistent data retention clauses.
    Identifies terms where user data continues to be held after account closure.
    """

    @property
    def category_name(self) -> str:
        return "data_retention"

    PATTERNS = [
        (re.compile(r"\bretain(s|ed|ing)?\s+(your\s+)?(personal\s+|user\s+)?(data|information)\s+(indefinitely|permanently)\b", re.IGNORECASE), "indefinite data retention"),
        (re.compile(r"\bkeep\s+(your\s+)?(data|information)\s+(indefinitely|for\s+as\s+long\s+as)\b", re.IGNORECASE), "perpetual retention"),
        (re.compile(r"\bretain(s|ed|ing)?\s+.*?\b(even\s+)?after\s+(you\s+)?(delete|close|terminate)\b", re.IGNORECASE), "post-deletion data retention"),
        (re.compile(r"\bbackup\s+(copies|archives)\s+may\s+persist\b", re.IGNORECASE), "persistent backup retention"),
        (re.compile(r"\bretained\s+for\s+(legitimate\s+business|analytical|internal)\s+purposes\b", re.IGNORECASE), "retention for business purposes"),
        (re.compile(r"\bstore(d)?\s+(your\s+)?information\s+(indefinitely|without\s+time\s+limit)\b", re.IGNORECASE), "storage without time limits"),
        (re.compile(r"\bdata\s+retention\s+policy\b", re.IGNORECASE), "data retention policy"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\b(permanently\s+)?(purged|deleted|erased)\s+(within|after)\s+\d+\s+(days|hours)\b", re.IGNORECASE),
        re.compile(r"\bimmediately\s+deleted\s+upon\s+(account\s+)?(closure|deletion)\b", re.IGNORECASE),
        re.compile(r"\bno\s+data\s+is\s+retained\b", re.IGNORECASE),
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

        is_indefinite = any("indefinite" in m.lower() or "perpetual" in m.lower() or "without time" in m.lower() for m in matched)
        risk = RiskLevel.HIGH if is_indefinite else RiskLevel.MEDIUM

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause indicates that user data or records may be retained indefinitely, "
                "for extended durations, or in residual backup systems following account termination."
            ),
            matched_patterns=matched,
        )
