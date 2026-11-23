"""
dpdp_auditor.engine.capability_detector — Facade for CS-01 Base Product Capability Detector.
"""

from cs01.pipeline.stage3_detect.capability_detector import (
    detect_product_capabilities,
    ProductCapabilityReport,
    StackCapabilities,
    PersonalDataInventoryItem,
    ImplementedControl,
    MissingControl,
)

__all__ = [
    "detect_product_capabilities",
    "ProductCapabilityReport",
    "StackCapabilities",
    "PersonalDataInventoryItem",
    "ImplementedControl",
    "MissingControl",
]
