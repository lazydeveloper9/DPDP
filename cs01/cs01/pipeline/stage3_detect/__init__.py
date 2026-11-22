"""cs01.pipeline.stage3_detect — PII detection and source-sink-guard flow tracing."""
from .detector import run_detect

__all__ = ["run_detect"]
