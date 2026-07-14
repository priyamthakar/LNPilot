import json

from lnpilot import analyze_ribogreen_plate, plan_batch


def test_batch_json_roundtrip_fields():
    plan = plan_batch(
        rna_mass="50 ug",
        target_np=4,
        lipid_composition={
            "ionizable": {"mol_percent": 50, "mw": "700 g/mol", "stock": "10 mg/mL"},
            "helper": {"mol_percent": 50, "mw": "800 g/mol", "stock": "10 mg/mL"},
        },
        frr="2:1 aqueous:organic",
        total_flow_rate="8 mL/min",
    )
    s = json.dumps(plan.to_dict())
    back = json.loads(s)
    assert back["target"]["target_np"] == 4
    assert back["schema_version"] == "1.0.0"
    assert back["record_type"] == "batch_plan"


def test_assay_json():
    assay = analyze_ribogreen_plate(
        data="examples/plate_reader_example.csv",
        plate_map="examples/plate_map_example.csv",
    )
    data = assay.to_dict()
    json.dumps(data)
    assert data["schema_version"] == "1.0.0"
    assert data["record_type"] == "assay_run"
