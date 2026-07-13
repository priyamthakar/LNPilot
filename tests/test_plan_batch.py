import json
from pathlib import Path

import pytest

from lnpilot import plan_batch
from lnpilot.core.exceptions import ValidationError

LIPIDS = {
    "ionizable": {"mol_percent": 50.0, "mw": "710 g/mol", "stock": "10 mg/mL"},
    "helper": {"mol_percent": 10.0, "mw": "790 g/mol", "stock": "10 mg/mL"},
    "cholesterol": {"mol_percent": 38.5, "mw": "386.65 g/mol", "stock": "10 mg/mL"},
    "peg_lipid": {"mol_percent": 1.5, "mw": "2500 g/mol", "stock": "5 mg/mL"},
}


def test_plan_batch_basic():
    plan = plan_batch(
        rna_mass="100 ug",
        target_np=6,
        lipid_composition=LIPIDS,
        frr="3:1 aqueous:organic",
        total_flow_rate="12 mL/min",
        expected_recovery=0.8,
    )
    d = plan.to_dict()
    assert d["theoretical"]["achieved_np"] == pytest.approx(6.0)
    assert d["mass_balance"]["balanced"] is True
    assert abs(
        d["mixing"]["aqueous_flow_mL_per_min"] + d["mixing"]["organic_flow_mL_per_min"] - 12.0
    ) < 1e-9
    # JSON serializable
    json.dumps(d)


def test_reference_phosphate_and_np():
    """Hand calc: 330 ug planned RNA, MW 330 → 1000 nmol P; N/P=6 → 6000 nmol ionizable."""
    plan = plan_batch(
        rna_mass="330 ug",
        target_np=6,
        lipid_composition={
            "ionizable": {"mol_percent": 50.0, "mw": "700 g/mol", "stock": "10 mg/mL"},
            "helper": {"mol_percent": 50.0, "mw": "800 g/mol", "stock": "10 mg/mL"},
        },
        frr="3:1 aqueous:organic",
        total_flow_rate="10 mL/min",
        expected_recovery=1.0,
        overage_fraction=0.0,
        avg_nt_mw=330.0,
    )
    assert plan.rna["phosphate_nmol"] == pytest.approx(1000.0)
    ion = next(x for x in plan.lipids if x["role"] == "ionizable")
    assert ion["amount_nmol"] == pytest.approx(6000.0)
    assert plan.mass_balance["total_lipid_nmol"] == pytest.approx(12000.0)


def test_negative_rna_rejected():
    with pytest.raises(ValidationError):
        plan_batch(
            rna_mass="-1 ug",
            target_np=6,
            lipid_composition=LIPIDS,
            frr="3:1 aqueous:organic",
            total_flow_rate="12 mL/min",
        )


def test_example_config():
    cfg = json.loads(Path("examples/batch_example.json").read_text(encoding="utf-8"))
    plan = plan_batch(**cfg)
    assert plan.batch_id == "demo-batch-001"


def test_reference_file():
    ref = json.loads(
        Path("tests/references/batch_ref_330ug.json").read_text(encoding="utf-8")
    )
    exp = ref["expected"]
    plan = plan_batch(
        rna_mass=f"{ref['inputs']['rna_mass_ug']} ug",
        target_np=ref["inputs"]["target_np"],
        lipid_composition={
            "ionizable": {"mol_percent": 50.0, "mw": "700 g/mol", "stock": "10 mg/mL"},
            "helper": {"mol_percent": 50.0, "mw": "800 g/mol", "stock": "10 mg/mL"},
        },
        frr="3:1 aqueous:organic",
        total_flow_rate="10 mL/min",
        expected_recovery=1.0,
        overage_fraction=0.0,
        avg_nt_mw=ref["inputs"]["avg_nt_mw"],
    )
    assert plan.rna["phosphate_nmol"] == pytest.approx(exp["phosphate_nmol"])
    ion = next(x for x in plan.lipids if x["role"] == "ionizable")
    assert ion["amount_nmol"] == pytest.approx(exp["ionizable_nmol"])
    assert plan.mass_balance["total_lipid_nmol"] == pytest.approx(exp["total_lipid_nmol"])
