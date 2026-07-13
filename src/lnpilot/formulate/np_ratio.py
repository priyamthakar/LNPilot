"""N/P ratio and RNA-phosphate calculations."""

from __future__ import annotations

from lnpilot.core.validation import require_positive

# Average nucleotide residue MW for mass-based phosphate approximation (g/mol)
DEFAULT_AVG_NT_MW = 330.0


def rna_phosphate_nmol(
    rna_mass_ug: float,
    *,
    avg_nt_mw_g_per_mol: float = DEFAULT_AVG_NT_MW,
) -> float:
    """Phosphate amount (nmol) from RNA mass using average nucleotide MW.

    Each nucleotide contributes one phosphate. nmol_P = mass_ug / avg_nt_mw * 1000
    because ug / (g/mol) = umol * (ug/g=1e-6)/(mol) wait:
    mass_g = rna_mass_ug * 1e-6
    mol_nt = mass_g / avg_nt_mw
    nmol = mol_nt * 1e9 = rna_mass_ug * 1e-6 / avg_nt_mw * 1e9 = rna_mass_ug * 1e3 / avg_nt_mw
    """
    m = require_positive("rna_mass_ug", rna_mass_ug)
    mw = require_positive("avg_nt_mw_g_per_mol", avg_nt_mw_g_per_mol)
    return m * 1000.0 / mw


def ionizable_lipid_nmol_for_np(
    phosphate_nmol: float,
    target_np: float,
    *,
    ionizable_groups_per_molecule: float = 1.0,
) -> float:
    """Ionizable lipid amount (nmol of molecules) for target N/P.

    N/P = (n_lipid * groups_per_molecule) / n_phosphate
    so n_lipid = N/P * n_phosphate / groups_per_molecule
    """
    p = require_positive("phosphate_nmol", phosphate_nmol)
    np_ratio = require_positive("target_np", target_np)
    g = require_positive("ionizable_groups_per_molecule", ionizable_groups_per_molecule)
    return np_ratio * p / g


def np_from_amounts(
    ionizable_lipid_nmol: float,
    phosphate_nmol: float,
    *,
    ionizable_groups_per_molecule: float = 1.0,
) -> float:
    """Compute N/P from amounts (round-trip helper)."""
    n_lipid = require_positive("ionizable_lipid_nmol", ionizable_lipid_nmol)
    p = require_positive("phosphate_nmol", phosphate_nmol)
    g = require_positive("ionizable_groups_per_molecule", ionizable_groups_per_molecule)
    return (n_lipid * g) / p
