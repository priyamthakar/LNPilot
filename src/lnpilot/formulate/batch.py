"""Flagship workflow: plan_batch()."""

from __future__ import annotations

from typing import Any

from lnpilot.core.exceptions import ValidationError
from lnpilot.core.models import BatchPlan
from lnpilot.core.provenance import Provenance
from lnpilot.core.units import to_canonical
from lnpilot.core.validation import require_positive
from lnpilot.formulate.composition import (
    component_amounts,
    normalize_composition,
    total_lipid_nmol_from_ionizable,
)
from lnpilot.formulate.mass_balance import check_lipid_mass_balance, scale_for_process
from lnpilot.formulate.mixing import (
    flow_rates_mL_per_min,
    junction_ethanol_fraction,
    parse_frr,
    phase_volumes_for_batch,
)
from lnpilot.formulate.np_ratio import (
    DEFAULT_AVG_NT_MW,
    ionizable_lipid_nmol_for_np,
    np_from_amounts,
    rna_phosphate_nmol,
)
from lnpilot.formulate.stocks import assign_stock_volumes


def _parse_lipid_composition(lipid_composition: dict | list) -> list[dict[str, Any]]:
    """Accept dict-of-roles (API sketch) or list-of-components."""
    if isinstance(lipid_composition, list):
        return list(lipid_composition)
    if not isinstance(lipid_composition, dict):
        raise ValidationError("lipid_composition must be a dict or list")

    out: list[dict[str, Any]] = []
    for key, spec in lipid_composition.items():
        if not isinstance(spec, dict):
            raise ValidationError(f"lipid_composition[{key!r}] must be a dict")
        name = str(spec.get("name", key))
        role = str(spec.get("role", key if key in {
            "ionizable", "helper", "cholesterol", "peg_lipid",
        } else "other"))
        mw = spec.get("mw")
        if mw is None:
            raise ValidationError(f"lipid {name!r} needs mw")
        mw_val = to_canonical(mw, "molar_mass", default_unit="g/mol")
        stock = spec.get("stock")
        stock_val = None
        if stock is not None:
            stock_val = to_canonical(stock, "concentration_mass", default_unit="mg/mL")
        mol = spec.get("mol_percent")
        if mol is None:
            raise ValidationError(f"lipid {name!r} needs mol_percent")
        groups = spec.get("ionizable_groups", 1.0 if role == "ionizable" else 0.0)
        out.append(
            {
                "name": name,
                "role": role,
                "mol_percent": float(mol),
                "mw": mw_val,
                "stock_mg_per_mL": stock_val,
                "ionizable_groups": float(groups),
            }
        )
    return out


