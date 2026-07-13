"""Stock solution volume calculations."""

from __future__ import annotations

from typing import Any

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.validation import require_positive


def stock_volume_mL(mass_ug: float, stock_mg_per_mL: float) -> float:
    """Volume of stock (mL) for required mass.

    mass_mg = mass_ug / 1000; V_mL = mass_mg / stock_mg_per_mL
    """
    m = require_positive("mass_ug", mass_ug)
    c = require_positive("stock_mg_per_mL", stock_mg_per_mL)
    return (m / 1000.0) / c


def assign_stock_volumes(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add stock_volume_mL for each component that has stock_mg_per_mL."""
    out: list[dict[str, Any]] = []
    for c in components:
        row = dict(c)
        stock = c.get("stock_mg_per_mL")
        if stock is None:
            row["stock_volume_mL"] = None
            row["stock_warning"] = "No stock concentration provided"
        else:
            if c.get("mass_ug") is None:
                raise ValidationError(f"Component {c.get('name')} missing mass_ug")
            row["stock_volume_mL"] = stock_volume_mL(float(c["mass_ug"]), float(stock))
            row["stock_warning"] = None
        out.append(row)
    return out
