"""Load plate-reader fluorescence exports."""

from __future__ import annotations

import csv
from pathlib import Path

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.validation import require_finite


def load_plate_signals(data: str | Path | dict[str, float]) -> dict[str, float]:
    """Return mapping well_id -> raw signal.

    CSV formats supported:
    - long: columns well, signal (or value/fluorescence/rfu)
    - matrix: first column row label (A,B,...), header 1..12
    """
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            out[str(k).strip().upper()] = require_finite(f"signal[{k}]", float(v))
        return out

    p = Path(data)
    if not p.exists():
        raise ValidationError(f"Plate data not found: {p}")

    suffix = p.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return _load_xlsx(p)
    return _load_csv(p)


def _load_csv(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        raise ValidationError("Empty plate data file")

    header = [c.strip() for c in rows[0]]
    header_l = [h.lower() for h in header]

    if "well" in header_l:
        # long format
        f.seek(0) if False else None
        with path.open(newline="", encoding="utf-8-sig") as f:
            dict_reader = csv.DictReader(f)
            fields = {h.strip().lower(): h for h in (dict_reader.fieldnames or [])}
            sig_key = None
            for cand in ("signal", "value", "fluorescence", "rfu", "raw"):
                if cand in fields:
                    sig_key = fields[cand]
                    break
            well_key = fields.get("well")
            if not well_key or not sig_key:
                raise ValidationError(
                    "Long-format plate CSV needs 'well' and a signal column "
                    "(signal|value|fluorescence|rfu|raw)"
                )
            out: dict[str, float] = {}
            for row in dict_reader:
                well = str(row[well_key]).strip().upper()
                out[well] = require_finite(f"signal[{well}]", float(row[sig_key]))
            return out

    # matrix format: col0 = row letter, rest = columns
    out = {}
    col_ids = header[1:]
    for row in rows[1:]:
        if not row:
            continue
        row_id = row[0].strip().upper()
        for j, col in enumerate(col_ids):
            if j + 1 >= len(row) or row[j + 1].strip() == "":
                continue
            well = f"{row_id}{str(col).strip()}"
            out[well] = require_finite(f"signal[{well}]", float(row[j + 1]))
    if not out:
        raise ValidationError("No signals parsed from plate matrix")
    return out


def _load_xlsx(path: Path) -> dict[str, float]:
    try:
        import openpyxl
    except ImportError as exc:
        raise ValidationError(
            "Reading XLSX requires optional dependency: pip install lnpilot[plate]"
        ) from exc
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        raise ValidationError("Empty XLSX plate data")
    # write temp-like structure via csv logic
    str_rows = [["" if c is None else str(c) for c in r] for r in rows]
    # reuse matrix/long detection
    header = [c.strip() for c in str_rows[0]]
    header_l = [h.lower() for h in header]
    if "well" in header_l:
        well_i = header_l.index("well")
        sig_i = None
        for cand in ("signal", "value", "fluorescence", "rfu", "raw"):
            if cand in header_l:
                sig_i = header_l.index(cand)
                break
        if sig_i is None:
            raise ValidationError("XLSX long format needs a signal column")
        out: dict[str, float] = {}
        for r in str_rows[1:]:
            if well_i >= len(r) or sig_i >= len(r):
                continue
            well = r[well_i].strip().upper()
            if not well:
                continue
            out[well] = require_finite(f"signal[{well}]", float(r[sig_i]))
        return out
    out = {}
    col_ids = header[1:]
    for row in str_rows[1:]:
        if not row:
            continue
        row_id = row[0].strip().upper()
        for j, col in enumerate(col_ids):
            if j + 1 >= len(row) or row[j + 1].strip() == "":
                continue
            well = f"{row_id}{str(col).strip()}"
            out[well] = require_finite(f"signal[{well}]", float(row[j + 1]))
    return out
