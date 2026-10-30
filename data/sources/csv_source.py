"""CSV reader -> list of dict rows."""
import csv


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
