"""FastAPI app — Pass 1: Home, Plan batch input/results.

Server-rendered (Jinja2), backed directly by lnpilot.formulate.plan_batch —
no separate JSON API layer.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lnpilot.core.exceptions import LNPilotError
from lnpilot.formulate.batch import plan_batch
from lnpilot.io.json_io import to_jsonable
from lnpilot.report.markdown import render_batch_plan_md
from lnpilot.web import presets

WEB_DIR = Path(__file__).parent
EXAMPLE_CONFIG_PATH = WEB_DIR.parent.parent.parent / "examples" / "batch_example.json"

app = FastAPI(title="LNPilot")
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# Bounded in-memory run store: run_id -> BatchPlan.to_dict(). No persistence in Pass 1.
_MAX_RUNS = 200
_runs: dict[str, dict[str, Any]] = {}


def _store_run(plan_dict: dict[str, Any]) -> str:
    run_id = uuid.uuid4().hex[:12]
    _runs[run_id] = plan_dict
    while len(_runs) > _MAX_RUNS:
        _runs.pop(next(iter(_runs)))
    return run_id


def _get_run(run_id: str) -> dict[str, Any] | None:
    return _runs.get(run_id)


def _lipid_rows_from_form(form: Any) -> list[dict[str, Any]]:
    """Build the lipid_composition list from the 4 fixed Standard-preset rows."""
    rows = []
    for i, base in enumerate(presets.STANDARD_LIPIDS):
        role = base["role"]
        name = str(form.get(f"lipid_name_{i}", base["name"])).strip() or base["name"]
        mol_percent = float(form.get(f"lipid_mol_percent_{i}", base["mol_percent"]))
        mw = float(form.get(f"lipid_mw_{i}", base["mw"]))
        stock_raw = form.get(f"lipid_stock_{i}", base["stock"])
        stock = float(stock_raw) if stock_raw not in (None, "") else None
        groups = float(form.get(f"lipid_groups_{i}", base["ionizable_groups"]))
        rows.append(
            {
                "name": name,
                "role": role,
                "mol_percent": mol_percent,
                "mw": mw,
                "stock_mg_per_mL": stock,
                "ionizable_groups": groups,
            }
        )
    return rows


def _plan_kwargs_from_form(form: Any) -> dict[str, Any]:
    rna_value = float(form.get("rna_mass_value", presets.DEFAULTS["rna_mass_value"]))
    rna_unit = form.get("rna_mass_unit", presets.DEFAULTS["rna_mass_unit"])
    target_np = float(form.get("target_np", presets.DEFAULTS["target_np"]))
    recovery_percent = float(
        form.get("expected_recovery_percent", presets.DEFAULTS["expected_recovery_percent"])
    )
    overage_percent = float(
        form.get("overage_percent", presets.DEFAULTS["overage_percent"])
    )
    aq_parts = float(form.get("frr_aqueous_parts", presets.DEFAULTS["frr_aqueous_parts"]))
    org_parts = float(form.get("frr_organic_parts", presets.DEFAULTS["frr_organic_parts"]))
    convention = form.get("frr_convention", presets.DEFAULTS["frr_convention"])
    total_flow_rate = float(form.get("total_flow_rate", presets.DEFAULTS["total_flow_rate"]))
    avg_nt_mw = float(form.get("avg_nt_mw", presets.DEFAULTS["avg_nt_mw"]))
    dilution = float(
        form.get("post_mix_dilution_factor", presets.DEFAULTS["post_mix_dilution_factor"])
    )

    fill_volume_raw = form.get("fill_volume", "")
    fill_volume = f"{float(fill_volume_raw)} mL" if str(fill_volume_raw).strip() else None

    n_vials_raw = form.get("n_vials", "")
    n_vials = int(float(n_vials_raw)) if str(n_vials_raw).strip() else None

    return {
        "batch_id": form.get("batch_id") or "batch-001",
        "rna_mass": f"{rna_value} {rna_unit}",
        "target_np": target_np,
        "lipid_composition": _lipid_rows_from_form(form),
        "frr": f"{aq_parts}:{org_parts} {convention}",
        "total_flow_rate": f"{total_flow_rate} mL/min",
        "expected_recovery": recovery_percent / 100.0,
        "overage_fraction": overage_percent / 100.0,
        "avg_nt_mw": avg_nt_mw,
        "fill_volume": fill_volume,
        "n_vials": n_vials,
        "post_mix_dilution_factor": dilution,
    }


def _form_context(form: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = dict(presets.DEFAULTS)
    if form:
        ctx.update(form)
    return ctx


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home.html", {})


@app.get("/plan/new", response_class=HTMLResponse)
def plan_new(request: Request, example: int = 0) -> HTMLResponse:
    form = dict(presets.DEFAULTS)
    if example:
        form.update(presets.EXAMPLE_OVERRIDES)
    return templates.TemplateResponse(
        request, "plan_input.html", {"form": form, "errors": {}, "error_message": None}
    )


@app.post("/plan/generate", response_class=HTMLResponse)
async def plan_generate(request: Request) -> Response:
    raw_form = dict((await request.form()))
    try:
        kwargs = _plan_kwargs_from_form(raw_form)
        plan = plan_batch(**kwargs)
    except LNPilotError as exc:
        return templates.TemplateResponse(
            request,
            "plan_input.html",
            {"form": _form_context(raw_form), "errors": {}, "error_message": str(exc)},
            status_code=422,
        )
    except (TypeError, ValueError) as exc:
        return templates.TemplateResponse(
            request,
            "plan_input.html",
            {
                "form": _form_context(raw_form),
                "errors": {},
                "error_message": f"Invalid input: {exc}",
            },
            status_code=422,
        )
    run_id = _store_run(plan.to_dict())
    return RedirectResponse(f"/plan/{run_id}/results", status_code=303)


@app.get("/plan/demo", response_class=HTMLResponse)
def plan_demo() -> Response:
    cfg = json.loads(EXAMPLE_CONFIG_PATH.read_text(encoding="utf-8"))
    plan = plan_batch(**cfg)
    run_id = _store_run(plan.to_dict())
    return RedirectResponse(f"/plan/{run_id}/results", status_code=303)


@app.get("/plan/{run_id}/results", response_class=HTMLResponse)
def plan_results(request: Request, run_id: str) -> HTMLResponse:
    plan = _get_run(run_id)
    if plan is None:
        return templates.TemplateResponse(
            request, "not_found.html", {"run_id": run_id}, status_code=404
        )
    return templates.TemplateResponse(
        request, "plan_results.html", {"plan": plan, "run_id": run_id}
    )


@app.get("/plan/{run_id}/export.json")
def export_json(run_id: str) -> Response:
    plan = _get_run(run_id)
    if plan is None:
        return Response("Run not found", status_code=404)
    body = json.dumps(to_jsonable(plan), indent=2)
    return Response(
        body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-batch-plan.json"'},
    )


@app.get("/plan/{run_id}/export.md")
def export_md(run_id: str) -> Response:
    plan = _get_run(run_id)
    if plan is None:
        return Response("Run not found", status_code=404)
    body = render_batch_plan_md(plan)
    return Response(
        body,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-batch-plan.md"'},
    )


@app.get("/plan/{run_id}/export.csv")
def export_csv(run_id: str) -> Response:
    plan = _get_run(run_id)
    if plan is None:
        return Response("Run not found", status_code=404)
    rows = plan.get("lipids") or plan.get("stocks") or []
    buf = io.StringIO()
    if rows:
        keys: list[str] = list(rows[0].keys())
        for r in rows[1:]:
            for k in r:
                if k not in keys:
                    keys.append(k)
        writer = csv.DictWriter(buf, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k) for k in keys})
    return Response(
        buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-lipids.csv"'},
    )
