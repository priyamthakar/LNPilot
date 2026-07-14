"""LNPilot command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_batch_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise SystemExit(
                "YAML configs require: pip install lnpilot[yaml] (or pass JSON)"
            ) from exc
        return yaml.safe_load(text)
    return json.loads(text)


def cmd_plan_batch(args: argparse.Namespace) -> int:
    from lnpilot.core.provenance import source_file_record
    from lnpilot.formulate.batch import plan_batch
    from lnpilot.io.csv_io import write_rows
    from lnpilot.io.json_io import write_json
    from lnpilot.report.markdown import render_batch_plan_md, write_markdown

    cfg = _load_batch_config(Path(args.config))
    plan = plan_batch(**cfg)
    plan.provenance.source_files.append(source_file_record("batch_config", args.config))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    d = plan.to_dict()
    write_json(d, out / "batch-plan.json")
    write_markdown(render_batch_plan_md(d), out / "batch-plan.md")
    write_rows(out / "lipids.csv", d.get("stocks") or d.get("lipids") or [])
    print(f"Wrote batch plan to {out}")
    return 0


def cmd_analyze_ribogreen(args: argparse.Namespace) -> int:
    from lnpilot.characterize.ribogreen import analyze_ribogreen_plate
    from lnpilot.io.csv_io import write_rows
    from lnpilot.io.json_io import write_json
    from lnpilot.report.markdown import render_assay_md, write_markdown

    kwargs: dict[str, Any] = {
        "data": args.data,
        "plate_map": args.map,
        "calibration": args.calibration,
        "weighting": args.weighting,
        "max_replicate_cv_percent": args.max_replicate_cv,
        "max_standard_bias_percent": args.max_standard_bias,
    }
    if args.input_rna_mass:
        kwargs["input_rna_mass"] = args.input_rna_mass
    if args.sample_volume:
        kwargs["sample_volume"] = args.sample_volume

    assay = analyze_ribogreen_plate(**kwargs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    d = assay.to_dict()
    write_json(d, out / "assay-run.json")
    write_markdown(render_assay_md(d), out / "assay-run.md")
    write_rows(out / "samples.csv", d.get("sample_table") or [])
    if args.plot:
        from lnpilot.report.plots import plot_calibration

        plot_calibration(d["calibration"], out / "calibration.png")
    print(f"Wrote assay results to {out}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "The web UI requires: pip install lnpilot[web]"
        ) from exc

    from lnpilot.web.app import app

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def cmd_render_report(args: argparse.Namespace) -> int:
    from lnpilot.io.json_io import read_json
    from lnpilot.report.markdown import (
        render_assay_md,
        render_batch_plan_md,
        write_markdown,
    )

    data = read_json(args.record)
    out = Path(args.out) if args.out else Path(args.record).with_suffix(".md")
    if "lipids" in data and "mixing" in data:
        text = render_batch_plan_md(data)
    elif "sample_table" in data or data.get("assay_type") == "ribogreen":
        text = render_assay_md(data)
    else:
        raise SystemExit("Unrecognized record type")
    write_markdown(text, out)
    print(f"Wrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lnpilot",
        description="LNPilot — mRNA–LNP batch planning and RiboGreen analysis",
    )
    p.add_argument("--version", action="version", version="lnpilot 0.1.1")
    sub = p.add_subparsers(dest="command", required=True)

    pb = sub.add_parser("plan-batch", help="Plan an LNP formulation batch")
    pb.add_argument("config", help="YAML or JSON batch config")
    pb.add_argument("--out", "-o", default="results", help="Output directory")
    pb.set_defaults(func=cmd_plan_batch)

    rg = sub.add_parser("analyze-ribogreen", help="Analyze a RiboGreen plate")
    rg.add_argument("data", help="Plate-reader CSV/XLSX")
    rg.add_argument("--map", required=True, help="Plate map CSV")
    rg.add_argument("--out", "-o", default="results", help="Output directory")
    rg.add_argument("--calibration", default="linear")
    rg.add_argument("--weighting", default=None, choices=["1/x", "1/x^2"])
    rg.add_argument("--input-rna-mass", default=None)
    rg.add_argument("--sample-volume", default=None)
    rg.add_argument("--max-replicate-cv", type=float, default=20.0)
    rg.add_argument("--max-standard-bias", type=float, default=20.0)
    rg.add_argument("--plot", action="store_true")
    rg.set_defaults(func=cmd_analyze_ribogreen)

    rr = sub.add_parser("render-report", help="Render Markdown from a JSON record")
    rr.add_argument("record", help="batch-plan.json or assay-run.json")
    rr.add_argument("--out", "-o", default=None)
    rr.add_argument("--format", default="markdown", choices=["markdown"])
    rr.set_defaults(func=cmd_render_report)

    sv = sub.add_parser("serve", help="Run the LNPilot web UI")
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--port", type=int, default=8000)
    sv.set_defaults(func=cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
