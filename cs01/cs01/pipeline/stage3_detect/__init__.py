"""cs01.pipeline.stage3_detect — PII detection, source-sink-guard flow tracing, capability detector, and Opengrep bridge."""
from .detector import run_detect
from .opengrep_bridge import OpengrepBridge
from .capability_detector import detect_product_capabilities

__all__ = ["run_detect", "OpengrepBridge", "detect_product_capabilities"]
