"""Unit boundary: Pint at I/O, canonical floats in kernels."""

from __future__ import annotations

from typing import Any

import pint

from lnpilot.core.exceptions import UnitError

# Canonical internal units (numeric kernels use these magnitudes)
CANONICAL = {
    "mass": "ug",
    "amount": "nmol",
    "volume": "mL",
    "concentration_mass": "mg/mL",
    "concentration_mass_ug": "ug/mL",
    "flow": "mL/min",
    "time": "min",
    "molar_mass": "g/mol",
}

_ureg: pint.UnitRegistry = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
try:
    _ureg.formatter.default_format = "~P"
except Exception:  # older pint
    _ureg.default_format = "~P"
Q_ = _ureg.Quantity


def registry() -> pint.UnitRegistry:
    return _ureg


def parse_quantity(value: Any, default_unit: str | None = None) -> pint.Quantity:
    """Parse a number+unit string, Quantity, or bare number with default_unit."""
    if isinstance(value, pint.Quantity):
        return value
    if isinstance(value, (int, float)):
        if default_unit is None:
            raise UnitError(f"Bare number {value!r} needs a default_unit")
        return Q_(value, default_unit)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            raise UnitError("Empty quantity string")
        try:
            q = _ureg.parse_expression(s)
        except Exception as exc:
            raise UnitError(f"Cannot parse quantity {value!r}: {exc}") from exc
        if not isinstance(q, pint.Quantity):
            if default_unit is None:
                raise UnitError(f"Bare number string {value!r} needs a default_unit")
            return Q_(float(q), default_unit)
        return q
    raise UnitError(f"Unsupported quantity type: {type(value).__name__}")


def to_canonical(value: Any, kind: str, default_unit: str | None = None) -> float:
    """Convert to canonical magnitude for *kind* (see CANONICAL)."""
    if kind not in CANONICAL:
        raise UnitError(f"Unknown canonical kind: {kind!r}")
    unit = CANONICAL[kind]
    q = parse_quantity(value, default_unit=default_unit or unit)
    try:
        return float(q.to(unit).magnitude)
    except Exception as exc:
        raise UnitError(f"Cannot convert {value!r} to {unit}: {exc}") from exc


def format_quantity(magnitude: float, kind: str, precision: int = 6) -> str:
    unit = CANONICAL.get(kind, "")
    if precision is None:
        return f"{magnitude} {unit}".strip()
    return f"{magnitude:.{precision}g} {unit}".strip()
