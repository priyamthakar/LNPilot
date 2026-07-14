"""Plate map validation and well role assignment."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from lnpilot.core.exceptions import PlateMapError, UnitError
from lnpilot.core.units import to_canonical
from lnpilot.core.validation import require_unique

# well, role, group_id, concentration, concentration_unit, dilution_factor, sample_id
REQUIRED_COLS = {"well", "role"}


def _norm_well(well: str) -> str:
    w = well.strip().upper().replace(" ", "")
    if not w:
        raise PlateMapError("Empty well id")
    return w


def load_plate_map(path: str | Path | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load plate map from CSV path or list of dicts."""
    if isinstance(path, list):
        rows = path
    else:
        p = Path(path)
        if not p.exists():
            raise PlateMapError(f"Plate map not found: {p}")
        with p.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise PlateMapError("Plate map CSV has no header")
            fields = {h.strip().lower() for h in reader.fieldnames}
            missing = REQUIRED_COLS - fields
            if missing:
                raise PlateMapError(f"Plate map missing columns: {sorted(missing)}")
            rows = []
            for raw in reader:
                rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()})

    if not rows:
        raise PlateMapError("Plate map is empty")

    wells = [_norm_well(str(r.get("well", ""))) for r in rows]
    try:
        require_unique(wells, label="well")
    except Exception as exc:
        raise PlateMapError(str(exc)) from exc

    allowed_roles = {
        "blank",
        "standard",
        "free",
        "total",
        "sample",
        "empty",
        "other",
    }
    out: list[dict[str, Any]] = []
    for r, well in zip(rows, wells):
        role = str(r.get("role", "")).strip().lower()
        if role not in allowed_roles:
            raise PlateMapError(
                f"Well {well}: unknown role {role!r}. "
                f"Allowed: {sorted(allowed_roles)}"
            )
        conc = r.get("concentration")
        if conc in (None, ""):
            conc = r.get("conc")
        dil = r.get("dilution_factor") or r.get("dilution") or "1"
        try:
            dil_f = float(dil) if dil != "" else 1.0
        except ValueError as exc:
            raise PlateMapError(f"Well {well}: bad dilution_factor {dil!r}") from exc
        if dil_f <= 0:
            raise PlateMapError(f"Well {well}: dilution_factor must be > 0")

        conc_f = None
        entered_conc = None
        entered_unit = str(r.get("concentration_unit") or "ug/mL").strip()
        if conc not in (None, ""):
            try:
                entered_conc = float(str(conc))
                conc_f = to_canonical(
                    f"{entered_conc} {entered_unit}",
                    "concentration_mass_ug",
                )
            except (TypeError, ValueError, UnitError) as exc:
                raise PlateMapError(f"Well {well}: bad concentration {conc!r}") from exc
            if conc_f < 0:
                raise PlateMapError(f"Well {well}: concentration must be >= 0")

        out.append(
            {
                "well": well,
                "role": role,
                "group_id": str(r.get("group_id") or r.get("group") or "").strip() or None,
                "sample_id": str(r.get("sample_id") or r.get("sample") or "").strip() or None,
                "concentration": conc_f,
                "concentration_unit": "ug/mL",
                "entered_concentration": entered_conc,
                "entered_concentration_unit": entered_unit,
                "dilution_factor": dil_f,
                "batch_id": str(r.get("batch_id") or "").strip() or None,
            }
        )

    standards = [x for x in out if x["role"] == "standard"]
    if standards and any(s["concentration"] is None for s in standards):
        raise PlateMapError("Standard wells require concentration")

    return out


def index_by_well(plate_map: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["well"]: r for r in plate_map}
