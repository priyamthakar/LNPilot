"""CSV export helpers."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence


def write_rows(path: str | Path, rows: Sequence[dict[str, Any]]) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return p
    # union of keys, stable order from first row then extras
    keys: list[str] = list(rows[0].keys())
    for r in rows[1:]:
        for k in r:
            if k not in keys:
                keys.append(k)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})
    return p


def lipids_to_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return list(plan.get("lipids") or plan.get("stocks") or [])
