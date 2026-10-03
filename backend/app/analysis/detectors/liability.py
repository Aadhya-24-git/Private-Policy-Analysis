import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class LiabilityDetector(BaseRiskDetector):
    """
    Detector for limitation of liability, aggregate liability caps,
    disclaimers of consequential damages, and broad indemnification requirements.
    """

    @property
    def category_name(self) -> str:
        return "liability"

    PATTERNS = [
        (re.compile(r"\blimitation\s+of\s+liability\b", re.IGNORECASE), "limitation of liability"),
        (re.compile(r"\bin\s+no\s+event\s+shall\s+(the\s+company|we|our|licensors|affiliates)\s+be\s+liable\b", re.IGNORECASE), "total exclusion of liability"),
        (re.compile(r"\bdisclaim(s|ed|ing)?\s+(all\s+)?(warranties|liability)\b", re.IGNORECASE), "warranty/liability disclaimer"),
        (re.compile(r"\b[\"']?as\s+is[\"']?\s+and\s+[\"']?as\s+available[\"']?\b", re.IGNORECASE), "as-is / as-available provision"),
        (re.compile(r"\bwithout\s+warranties\s+of\s+any\s+kind\b", re.IGNORECASE), "disclaimer of all warranties"),
        (re.compile(r"\bindirect,\s+incidental,\s+(special,\s+)?consequential(\s+or\s+punitive)?\s+damages\b", re.IGNORECASE), "exclusion of consequential/incidental damages"),
        (re.compile(r"\bshall\s+not\s+exceed\s+(the\s+amount\s+paid|fifty\s+dollars|one\s+hundred\s+dollars|\$\d+)\b", re.IGNORECASE), "strict monetary liability cap"),
        (re.compile(r"\bhold\s+harmless\s+and\s+indemnify\b", re.IGNORECASE), "indemnification requirement"),
        (re.compile(r"\bat\s+your\s+sole\s+risk\b", re.IGNORECASE), "use at sole risk"),
        (re.compile(r"\bno\s+liability\s+for\s+(any\s+)?(loss\s+of\s+data|security\s+breaches|unauthorized\s+access)\b", re.IGNORECASE), "no liability for data loss or breach"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\bdoes\s+not\s+exclude\s+or\s+limit\s+our\s+liability\s+for\s+gross\s+negligence\b", re.IGNORECASE),
        re.compile(r"\bwe\s+accept\s+full\s+liability\b", re.IGNORECASE),
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

        has_strict_cap = any("strict monetary" in m.lower() or "data loss" in m.lower() for m in matched)
        has_total_exclusion = any("total exclusion" in m.lower() for m in matched)

        if has_strict_cap or has_total_exclusion:
            risk = RiskLevel.CRITICAL
        else:
            risk = RiskLevel.HIGH

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause disclaims warranties, excludes liability for consequential or incidental damages, "
                "or imposes aggregate monetary caps on legal recovery."
            ),
            matched_patterns=matched,
        )
