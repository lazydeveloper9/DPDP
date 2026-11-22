"""
ScanConfig — parsed and validated cs01.yaml configuration.
Loaded once at CLI startup; passed to every pipeline stage via the runner.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ThirdScheduleFlags(BaseModel):
    health_data: bool = False
    financial_data: bool = False
    biometric_data: bool = False
    children_data: bool = False


class ApprovedProcessor(BaseModel):
    name: str
    services: list[str] = Field(default_factory=list)


class EngineConfig(BaseModel):
    tree_sitter: bool = True
    opengrep: bool = False
    ai_triage: bool = False
    ai_triage_endpoint: Optional[str] = None   # local vLLM endpoint URL


class BonusConfig(BaseModel):
    consent_audit: bool = False
    patch_generator: bool = False
    dast_probe: bool = False


class ScanConfig(BaseModel):
    """
    Fully validated configuration for a cs01 scan.
    Loaded from cs01.yaml and supplemented by CLI flags.
    """
    # Organisation profile
    org_name: str = "Unknown Org"
    entity_type: str = "data_fiduciary"
    is_sdf: bool = False
    third_schedule: ThirdScheduleFlags = Field(default_factory=ThirdScheduleFlags)
    approved_processors: list[ApprovedProcessor] = Field(default_factory=list)
    allowed_cross_border_regions: list[str] = Field(default_factory=list)

    # Scan settings
    scan_root: str = "."
    scan_layers: list[str] = Field(default_factory=lambda: ["code", "schema", "iac", "secrets"])
    fail_on: str = "high"                               # critical | high | medium | never
    output_formats: list[str] = Field(default_factory=lambda: ["sarif", "json", "html"])
    output_dir: str = "./cs01-reports"
    dpdpignore_path: Optional[str] = None               # path to .dpdpignore file
    baseline_path: Optional[str] = None                 # path to .cs01-baseline.json
    diff_base: Optional[str] = None                     # git ref for --diff-base

    # Engine
    engine: EngineConfig = Field(default_factory=EngineConfig)

    # Bonus modules
    bonus: BonusConfig = Field(default_factory=BonusConfig)

    # Policy profiles directory
    policy_profiles_dir: str = "./policy_profiles"

    # Debug / developer flags
    save_stage_output: bool = False       # saves intermediate JSONs to output_dir
    debug: bool = False
    strict_test_scanning: bool = False    # if True, PII in test files gets full severity

    @property
    def approved_processor_names(self) -> list[str]:
        return [p.name.lower() for p in self.approved_processors]
