"""Single interface. Native extension (`svl_native`) ho to wahi, warna Python reference.
Rule: C++ ko main calculation se tabhi jodo jab benchmark meaningful gain dikhaye."""
from engines.reference.rolling_stats import rolling_mean as _ref

try:
    import svl_native as _native  # optional compiled module
    rolling_mean = _native.rolling_mean
    BACKEND = "native"
except ImportError:
    rolling_mean = _ref
    BACKEND = "python-reference"
