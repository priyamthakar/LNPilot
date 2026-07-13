"""Markdown report generator (reproducible, not regulatory)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def render_batch_plan_md(plan: dict[str, Any]) -> str:
    p = plan
    prov = p.get("provenance") or {}
    lines = [
        f"# LNPilot Batch Plan — {p.get('batch_id', '')}",
        "",
        "> Reproducible calculation report. **Not** a regulatory document.",
        "",
        "## Provenance",
        "",
        f"- Software: {prov.get('software_name')} {prov.get('software_version')}",
        f"- Workflow: {prov.get('workflow_name')} {prov.get('workflow_version')}",
        f"- Generated: {prov.get('generated_at')}",
        f"- Method: {prov.get('method_id')}",
        "",
        "## Target",
        "",
    ]
    for k, v in (p.get("target") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## RNA", ""]
    for k, v in (p.get("rna") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Lipids", "", "| Name | Role | mol% (norm) | nmol | mass (µg) | stock (mL) |",
              "|---|---|---:|---:|---:|---:|"]
    stocks = {s["name"]: s for s in (p.get("stocks") or [])}
    for lip in p.get("lipids") or []:
        st = stocks.get(lip["name"], {})
        lines.append(
            f"| {lip.get('name')} | {lip.get('role')} | "
            f"{lip.get('normalized_mol_percent', 0):.3f} | "
            f"{lip.get('amount_nmol', 0):.4g} | "
            f"{lip.get('mass_ug', 0):.4g} | "
            f"{st.get('stock_volume_mL', '—')} |"
        )
    lines += ["", "## Mixing", ""]
    for k, v in (p.get("mixing") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Theoretical outputs", ""]
    for k, v in (p.get("theoretical") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Mass balance", ""]
    for k, v in (p.get("mass_balance") or {}).items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Assumptions", ""]
    for a in p.get("assumptions") or []:
        lines.append(f"- {a}")
    lines += ["", "## Warnings", ""]
    warns = p.get("warnings") or []
    if not warns:
        lines.append("- (none)")
    else:
        for w in warns:
            lines.append(f"- {w}")
    lines += ["", "## Calculation trace", ""]
    for t in p.get("calculation_trace") or []:
        lines.append(f"- `{t}`")
    lines.append("")
    return "\n".join(lines)


def render_assay_md(assay: dict[str, Any]) -> str:
    a = assay
    prov = a.get("provenance") or {}
    lines = [
        f"# LNPilot Assay Report — {a.get('assay_id', '')}",
        "",
        "> Reproducible analysis report. **Not** a regulatory document.",
        "",
        "## Provenance",
        "",
        f"- Software: {prov.get('software_name')} {prov.get('software_version')}",
        f"- Workflow: {prov.get('workflow_name')}",
        f"- Generated: {prov.get('generated_at')}",
        "",
        "## Calibration",
        "",
    ]
    cal = a.get("calibration") or {}
    for k in ("model", "slope", "intercept", "r_squared", "n_points", "x_min", "x_max", "weighted"):
        if k in cal:
            lines.append(f"- **{k}**: {cal[k]}")
    lines += ["", "## Samples", "",
              "| Key | Free (µg/mL) | Total (µg/mL) | Encap (µg/mL) | EE% |",
              "|---|---:|---:|---:|---:|"]
    for s in a.get("sample_table") or []:
        ee = s.get("ee_percent")
        ee_s = f"{ee:.2f}" if ee is not None else "—"
        lines.append(
            f"| {s.get('sample_key')} | {s.get('free_rna_ug_per_mL')} | "
            f"{s.get('total_rna_ug_per_mL')} | {s.get('encapsulated_rna_ug_per_mL')} | {ee_s} |"
        )
    lines += ["", "## QC", ""]
    qc = a.get("qc") or {}
    lines.append(f"- **status**: {qc.get('status')}")
    for f in qc.get("flags") or []:
        lines.append(f"- {f}")
    lines += ["", "## Assumptions", ""]
    for x in a.get("assumptions") or []:
        lines.append(f"- {x}")
    lines += ["", "## Warnings", ""]
    warns = a.get("warnings") or []
    lines.append("- (none)" if not warns else "")
    for w in warns:
        lines.append(f"- {w}")
    lines.append("")
    return "\n".join(lines)


def write_markdown(text: str, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p
