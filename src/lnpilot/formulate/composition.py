"""Lipid composition normalization and total-lipid scaling."""

from __future__ import annotations

from typing import Any

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.validation import require_positive, require_unique


def normalize_composition(
    components: list[dict[str, Any]],
    *,
    ionizable_name: str | None = None,
) -> list[dict[str, Any]]:
    """Validate components and add entered_mol_percent + normalized_mol_percent.

    Each component needs: name, mol_percent, mw (g/mol).
    Optional: role (ionizable|helper|cholesterol|peg_lipid|other), ionizable_groups.
    """
    if not components:
        raise ValidationError("lipid_composition must not be empty")

    names = [str(c.get("name", "")).strip() for c in components]
    if any(not n for n in names):
        raise ValidationError("Every lipid component needs a non-empty name")
    require_unique(names, label="lipid name")

    total = 0.0
    cleaned: list[dict[str, Any]] = []
    for c in components:
        name = str(c["name"]).strip()
        mol = require_positive(f"mol_percent[{name}]", float(c["mol_percent"]))
        mw = require_positive(f"mw[{name}]", float(c["mw"]))
        role = str(c.get("role", "other"))
        groups = float(c.get("ionizable_groups", 1.0 if role == "ionizable" else 0.0))
        if groups < 0:
            raise ValidationError(f"ionizable_groups[{name}] must be >= 0")
        stock = c.get("stock_mg_per_mL")
        if stock is not None:
            stock = require_positive(f"stock[{name}]", float(stock))
        total += mol
        cleaned.append(
            {
                "name": name,
                "role": role,
                "entered_mol_percent": mol,
                "mw_g_per_mol": mw,
                "ionizable_groups": groups,
                "stock_mg_per_mL": stock,
            }
        )

    if total <= 0:
        raise ValidationError("Total mol% must be > 0")

    for c in cleaned:
        c["normalized_mol_percent"] = 100.0 * c["entered_mol_percent"] / total
        c["mol_fraction"] = c["normalized_mol_percent"] / 100.0

    # Identify ionizable
    ionizables = [c for c in cleaned if c["role"] == "ionizable"]
    if ionizable_name:
        match = [c for c in cleaned if c["name"] == ionizable_name]
        if not match:
            raise ValidationError(f"ionizable lipid {ionizable_name!r} not in composition")
        if match[0]["ionizable_groups"] <= 0:
            raise ValidationError(
                f"Ionizable lipid {ionizable_name!r} needs ionizable_groups > 0"
            )
    elif not ionizables:
        raise ValidationError(
            "Composition needs at least one component with role='ionizable' "
            "or pass ionizable_name="
        )
    elif len(ionizables) > 1 and ionizable_name is None:
        raise ValidationError(
            "Multiple ionizable lipids: pass ionizable_name= to select one for N/P"
        )

    return cleaned


def total_lipid_nmol_from_ionizable(
    ionizable_nmol: float,
    ionizable_mol_fraction: float,
) -> float:
    """Total lipid nmol given ionizable amount and its mol fraction."""
    n = require_positive("ionizable_nmol", ionizable_nmol)
    f = require_positive("ionizable_mol_fraction", ionizable_mol_fraction)
    if f > 1.0 + 1e-12:
        raise ValidationError(f"ionizable_mol_fraction must be <= 1, got {f}")
    return n / f


def component_amounts(
    components: list[dict[str, Any]],
    total_lipid_nmol: float,
) -> list[dict[str, Any]]:
    """Per-component nmol and mass_ug from total lipid nmol."""
    total = require_positive("total_lipid_nmol", total_lipid_nmol)
    out: list[dict[str, Any]] = []
    for c in components:
        nmol = total * c["mol_fraction"]
        # mass_ug = nmol * MW_g/mol * 1e-3  (nmol * g/mol = ng * 1e-9/1e-9 ... :
        # mol = nmol * 1e-9; mass_g = mol * MW; mass_ug = mass_g * 1e6
        # = nmol * 1e-9 * MW * 1e6 = nmol * MW * 1e-3
        mass_ug = nmol * c["mw_g_per_mol"] * 1e-3
        row = dict(c)
        row["amount_nmol"] = nmol
        row["mass_ug"] = mass_ug
        out.append(row)
    return out
