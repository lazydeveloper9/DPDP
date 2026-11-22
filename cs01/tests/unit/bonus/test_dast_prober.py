"""
Unit tests for DAST live probing guardrails and report output.
"""

import pytest
from cs01.bonus.dast_prober import run_dast_probe


def test_dast_probe_requires_explicit_opt_in():
    """Verify that probing without --allow-live-probe raises PermissionError."""
    with pytest.raises(PermissionError, match="--allow-live-probe"):
        run_dast_probe("https://example.com", allow_live_probe=False)
