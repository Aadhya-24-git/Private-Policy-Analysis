from app.analysis.detectors.auto_renewal import AutoRenewalDetector
from app.analysis.detectors.hidden_fees import HiddenFeesDetector
from app.analysis.detectors.arbitration import ArbitrationDetector
from app.analysis.detectors.data_sharing import DataSharingDetector
from app.analysis.detectors.cancellation import CancellationDetector
from app.analysis.detectors.data_retention import DataRetentionDetector
from app.analysis.detectors.liability import LiabilityDetector

__all__ = [
    "AutoRenewalDetector",
    "HiddenFeesDetector",
    "ArbitrationDetector",
    "DataSharingDetector",
    "CancellationDetector",
    "DataRetentionDetector",
    "LiabilityDetector",
]
