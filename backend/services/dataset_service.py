"""Datasets DATA_DIR ke andar hi (client path nahi deta, sirf file ka naam)."""
import os
import re
from pathlib import Path

from data.loaders import load_dataset
from data.provenance import data_label, is_synthetic_path

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.csv$")


def data_dir():
    return Path(os.environ.get("DATA_DIR", "data/samples"))


def resolve(name):
    if not isinstance(name, str) or not _NAME.match(name):
        raise ValueError("invalid dataset name (sirf *.csv file ka naam)")
    p = data_dir() / name
    if not p.exists():
        raise KeyError(name)
    return str(p)


def list_datasets():
    d = data_dir()
    out = []
    for f in sorted(d.glob("*.csv")) if d.exists() else []:
        ds = load_dataset(f)
        synthetic = is_synthetic_path(f)
        out.append({"file": f.name, **ds.meta(), "bars": len(ds.bars),
                    "synthetic": synthetic, "data_label": data_label(f)})
    return out
