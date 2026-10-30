"""Manifest + data requirement checks."""
REQUIRED_KEYS = ("id", "version", "entry_point", "required_data", "parameters", "execution_modes")


def validate_manifest(m):
    return [f"missing: {k}" for k in REQUIRED_KEYS if k not in m]


def check_data_requirements(required, dataset):
    missing = [f for f in required if f not in dataset.fields]
    return (not missing, missing)
