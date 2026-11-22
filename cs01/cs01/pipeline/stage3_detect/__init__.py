"""cs01.pipeline.stage3_detect — PII detection, source-sink-guard flow tracing, and Opengrep bridge."""
from .detector import run_detect
from .opengrep_bridge import OpengrepBridge

__all__ = ["run_detect", "OpengrepBridge"]
