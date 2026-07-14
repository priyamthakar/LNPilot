import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from lnpilot.web import presets  # noqa: E402
from lnpilot.web.app import app  # noqa: E402

client = TestClient(app)


def test_home_page():
    r = client.get("/")
    assert r.status_code == 200
    assert "Plan a batch" in r.text


def test_plan_new_page():
    r = client.get("/plan/new")
    assert r.status_code == 200
    assert "Generate plan" in r.text


def _standard_form() -> dict:
    form = {k: v for k, v in presets.DEFAULTS.items() if k not in ("preset", "lipids")}
    for i, lip in enumerate(presets.STANDARD_LIPIDS):
        form[f"lipid_name_{i}"] = lip["name"]
        form[f"lipid_mol_percent_{i}"] = lip["mol_percent"]
        form[f"lipid_mw_{i}"] = lip["mw"]
        form[f"lipid_stock_{i}"] = lip["stock"]
        form[f"lipid_groups_{i}"] = lip["ionizable_groups"]
    return form


def test_plan_generate_and_results_and_exports():
    r = client.post("/plan/generate", data=_standard_form(), follow_redirects=False)
    assert r.status_code == 303
    location = r.headers["location"]

    r = client.get(location)
    assert r.status_code == 200
    assert "Achieved N/P" in r.text

    run_id = location.split("/")[2]

    r = client.get(f"/plan/{run_id}/export.json")
    assert r.status_code == 200
    assert r.json()["batch_id"] == "batch-001"

    r = client.get(f"/plan/{run_id}/export.csv")
    assert r.status_code == 200
    assert "name" in r.text.splitlines()[0]

    r = client.get(f"/plan/{run_id}/export.md")
    assert r.status_code == 200
    assert "LNPilot Batch Plan" in r.text


def test_plan_generate_invalid_frr_shows_inline_error():
    form = _standard_form()
    form["frr_aqueous_parts"] = 0
    r = client.post("/plan/generate", data=form)
    assert r.status_code == 422
    assert "Could not generate plan" in r.text


def test_plan_demo_runs_real_example():
    r = client.get("/plan/demo", follow_redirects=False)
    assert r.status_code == 303
    r = client.get(r.headers["location"])
    assert r.status_code == 200
    assert "Achieved N/P" in r.text


def test_missing_run_returns_404():
    r = client.get("/plan/does-not-exist/results")
    assert r.status_code == 404
