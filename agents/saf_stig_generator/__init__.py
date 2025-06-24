"""SAF STIG Generator - Automated MITRE SAF baseline generation."""

__version__ = "0.1.0"
__author__ = "SAF Development Team"
__description__ = (
    "An autonomous system built using the Google Agent Development Kit (ADK)"
)

# Re-export main components
from .coding import CodingAgent
from .common.config import ensure_dir, get_artifacts_dir, get_download_dir
from .orchestrator import OrchestratorAgent
from .qa import QualityAssuranceAgent

__all__ = [
    "OrchestratorAgent",
    "CodingAgent",
    "QualityAssuranceAgent",
    "get_artifacts_dir",
    "get_download_dir",
    "ensure_dir",
]
