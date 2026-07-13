"""Input validation helpers — fail clearly, never silent coerce."""

from __future__ import annotations

import math
from typing import Iterable

from lnpilot.core.exceptions import ValidationError


def require_finite(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")
    v = float(value)
    if not math.isfinite(v):
        raise ValidationError(f"{name} must be finite, got {value!r}")
    return v


def require_positive(name: str, value: float, *, allow_zero: bool = False) -> float:
    v = require_finite(name, value)
    if allow_zero:
        if v < 0:
            raise ValidationError(f"{name} must be >= 0, got {v}")
    else:
        if v <= 0:
            raise ValidationError(f"{name} must be > 0, got {v}")
    return v


def require_non_negative(name: str, value: float) -> float:
    return require_positive(name, value, allow_zero=True)


def require_in_range(
    name: str,
    value: float,
    low: float,
    high: float,
    *,
    inclusive: bool = True,
) -> float:
    v = require_finite(name, value)
    if inclusive:
        ok = low <= v <= high
    else:
        ok = low < v < high
    if not ok:
        raise ValidationError(f"{name} must be in [{low}, {high}], got {v}")
    return v


def require_unique(names: Iterable[str], label: str = "name") -> list[str]:
    seen: set[str] = set()
    dups: list[str] = []
    out: list[str] = []
    for n in names:
        if n in seen:
            dups.append(n)
        else:
            seen.add(n)
            out.append(n)
    if dups:
        raise ValidationError(f"Duplicate {label}(s): {sorted(set(dups))}")
    return out


def require_equal_length(*arrays: list | tuple, names: tuple[str, ...] | None = None) -> None:
    if not arrays:
        return
    n0 = len(arrays[0])
    for i, a in enumerate(arrays[1:], start=1):
        if len(a) != n0:
            labels = names or tuple(f"array{j}" for j in range(len(arrays)))
            raise ValidationError(
                f"Length mismatch: {labels[0]}={n0}, {labels[i]}={len(a)}"
            )
