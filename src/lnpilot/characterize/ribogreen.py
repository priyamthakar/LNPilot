"""Flagship workflow: analyze_ribogreen_plate()."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from lnpilot.characterize.calibration import fit_linear
from lnpilot.characterize.plate_map import index_by_well, load_plate_map
from lnpilot.characterize.qc import (
    evaluate_calibration_qc,
    evaluate_ee_qc,
    evaluate_range_qc,
    summarize_qc,
)
from lnpilot.core.exceptions import ValidationError
from lnpilot.core.models import AssayRun, Result
from lnpilot.core.provenance import Provenance
from lnpilot.core.units import to_canonical
from lnpilot.io.plate_reader import load_plate_signals


def _mean_std(vals: list[float]) -> tuple[float, float | None, int]:
    a = np.asarray(vals, dtype=float)
    n = len(a)
    if n == 0:
        raise ValidationError("Empty replicate group")
    mean = float(np.mean(a))
    sd = float(np.std(a, ddof=1)) if n > 1 else None
    return mean, sd, n


def analyze_ribogreen_plate(
    data: str | Path | dict[str, float],
    plate_map: str | Path | list[dict[str, Any]],
    *,
    calibration: str = "linear",
    weighting: str | None = None,
    assay_id: str = "ribogreen-001",
    input_rna_mass: Any = None,
    sample_volume: Any = None,
    min_r2: float = 0.99,
    operator: str | None = None,
) -> AssayRun:
    """Analyze RiboGreen plate: calibration, free/total RNA, EE%, recovery.

    Plate map roles: blank, standard, free, total (and optional sample).
    Pair free/total via group_id or sample_id.
    """
    if calibration != "linear":
        raise ValidationError("v0.1 only supports calibration='linear'")

    warnings: list[str] = []
    assumptions: list[str] = [
        "RiboGreen measures dye-accessible RNA, not full-length or functional RNA.",
        "EE% = (total - free) / total after blank correction, dilution, and calibration.",
        "Matrix, surfactant, and timing effects can bias fluorescence.",
        "High EE% alone does not imply potency or correct biodistribution.",
    ]

    pmap = load_plate_map(plate_map)
    by_well = index_by_well(pmap)
    signals = load_plate_signals(data)

    # Match wells
    missing = [w for w in by_well if w not in signals]
    if missing:
        raise ValidationError(f"Plate data missing wells from map: {missing[:10]}")

    # Blanks
    blank_wells = [r for r in pmap if r["role"] == "blank"]
    if not blank_wells:
        warnings.append("No blank wells; using blank = 0")
        blank_mean, blank_sd, blank_n = 0.0, None, 0
    else:
        blank_vals = [signals[r["well"]] for r in blank_wells]
        blank_mean, blank_sd, blank_n = _mean_std(blank_vals)

    def corr(well: str) -> float:
        return float(signals[well]) - blank_mean

    # Standards
    std_rows = [r for r in pmap if r["role"] == "standard"]
    if len(std_rows) < 2:
        raise ValidationError("Need at least 2 standard wells")

    # Aggregate standards by concentration (replicates)
    # Convention: plate_map concentration = concentration in the assay well.
    std_groups: dict[float, list[float]] = defaultdict(list)
    for r in std_rows:
        x = float(r["concentration"])
        std_groups[x].append(corr(r["well"]))

    xs: list[float] = []
    ys: list[float] = []
    for conc in sorted(std_groups):
        m, _, _ = _mean_std(std_groups[conc])
        xs.append(conc)
        ys.append(m)

    weights = None
    if weighting == "1/x":
        weights = [1.0 / c if c != 0 else 1.0 for c in xs]
        if any(c == 0 for c in xs):
            warnings.append("1/x weighting: zero-concentration standard got weight 1")
    elif weighting == "1/x^2":
        weights = [1.0 / (c * c) if c != 0 else 1.0 for c in xs]
    elif weighting is not None:
        raise ValidationError("weighting must be None, '1/x', or '1/x^2'")

    cal = fit_linear(xs, ys, weights=weights)
    qc_flags = evaluate_calibration_qc(cal, min_r2=min_r2)

    # Samples: free / total paired by group_id or sample_id
    free_rows = [r for r in pmap if r["role"] == "free"]
    total_rows = [r for r in pmap if r["role"] == "total"]

    def key_of(r: dict[str, Any]) -> str:
        return r.get("group_id") or r.get("sample_id") or r["well"]

    free_by: dict[str, list[dict]] = defaultdict(list)
    total_by: dict[str, list[dict]] = defaultdict(list)
    for r in free_rows:
        free_by[key_of(r)].append(r)
    for r in total_rows:
        total_by[key_of(r)].append(r)

    keys = sorted(set(free_by) | set(total_by))
    sample_table: list[dict[str, Any]] = []
    results: list[Result] = []
    all_flags = list(qc_flags)

    for k in keys:
        row: dict[str, Any] = {"sample_key": k}

        def conc_from_rows(rows: list[dict]) -> tuple[float | None, float | None, int, list[str]]:
            if not rows:
                return None, None, 0, [f"No wells for {k}"]
            flags: list[str] = []
            concs = []
            for r in rows:
                sig = corr(r["well"])
                c_well = cal.predict_concentration(sig)
                c = c_well * r["dilution_factor"]
                flags.extend(evaluate_range_qc(c_well, cal))
                concs.append(c)
            mean, sd, n = _mean_std(concs)
            return mean, sd, n, flags

        free_c, free_sd, free_n, f_flags = conc_from_rows(free_by.get(k, []))
        tot_c, tot_sd, tot_n, t_flags = conc_from_rows(total_by.get(k, []))
        all_flags.extend(f_flags)
        all_flags.extend(t_flags)

        row["free_rna_ug_per_mL"] = free_c
        row["free_sd"] = free_sd
        row["free_n"] = free_n
        row["total_rna_ug_per_mL"] = tot_c
        row["total_sd"] = tot_sd
        row["total_n"] = tot_n

        ee = None
        encap = None
        if free_c is not None and tot_c is not None:
            if abs(tot_c) < 1e-15:
                all_flags.append(f"{k}: total RNA ~0; cannot compute EE")
            else:
                encap = tot_c - free_c
                ee = encap / tot_c
                ee_flags = evaluate_ee_qc(ee)
                all_flags.extend([f"{k}: {f}" for f in ee_flags])
        row["encapsulated_rna_ug_per_mL"] = encap
        row["ee_fraction"] = ee
        row["ee_percent"] = None if ee is None else 100.0 * ee

        batch_ids = []
        for r in free_by.get(k, []) + total_by.get(k, []):
            if r.get("batch_id"):
                batch_ids.append(r["batch_id"])
        row["batch_id"] = batch_ids[0] if batch_ids else None
        sample_table.append(row)

        if ee is not None:
            results.append(
                Result(
                    name=f"EE%{k}",
                    value=100.0 * ee,
                    unit="%",
                    replicate_count=min(free_n, tot_n) or None,
                    method="ribogreen_linear_calibration",
                    qc_status=summarize_qc(evaluate_ee_qc(ee))["status"],
                    warnings=evaluate_ee_qc(ee),
                    assumptions=assumptions[:2],
                )
            )

    recovery = None
    if input_rna_mass is not None and sample_volume is not None:
        mass_ug = to_canonical(input_rna_mass, "mass", default_unit="ug")
        vol_mL = to_canonical(sample_volume, "volume", default_unit="mL")
        # use mean total across samples if single sample group
        totals = [s["total_rna_ug_per_mL"] for s in sample_table if s["total_rna_ug_per_mL"] is not None]
        if totals and vol_mL > 0 and mass_ug > 0:
            recovered = float(np.mean(totals)) * vol_mL
            recovery = recovered / mass_ug
            results.append(
                Result(
                    name="RNA_recovery",
                    value=recovery,
                    unit="fraction",
                    method="total_rna_conc * sample_volume / input_mass",
                    qc_status="ok" if 0 <= recovery <= 1.2 else "warning",
                    warnings=[]
                    if 0 <= recovery <= 1.2
                    else [f"Recovery {recovery:.2%} outside 0–120%"],
                )
            )
            assumptions.append("Recovery uses mean total RNA concentration × sample_volume.")
    elif input_rna_mass is not None:
        warnings.append("input_rna_mass set without sample_volume; recovery not computed")

    qc = summarize_qc(all_flags)
    if qc["status"] != "ok":
        warnings.extend(qc["flags"])

    source_files = []
    if isinstance(data, (str, Path)):
        source_files.append({"role": "plate_reader", "path": str(data)})
    if isinstance(plate_map, (str, Path)):
        source_files.append({"role": "plate_map", "path": str(plate_map)})

    prov = Provenance.create(
        workflow_name="analyze_ribogreen_plate",
        assumptions=assumptions,
        warnings=warnings,
        source_files=source_files,
        operator=operator,
        method_id="characterize.ribogreen.v0.1",
    )

    batch_ids = sorted({s["batch_id"] for s in sample_table if s.get("batch_id")})

    return AssayRun(
        assay_id=assay_id,
        assay_type="ribogreen",
        batch_ids=batch_ids,
        raw_data_ref=str(data) if isinstance(data, (str, Path)) else None,
        plate_map={"wells": pmap},
        calibration=cal.to_dict(),
        dilution_scheme={
            "note": "Per-well dilution_factor applied after calibration invert",
        },
        replicates={
            "blank_n": blank_n,
            "blank_mean_signal": blank_mean,
            "blank_sd": blank_sd,
            "standard_levels": len(xs),
        },
        reagent_metadata={},
        qc=qc,
        results=results,
        sample_table=sample_table,
        warnings=warnings,
        assumptions=assumptions,
        provenance=prov,
    )
