from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATHS = ["/health", "/strategies", "/backtests", "/validations/{id}", "/comparisons", "/reports/{id}", "/audit"]


def test_openapi_lists_all_routes_and_client_uses_them():
    spec = (ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8")
    assert all(p in spec for p in PATHS)
    client = "".join(f.read_text(encoding="utf-8") for f in (ROOT / "frontend/src/api").glob("*.ts"))
    for p in ("/health", "/strategies", "/backtests", "/reports/"):
        assert p in client
