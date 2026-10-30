"""Timestamp parsing (ISO-8601)."""
from datetime import datetime


def parse_ts(s):
    return datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
