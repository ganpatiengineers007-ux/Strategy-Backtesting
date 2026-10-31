from backend.schemas.report import ReportSummary


def test_summary():
    r = ReportSummary.from_report({"run_id": "r", "status": "COMPLETED", "validation": {"status": "FAIL"},
                                   "metrics": {"n_trades": 4, "total_return_pct": -1.5}})
    assert r.validation_status == "FAIL" and r.n_trades == 4 and r.total_return_pct == -1.5
