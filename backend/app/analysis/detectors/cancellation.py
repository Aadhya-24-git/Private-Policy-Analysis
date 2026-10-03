import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class CancellationDetector(BaseRiskDetector):
    """
    Detector for account or subscription cancellation stipulations,
    notice windows, penalty fees, and restrictive conditions.
    """

    @property
    def category_name(self) -> str:
        return "cancellation"

    PATTERNS = [
        (re.compile(r"\b(must\s+)?cancel\s+at\s+least\s+\d+\s+(days|hours)\s+(in\s+advance|prior|before)\b", re.IGNORECASE), "advance notice cancellation requirement"),
        (re.compile(r"\bcancellation\s+fee(s)?\b", re.IGNORECASE), "cancellation fee"),
        (re.compile(r"\bearly\s+termination\s+(fee|charge|penalty)\b", re.IGNORECASE), "early termination penalty"),
        (re.compile(r"\bnon-refundable\s+upon\s+(cancellation|termination)\b", re.IGNORECASE), "non-refundable upon cancellation"),
        (re.compile(r"\bwritten\s+notice\s+to\s+cancel\b", re.IGNORECASE), "written notice to cancel"),
        (re.compile(r"\bto\s+cancel\s+your\s+(subscription|account|membership)\b", re.IGNORECASE), "cancellation procedure"),
        (re.compile(r"\bno\s+refunds\s+(will\s+be\s+issued\s+)?for\s+(unused|partial|early)\b", re.IGNORECASE), "no refunds for partial periods"),
        (re.compile(r"\bcancellation\s+will\s+(only\s+)?take\s+effect\s+at\s+the\s+end\s+of\b", re.IGNORECASE), "delayed cancellation effect"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\bcancel\s+at\s+any\s+time\s+without\s+(any\s+)?(fee|penalty|charge)\b", re.IGNORECASE),
        re.compile(r"\bfree\s+cancellation\b", re.IGNORECASE),
        re.compile(r"\bno\s+cancellation\s+fee\b", re.IGNORECASE),
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

        has_penalty = any("fee" in m.lower() or "penalty" in m.lower() or "non-refundable" in m.lower() for m in matched)
        risk = RiskLevel.HIGH if has_penalty else RiskLevel.MEDIUM

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause specifies conditions, advance notice windows, penalty fees, "
                "or restrictions governing account or subscription cancellation."
            ),
            matched_patterns=matched,
        )
