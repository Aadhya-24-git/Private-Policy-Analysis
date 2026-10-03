import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class ArbitrationDetector(BaseRiskDetector):
    """
    Detector for mandatory binding arbitration, class action waivers,
    and jury trial waivers.
    """

    @property
    def category_name(self) -> str:
        return "arbitration"

    PATTERNS = [
        (re.compile(r"\b(mandatory\s+)?binding\s+arbitration\b", re.IGNORECASE), "binding arbitration"),
        (re.compile(r"\barbitration\s+agreement\b", re.IGNORECASE), "arbitration agreement"),
        (re.compile(r"\bdispute(s)?\s+(shall|will)\s+be\s+(resolved|settled)\s+by\s+arbitration\b", re.IGNORECASE), "disputes resolved by arbitration"),
        (re.compile(r"\bclass\s+action\s+waiver\b", re.IGNORECASE), "class action waiver"),
        (re.compile(r"\bwaive\s+(any\s+)?(right\s+to\s+a\s+)?(jury\s+trial|trial\s+by\s+jury)\b", re.IGNORECASE), "waiver of jury trial"),
        (re.compile(r"\btrial\s+by\s+jury\s+is\s+(hereby\s+)?waived\b", re.IGNORECASE), "jury trial waived"),
        (re.compile(r"\bwaive\s+(any\s+right\s+to\s+participate\s+in\s+a\s+)?class\s+action\b", re.IGNORECASE), "waiver of class action participation"),
        (re.compile(r"\bindividual\s+capacity\s+and\s+not\s+as\s+a\s+(plaintiff|class\s+member)\b", re.IGNORECASE), "prohibition on class representation"),
        (re.compile(r"\bamerican\s+arbitration\s+association\b", re.IGNORECASE), "American Arbitration Association"),
        (re.compile(r"\bjams\s+(rules|comprehensive|arbitration)\b", re.IGNORECASE), "JAMS arbitration rules"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\bnot\s+subject\s+to\s+arbitration\b", re.IGNORECASE),
        re.compile(r"\barbitration\s+is\s+optional\b", re.IGNORECASE),
        re.compile(r"\bdoes\s+not\s+require\s+arbitration\b", re.IGNORECASE),
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

        has_class_waiver = any("class" in m.lower() for m in matched)
        has_binding = any("binding" in m.lower() for m in matched)
        risk = RiskLevel.CRITICAL if (has_class_waiver and has_binding) else RiskLevel.HIGH

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause specifies mandatory binding arbitration or a waiver of jury trials "
                "and class action participation for resolving legal disputes."
            ),
            matched_patterns=matched,
        )
