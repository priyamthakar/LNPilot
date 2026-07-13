import pytest

from lnpilot import analyze_ribogreen_plate


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
