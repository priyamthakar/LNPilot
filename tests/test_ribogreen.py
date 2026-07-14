import pytest

from lnpilot import analyze_ribogreen_plate
from lnpilot.core.exceptions import ValidationError


def test_example_plate():
    assay = analyze_ribogreen_plate(
        data="examples/plate_reader_example.csv",
        plate_map="examples/plate_map_example.csv",
    )
    d = assay.to_dict()
    assert d["calibration"]["r_squared"] > 0.99
    assert len(d["sample_table"]) == 1
    s = d["sample_table"][0]
    # blank=100; free ~310 corr → conc ~0.31 if slope~1000, intercept~0
    # standards: blank-corrected y = 0,250,500,1000,2000,4000 for x=0..4 → slope 1000
    assert s["ee_percent"] is not None
    assert 0 < s["ee_percent"] < 100
    # free < total
    assert s["free_rna_ug_per_mL"] < s["total_rna_ug_per_mL"]
    assert s["free_cv_percent"] is not None
    assert s["ee_confidence_interval_95"] is not None
    assert d["calibration"]["lloq"] == pytest.approx(0.25)
    assert len(d["calibration"]["standard_summary"]) == 6
    assert d["provenance"]["source_files"][0]["sha256"]


def test_synthetic_ee():
    """Signals crafted so free≈1, total≈4 ug/mL → EE≈75% with slope 1000, blank 100."""
    # y = 1000 x + 100 (raw), blank 100 → corr = 1000 x
    data = {
        "A1": 100.0,
        "B1": 100.0,   # std 0
        "B2": 1100.0,  # std 1
        "B3": 2100.0,  # std 2
        "B4": 4100.0,  # std 4
        "C1": 1100.0,  # free → 1 ug/mL
        "C2": 4100.0,  # total → 4 ug/mL
    }
    pmap = [
        {"well": "A1", "role": "blank"},
        {"well": "B1", "role": "standard", "concentration": "0"},
        {"well": "B2", "role": "standard", "concentration": "1"},
        {"well": "B3", "role": "standard", "concentration": "2"},
        {"well": "B4", "role": "standard", "concentration": "4"},
        {"well": "C1", "role": "free", "group_id": "S1", "dilution_factor": "1"},
        {"well": "C2", "role": "total", "group_id": "S1", "dilution_factor": "1"},
    ]
    assay = analyze_ribogreen_plate(data=data, plate_map=pmap)
    s = assay.sample_table[0]
    assert s["ee_percent"] == pytest.approx(75.0, rel=1e-3)


def test_recovery_is_calculated_per_sample():
    data = {
        "A1": 100.0,
        "B1": 100.0,
        "B2": 1100.0,
        "B3": 2100.0,
        "B4": 4100.0,
        "C1": 1100.0,
        "C2": 4100.0,
        "D1": 1100.0,
        "D2": 2100.0,
    }
    pmap = [
        {"well": "A1", "role": "blank"},
        {"well": "B1", "role": "standard", "concentration": 0},
        {"well": "B2", "role": "standard", "concentration": 1},
        {"well": "B3", "role": "standard", "concentration": 2},
        {"well": "B4", "role": "standard", "concentration": 4},
        {"well": "C1", "role": "free", "group_id": "S1"},
        {"well": "C2", "role": "total", "group_id": "S1"},
        {"well": "D1", "role": "free", "group_id": "S2"},
        {"well": "D2", "role": "total", "group_id": "S2"},
    ]
    assay = analyze_ribogreen_plate(
        data=data,
        plate_map=pmap,
        input_rna_mass={"S1": "4 ug", "S2": "2 ug"},
        sample_volume={"S1": "1 mL", "S2": "1 mL"},
    )
    assert [s["recovery_fraction"] for s in assay.sample_table] == pytest.approx([1.0, 1.0])

    with pytest.raises(ValidationError, match="mapping keyed by sample"):
        analyze_ribogreen_plate(
            data=data,
            plate_map=pmap,
            input_rna_mass="4 ug",
            sample_volume="1 mL",
        )


def test_recovery_requires_mass_and_volume_together():
    with pytest.raises(ValidationError, match="provided together"):
        analyze_ribogreen_plate(
            data="examples/plate_reader_example.csv",
            plate_map="examples/plate_map_example.csv",
            input_rna_mass="2 ug",
        )
