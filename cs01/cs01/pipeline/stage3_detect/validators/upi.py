"""
UPI & VPA Validator
===================
Validates Indian Virtual Payment Addresses (UPI IDs) against NPCI-registered PSP handles.
Format: <username>@<handle>
"""

from __future__ import annotations
import re
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()

# Built-in fallback PSP handles
DEFAULT_PSP_HANDLES: set[str] = {
    "@sbi", "@oksbi", "@ybl", "@okaxis", "@axisbank",
    "@okhdfcbank", "@hdfc", "@icici", "@okicici", "@ibl",
    "@indus", "@kotak", "@kmbl", "@pnb", "@barodampay",
    "@paytm", "@ptyes", "@pthdfc", "@ptsbi", "@gpay",
    "@phonepe", "@apl", "@amazon", "@bhim", "@fbl",
    "@federal", "@rbl", "@upi", "@nsdl", "@airtel",
    "@fino", "@jio", "@jiomoney",
}

VPA_PATTERN = re.compile(r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$")


def load_psp_handles(policy_profiles_dir: str | Path | None = None) -> set[str]:
    """Load active PSP handles from YAML policy profile if available."""
    handles = set(DEFAULT_PSP_HANDLES)
    if policy_profiles_dir:
        p = Path(policy_profiles_dir) / "psp_handles.yaml"
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    data = yaml.load(fh)
                if isinstance(data, dict) and "handles" in data:
                    handles.update(h.lower() for h in data["handles"])
            except Exception:
                pass
    return handles


def validate_upi_id(candidate: str, handles: set[str] | None = None) -> tuple[bool, str]:
    """
    Validate a potential UPI/VPA string.
    Returns (is_valid, handle_or_reason).
    """
    cleaned = candidate.strip().lower()

    if not VPA_PATTERN.match(cleaned):
        return False, "invalid_vpa_format"

    active_handles = handles or DEFAULT_PSP_HANDLES
    parts = cleaned.split("@", 1)
    if len(parts) != 2:
        return False, "missing_at_symbol"

    handle = "@" + parts[1]
    if handle in active_handles:
        return True, f"valid ({handle})"

    return False, f"unrecognized_psp_handle ({handle})"
