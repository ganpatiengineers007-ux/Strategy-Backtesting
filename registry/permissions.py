"""Role-based permissions. viewer < analyst < admin."""
_VIEWER = {"list", "view", "view_report"}
_ANALYST = _VIEWER | {"run_backtest", "run_validation", "compare"}
ROLES = {"viewer": _VIEWER, "analyst": _ANALYST, "admin": _ANALYST | {"register", "approve", "reject", "retire"}}


def can(role, action):
    return action in ROLES.get(role, set())


def require(role, action):
    if not can(role, action):
        raise PermissionError(f"role '{role}' ko '{action}' ki ijazat nahi")
