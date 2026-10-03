import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class HiddenFeesDetector(BaseRiskDetector):
    """
    Detector for hidden, unexpected, or discretionary fee clauses.
    Identifies terms specifying additional fees, unilateral rate modifications,
    administrative costs, or price increases.
    """

    @property
    def category_name(self) -> str:
        return "hidden_fees"

    PATTERNS = [
        (re.compile(r"\badditional\s+(fee|fees|charge|charges|cost|costs)\b", re.IGNORECASE), "additional fees"),
        (re.compile(r"\bsubject\s+to\s+change\s+without\s+(prior\s+)?notice\b", re.IGNORECASE), "rates subject to change without notice"),
        (re.compile(r"\bfees\s+are\s+subject\s+to\s+change\b", re.IGNORECASE), "fees subject to change"),
        (re.compile(r"\badministrative\s+(fee|fees|charge|charges)\b", re.IGNORECASE), "administrative fees"),
        (re.compile(r"\bprocessing\s+fee(s)?\b", re.IGNORECASE), "processing fee"),
        (re.compile(r"\blate\s+(fee|fees|payment\s+fee)\b", re.IGNORECASE), "late fees"),
        (re.compile(r"\bnon-refundable\s+(fee|fees|deposit|charge)\b", re.IGNORECASE), "non-refundable fees"),
        (re.compile(r"\bprice(s)?\s+(may\s+)?increase\b", re.IGNORECASE), "price increase"),
        (re.compile(r"\breactivation\s+fee\b", re.IGNORECASE), "reactivation fee"),
        (re.compile(r"\brestocking\s+fee\b", re.IGNORECASE), "restocking fee"),
        (re.compile(r"\bunannounced\s+(fee|fees|charge|charges)\b", re.IGNORECASE), "unannounced charges"),
        (re.compile(r"\bdiscretionary\s+(fee|fees|charge|charges)\b", re.IGNORECASE), "discretionary charges"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\bno\s+additional\s+(fee|fees|charge|charges|cost|costs)\b", re.IGNORECASE),
        re.compile(r"\bwithout\s+(any\s+)?additional\s+(fee|fees|charge|charges)\b", re.IGNORECASE),
        re.compile(r"\bfree\s+of\s+charge\b", re.IGNORECASE),
        re.compile(r"\bno\s+hidden\s+fees\b", re.IGNORECASE),
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

        is_unilateral = any("without notice" in m or "unannounced" in m or "discretionary" in m for m in matched)
        risk = RiskLevel.HIGH if is_unilateral else RiskLevel.MEDIUM

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause references potential additional fees, surcharges, administrative adjustments, "
                "or price modifications that may be incurred beyond base rates."
            ),
            matched_patterns=matched,
        )
