"""Default form values for the Plan-input screen."""

from __future__ import annotations

from lnpilot.formulate.np_ratio import DEFAULT_AVG_NT_MW

# Matches examples/batch_example.json's lipid_composition (Standard 4-component preset).
STANDARD_LIPIDS = [
    {"name": "Ionizable lipid", "role": "ionizable", "mol_percent": 50.0,
     "mw": 710.0, "stock": 10.0, "ionizable_groups": 1.0},
    {"name": "Helper lipid", "role": "helper", "mol_percent": 10.0,
     "mw": 790.0, "stock": 10.0, "ionizable_groups": 0.0},
    {"name": "Cholesterol", "role": "cholesterol", "mol_percent": 38.5,
     "mw": 386.65, "stock": 10.0, "ionizable_groups": 0.0},
    {"name": "PEG-lipid", "role": "peg_lipid", "mol_percent": 1.5,
     "mw": 2500.0, "stock": 5.0, "ionizable_groups": 0.0},
]

DEFAULTS = {
    "preset": "standard",
    "rna_mass_value": 100.0,
    "rna_mass_unit": "ug",
    "target_np": 6.0,
    "expected_recovery_percent": 85.0,
    "overage_percent": 0.0,
    "frr_aqueous_parts": 3.0,
    "frr_organic_parts": 1.0,
    "frr_convention": "aqueous:organic",
    "total_flow_rate": 12.0,
    "fill_volume": "",
    "n_vials": "",
    "post_mix_dilution_factor": 1.0,
    "avg_nt_mw": DEFAULT_AVG_NT_MW,
    "lipids": STANDARD_LIPIDS,
}

# examples/batch_example.json, expressed as form fields — for the "Load example" link.
EXAMPLE_OVERRIDES = {
    "expected_recovery_percent": 80.0,
    "overage_percent": 10.0,
}
