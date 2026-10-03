import re
from typing import Optional, List
from app.models.finding import RiskLevel
from app.analysis.base import BaseRiskDetector, DetectionResult


class DataSharingDetector(BaseRiskDetector):
    """
    Detector for user data sharing, third-party disclosure, data monetization,
    and advertising data transfers.
    """

    @property
    def category_name(self) -> str:
        return "data_sharing"

    PATTERNS = [
        (re.compile(r"\bshare(s|d|ing)?\s+(your\s+)?(personal\s+|user\s+)?(data|information)\s+with\s+(third|external|commercial|advertising)\b", re.IGNORECASE), "share personal data with third parties"),
        (re.compile(r"\bdisclose(s|d|ing)?\s+(your\s+)?(personal\s+|user\s+)?(data|information)\s+to\s+third\s+parties\b", re.IGNORECASE), "disclose data to third parties"),
        (re.compile(r"\bthird[- ]party\s+.*?\b(advertisers|marketers|vendors|partners|networks)\b", re.IGNORECASE), "third-party advertisers or partners"),
        (re.compile(r"\b(third[- ]party|external)\s+(advertising|marketing|commercial)\b", re.IGNORECASE), "third-party advertising"),
        (re.compile(r"\bsell(s|ing)?\s+(your\s+)?(personal\s+|user\s+)?(data|information)\b", re.IGNORECASE), "selling personal data"),
        (re.compile(r"\bmonetiz(e|ing|ation)\s+(your\s+)?(personal\s+|user\s+)?data\b", re.IGNORECASE), "data monetization"),
        (re.compile(r"\btargeted\s+(advertising|marketing|promotions)\b", re.IGNORECASE), "targeted advertising"),
        (re.compile(r"\btransfer(s|red|ring)?\s+(your\s+)?data\s+to\s+(third\s+parties|affiliates|partners)\b", re.IGNORECASE), "transfer data to third parties"),
        (re.compile(r"\bshare\s+(information|data)\s+for\s+commercial\s+purposes\b", re.IGNORECASE), "share data for commercial purposes"),
    ]

    NEGATION_PATTERNS = [
        re.compile(r"\b(do\s+not|does\s+not|never|will\s+not)\s+sell\s+(your\s+)?(personal\s+|user\s+)?(data|information)\b", re.IGNORECASE),
        re.compile(r"\b(do\s+not|does\s+not|never|will\s+not)\s+share\s+(your\s+)?(personal\s+|user\s+)?(data|information)\b", re.IGNORECASE),
        re.compile(r"\bno\s+third[- ]party\s+data\s+sharing\b", re.IGNORECASE),
        re.compile(r"\bwithout\s+(your\s+)?(prior\s+)?consent\b", re.IGNORECASE),
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

        is_selling = any("sell" in m.lower() or "monetiz" in m.lower() for m in matched)
        is_advertising = any("advertis" in m.lower() or "commercial" in m.lower() for m in matched) or bool(
            re.search(r"\b(advertis|marketing|commercial)\b", clause_text, re.IGNORECASE)
        )

        if is_selling:
            risk = RiskLevel.CRITICAL
        elif is_advertising:
            risk = RiskLevel.HIGH
        else:
            risk = RiskLevel.MEDIUM

        return DetectionResult(
            category=self.category_name,
            risk_level=risk,
            explanation=(
                "Clause states that user data or personal information may be shared with, "
                "transferred to, or monetized by external third parties, affiliates, or advertising partners."
            ),
            matched_patterns=matched,
        )
