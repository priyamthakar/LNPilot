import json
from pathlib import Path

from lnpilot.cli import main


def test_cli_plan_batch(tmp_path: Path):
    out = tmp_path / "out"
    rc = main(["plan-batch", "examples/batch_example.json", "--out", str(out)])
    assert rc == 0
    assert (out / "batch-plan.json").exists()
    assert (out / "batch-plan.md").exists()
    data = json.loads((out / "batch-plan.json").read_text(encoding="utf-8"))
    assert data["target"]["target_np"] == 6


def test_cli_analyze_ribogreen(tmp_path: Path):
    out = tmp_path / "assay"
    rc = main(
        [
            "analyze-ribogreen",
            "examples/plate_reader_example.csv",
            "--map",
            "examples/plate_map_example.csv",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert (out / "assay-run.json").exists()
    assert (out / "samples.csv").exists()


def test_cli_render_report(tmp_path: Path):
    plan_out = tmp_path / "p"
    main(["plan-batch", "examples/batch_example.json", "--out", str(plan_out)])
    md = tmp_path / "report.md"
    rc = main(["render-report", str(plan_out / "batch-plan.json"), "--out", str(md)])
    assert rc == 0
    text = md.read_text(encoding="utf-8")
    assert "LNPilot Batch Plan" in text
