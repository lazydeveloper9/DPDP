"""Stage 5 classifier — stub (implementation in sprint S5)."""
from cs01.models import RawFinding, ScoredFindingBundle, DpdpReadinessScore, ScanConfig

def run_classify(
    raw_findings: list[RawFinding],
    cfg: ScanConfig,
    **kwargs,
) -> ScoredFindingBundle:
    return ScoredFindingBundle(
        scan_id=kwargs.get("scan_id", ""),
        scan_timestamp=kwargs.get("scan_timestamp", ""),
        scan_root=kwargs.get("scan_root", ""),
        total_files_scanned=kwargs.get("total_files", 0),
        partial_scan=kwargs.get("partial_scan", False),
        partial_scan_details=kwargs.get("partial_details", []),
    )