def plan_batch(
    *,
    rna_mass: Any = None,
    final_rna_concentration: Any = None,
    final_volume: Any = None,
    target_np: float,
    lipid_composition: dict | list,
    frr: str,
    total_flow_rate: Any,
    expected_recovery: float = 1.0,
    overage_fraction: float = 0.0,
    avg_nt_mw: float = DEFAULT_AVG_NT_MW,
    ionizable_name: str | None = None,
    batch_id: str = "batch-001",
    fill_volume: Any = None,
    n_vials: int | None = None,
    post_mix_dilution_factor: float = 1.0,
    organic_is_ethanol: bool = True,
    path_volume: Any = None,
    aqueous_rna_concentration: Any = None,
    operator: str | None = None,
    instrument_metadata: dict[str, Any] | None = None,
) -> BatchPlan:
    """Plan an mRNA–LNP batch: N/P, lipids, stocks, mixing, mass balance.

    Provide either ``rna_mass`` or both ``final_rna_concentration`` and
    ``final_volume`` (target product basis before process scale-up).
    """
    warnings: list[str] = []
    assumptions: list[str] = [
        "RNA phosphate from mass-based average nucleotide MW (approximate).",
        "N/P uses user-supplied effective ionizable groups per molecule.",
        "Junction ethanol fraction is at the mixer, not after dilution/TFF.",
        "Organic phase treated as ethanolic lipid stream for EtOH fraction."
        if organic_is_ethanol
        else "Organic phase not assumed pure ethanol.",
    ]
    trace: list[str] = []

    # --- target RNA mass ---
    if rna_mass is not None:
        target_rna_ug = to_canonical(rna_mass, "mass", default_unit="ug")
    elif final_rna_concentration is not None and final_volume is not None:
        conc = to_canonical(
            final_rna_concentration, "concentration_mass_ug", default_unit="ug/mL"
        )
        vol = to_canonical(final_volume, "volume", default_unit="mL")
        target_rna_ug = conc * vol  # ug/mL * mL = ug
        trace.append(
            f"target_rna_mass_ug = conc_ug_per_mL ({conc}) * volume_mL ({vol}) = {target_rna_ug}"
        )
    else:
        raise ValidationError(
            "Provide rna_mass or both final_rna_concentration and final_volume"
        )
    require_positive("rna_mass", target_rna_ug)

    scale = scale_for_process(
        target_rna_ug,
        expected_recovery=expected_recovery,
        overage_fraction=overage_fraction,
    )
    planned_rna_ug = scale["planned_rna_mass_ug"]
    trace.append(
        f"planned_rna_ug = target ({target_rna_ug}) / recovery ({expected_recovery}) "
        f"* (1 + overage {overage_fraction}) = {planned_rna_ug}"
    )

    # --- phosphate & N/P ---
    p_nmol = rna_phosphate_nmol(planned_rna_ug, avg_nt_mw_g_per_mol=avg_nt_mw)
    trace.append(
        f"phosphate_nmol = rna_ug * 1000 / avg_nt_mw = {planned_rna_ug} * 1000 / {avg_nt_mw} = {p_nmol}"
    )
    assumptions.append(
        f"avg_nt_mw = {avg_nt_mw} g/mol (mass-based phosphate approximation)."
    )

    comps_in = _parse_lipid_composition(lipid_composition)
    comps = normalize_composition(comps_in, ionizable_name=ionizable_name)
    if ionizable_name:
        ion = next(c for c in comps if c["name"] == ionizable_name)
    else:
        ion = next(c for c in comps if c["role"] == "ionizable")

    ion_nmol = ionizable_lipid_nmol_for_np(
        p_nmol,
        float(target_np),
        ionizable_groups_per_molecule=float(ion["ionizable_groups"]),
    )
    trace.append(
        f"ionizable_nmol = N/P * P / groups = {target_np} * {p_nmol} / "
        f"{ion['ionizable_groups']} = {ion_nmol}"
    )

    total_lipid = total_lipid_nmol_from_ionizable(ion_nmol, ion["mol_fraction"])
    trace.append(
        f"total_lipid_nmol = ionizable_nmol / mol_fraction = {ion_nmol} / "
        f"{ion['mol_fraction']} = {total_lipid}"
    )

    amounts = component_amounts(comps, total_lipid)
    stocks = assign_stock_volumes(amounts)
    if any(s.get("stock_volume_mL") is None for s in stocks):
        warnings.append("One or more lipids lack stock concentration; stock volumes incomplete.")

    mb = check_lipid_mass_balance(amounts, total_lipid)
    if not mb["balanced"]:
        warnings.append("Lipid nmol sum does not match total within tolerance.")

    check_np = np_from_amounts(
        ion_nmol, p_nmol, ionizable_groups_per_molecule=float(ion["ionizable_groups"])
    )
    trace.append(f"N/P check (round-trip) = {check_np}")

    # --- mixing ---
    frr_info = parse_frr(frr)
    tfr = to_canonical(total_flow_rate, "flow", default_unit="mL/min")
    flows = flow_rates_mL_per_min(tfr, frr_info["aqueous_to_organic"])
    etoh = junction_ethanol_fraction(frr_info["aqueous_to_organic"])
    if not organic_is_ethanol:
        warnings.append("Junction organic fraction reported; organic not assumed ethanol.")
    trace.append(
        f"Q_aq = {flows['aqueous_flow_mL_per_min']} mL/min, "
        f"Q_org = {flows['organic_flow_mL_per_min']} mL/min, "
        f"junction_organic_fraction = {etoh}"
    )

    # Organic volume from lipid stocks if available
    org_stock_vols = [s["stock_volume_mL"] for s in stocks if s.get("stock_volume_mL") is not None]
    organic_vol = sum(org_stock_vols) if org_stock_vols else None
    phases: dict[str, float | None] = {}
    if organic_vol is not None and organic_vol > 0:
        phases.update(
            phase_volumes_for_batch(
                organic_vol * (frr_info["aqueous_to_organic"] + 1.0),
                frr_info["aqueous_to_organic"],
            )
        )
        # reconcile: organic should match stock sum
        phases["organic_volume_mL"] = organic_vol
        phases["aqueous_volume_mL"] = organic_vol * frr_info["aqueous_to_organic"]
        phases["total_mixed_volume_mL"] = organic_vol * (
            frr_info["aqueous_to_organic"] + 1.0
        )
    else:
        phases.update(
            {
                "total_mixed_volume_mL": None,
                "aqueous_volume_mL": None,
                "organic_volume_mL": None,
            }
        )
        warnings.append("Organic phase volume unknown without complete stock volumes.")

    # Aqueous RNA concentration at mix
    aq_vol = phases.get("aqueous_volume_mL")
    if aqueous_rna_concentration is not None:
        aq_rna_conc = to_canonical(
            aqueous_rna_concentration, "concentration_mass_ug", default_unit="ug/mL"
        )
    elif aq_vol and aq_vol > 0:
        aq_rna_conc = planned_rna_ug / aq_vol
    else:
        aq_rna_conc = None

    dil = require_positive("post_mix_dilution_factor", post_mix_dilution_factor)
    if dil < 1.0:
        raise ValidationError("post_mix_dilution_factor must be >= 1")

    theo_rna_conc = None
    theo_lipid_conc_mg_mL = None
    mixed_v = phases.get("total_mixed_volume_mL")
    if mixed_v and mixed_v > 0:
        theo_rna_conc = planned_rna_ug / mixed_v  # ug/mL at mix before dilution
        theo_lipid_conc_mg_mL = (mb["total_lipid_mass_ug"] / 1000.0) / mixed_v
        if dil > 1.0:
            theo_rna_conc = theo_rna_conc / dil
            theo_lipid_conc_mg_mL = theo_lipid_conc_mg_mL / dil

    fill_mL = None
    if fill_volume is not None:
        fill_mL = to_canonical(fill_volume, "volume", default_unit="mL")
        require_positive("fill_volume", fill_mL)
    n_v = n_vials
    if n_v is not None:
        if isinstance(n_v, bool) or not isinstance(n_v, int):
            raise ValidationError("n_vials must be a positive integer")
        require_positive("n_vials", float(n_v))

    path_v = None
    mix_t = None
    if path_volume is not None:
        path_v = to_canonical(path_volume, "volume", default_unit="mL")
        mix_t = path_v / tfr

    if abs(check_np - float(target_np)) > 1e-6 * max(float(target_np), 1.0):
        warnings.append("N/P round-trip residual exceeds tolerance.")

    prov = Provenance.create(
        workflow_name="plan_batch",
        assumptions=assumptions,
        warnings=warnings,
        operator=operator,
        method_id="formulate.plan_batch.v0.1.1",
        instrument_metadata=dict(instrument_metadata or {}),
    )

    return BatchPlan(
        batch_id=batch_id,
        target={
            "target_np": float(target_np),
            "target_rna_mass_ug": target_rna_ug,
            "planned_rna_mass_ug": planned_rna_ug,
            "expected_recovery": scale["expected_recovery"],
            "overage_fraction": float(overage_fraction),
            "process_scale_factor": scale["process_scale_factor"],
            "fill_volume_mL": fill_mL,
            "n_vials": n_v,
            "post_mix_dilution_factor": dil,
        },
        rna={
            "planned_mass_ug": planned_rna_ug,
            "phosphate_nmol": p_nmol,
            "avg_nt_mw_g_per_mol": avg_nt_mw,
            "aqueous_concentration_ug_per_mL": aq_rna_conc,
            "mode": "mass_based_average_nt_mw",
        },
        lipids=amounts,
        stocks=stocks,
        aqueous={
            "volume_mL": phases.get("aqueous_volume_mL"),
            "rna_mass_ug": planned_rna_ug,
            "rna_concentration_ug_per_mL": aq_rna_conc,
        },
        organic={
            "volume_mL": phases.get("organic_volume_mL"),
            "is_ethanol_stream": organic_is_ethanol,
        },
        mixing={
            **frr_info,
            **flows,
            "junction_organic_volume_fraction": etoh,
            "path_volume_mL": path_v,
            "mixing_time_min": mix_t,
        },
        downstream={
            "post_mix_dilution_factor": dil,
            "note": "Buffer exchange / TFF not modeled in detail in v0.1",
        },
        theoretical={
            "mixed_volume_mL": mixed_v,
            "rna_concentration_ug_per_mL_after_dilution": theo_rna_conc,
            "total_lipid_concentration_mg_per_mL_after_dilution": theo_lipid_conc_mg_mL,
            "achieved_np": check_np,
        },
        mass_balance=mb,
        calculation_trace=trace,
        warnings=warnings,
        assumptions=assumptions,
        provenance=prov,
    )
