"""Overage / recovery adjustments and mass-balance checks."""

from __future__ import annotations

from typing import Any

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.validation import require_non_negative, require_positive


def scale_for_process(
    target_rna_mass_ug: float,
    *,
    expected_recovery: float = 1.0,
    overage_fraction: float = 0.0,
) -> dict[str, float]:
    """Inflate RNA (and downstream lipids) for recovery and overage.

    planned = target / recovery * (1 + overage)
    recovery in (0, 1]; overage_fraction >= 0 (e.g. 0.1 = 10% overage).
    """
    target = require_positive("target_rna_mass_ug", target_rna_mass_ug)
    rec = require_positive("expected_recovery", expected_recovery)
    if rec > 1.0:
        raise ValidationError(f"expected_recovery must be <= 1, got {rec}")
    over = require_non_negative("overage_fraction", overage_fraction)
    planned = target / rec * (1.0 + over)
    return {
        "target_rna_mass_ug": target,
        "expected_recovery": rec,
        "overage_fraction": over,
        "planned_rna_mass_ug": planned,
        "process_scale_factor": planned / target,
    }


def check_lipid_mass_balance(
    components: list[dict[str, Any]],
    total_lipid_nmol: float,
    *,
    tol: float = 1e-6,
) -> dict[str, Any]:
    """Verify sum of component nmol equals total lipid nmol."""
    total = require_positive("total_lipid_nmol", total_lipid_nmol)
    s = sum(float(c["amount_nmol"]) for c in components)
    ok = abs(s - total) <= tol * max(total, 1.0)
    mass_ug_sum = sum(float(c["mass_ug"]) for c in components)
    return {
        "component_nmol_sum": s,
        "total_lipid_nmol": total,
        "nmol_residual": s - total,
        "balanced": ok,
        "total_lipid_mass_ug": mass_ug_sum,
        "tolerance": tol,
    }
