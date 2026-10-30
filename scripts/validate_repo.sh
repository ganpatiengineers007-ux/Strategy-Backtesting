#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "== python compile"
python -m compileall -q backend backtest cli contracts data engines metrics optimization persistence registry reporting risk strategies validation
echo "== python tests"
python -m pytest -q
if command -v go >/dev/null; then echo "== go"; (cd engines/go && go vet ./... && go test ./...); else echo "skip go (not installed)"; fi
if command -v cargo >/dev/null; then echo "== rust"; (cd engines/rust && cargo test -q); else echo "skip rust (not installed)"; fi
if command -v cmake >/dev/null; then echo "== c++"; (cd engines/cpp && cmake -S . -B build >/dev/null && cmake --build build >/dev/null && ctest --test-dir build --output-on-failure);
elif command -v g++ >/dev/null; then echo "== c++ (g++)"; g++ -std=c++17 -Iengines/cpp/include engines/cpp/src/rolling_stats.cpp engines/cpp/tests/test_rolling_stats.cpp -o /tmp/svl_cpp_test && /tmp/svl_cpp_test;
else echo "skip c++ (not installed)"; fi
if command -v npm >/dev/null && [ -d frontend/node_modules ]; then echo "== frontend"; (cd frontend && npx tsc --noEmit); else echo "skip frontend (npm install nahi hua)"; fi
echo "ALL CHECKS OK"
