"""Import/wiring test for backend/services/report_service.py"""
import importlib


def test_module_imports():
    importlib.import_module("backend.services.report_service")


import json

from backend.services import report_service


def test_list_and_report_add_provenance(tmp_path):
    run = tmp_path / "run-sample"
    run.mkdir()
    (run / "run.json").write_text(json.dumps({"run_id": "run-sample", "strategy_id": "x", "status": "COMPLETED",
                                              "dataset_id": "sample_5m"}), encoding="utf-8")
    (run / "report.json").write_text(json.dumps({"run_id": "run-sample", "status": "COMPLETED", "metrics": {},
                                                 "validation": {"status": "PASS"}}), encoding="utf-8")
    rows = report_service.list_runs(str(tmp_path))
    assert rows[0]["synthetic"] is True and rows[0]["data_label"] == "synthetic"
    assert report_service.get_report("run-sample", str(tmp_path))["synthetic"] is True
