from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from app.models.finding import RiskLevel


@dataclass
class DetectionResult:
    """
    Standardized payload generated when a detector identifies a policy risk pattern.
    """
    category: str
    risk_level: RiskLevel
    explanation: str
    matched_patterns: List[str] = field(default_factory=list)


class BaseRiskDetector(ABC):
    """
    Abstract base class for deterministic rule-based policy risk detectors.
    Operates strictly on the verbatim stored clause text without LLM hallucinations.
    """

    @property
    @abstractmethod
    def category_name(self) -> str:
        """Standardized category identifier (e.g., 'auto_renewal', 'arbitration')."""
        pass

    @abstractmethod
    def detect(self, clause_text: str) -> Optional[DetectionResult]:
        """
        Analyze the raw clause text. Returns a DetectionResult if a risk
        pattern is matched, or None otherwise.
        """
        pass
