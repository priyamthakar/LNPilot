"""Assay QC flags."""

from __future__ import annotations

from typing import Any

from lnpilot.characterize.calibration import LinearCalibration


def evaluate_calibration_qc(cal: LinearCalibration, *, min_r2: float = 0.99) -> list[str]:
    flags: list[str] = []
    if cal.r_squared < min_r2:
        flags.append(f"Calibration R²={cal.r_squared:.4f} below {min_r2}")
    if abs(cal.slope) < 1e-12:
        flags.append("Calibration slope near zero")
    return flags


def evaluate_ee_qc(ee_fraction: float | None) -> list[str]:
    if ee_fraction is None:
        return ["EE not calculated"]
    flags: list[str] = []
    if ee_fraction < 0:
        flags.append(f"Physically implausible EE% < 0 ({100 * ee_fraction:.1f}%)")
    if ee_fraction > 1.0:
        flags.append(f"Physically implausible EE% > 100 ({100 * ee_fraction:.1f}%)")
    return flags


def evaluate_range_qc(conc: float, cal: LinearCalibration) -> list[str]:
    if not cal.in_range(conc):
        return [
            f"Concentration {conc:g} outside calibration range "
            f"[{cal.x_min:g}, {cal.x_max:g}]"
        ]
    return []


def summarize_qc(flags: list[str]) -> dict[str, Any]:
    if not flags:
        return {"status": "ok", "flags": []}
    # fail if any "implausible" or near-zero slope
    fail_kw = ("implausible", "near zero", "near-zero", "zero")
    status = "fail" if any(any(k in f.lower() for k in fail_kw) for f in flags) else "warning"
    return {"status": status, "flags": flags}
