"""Strategy lifecycle states (blueprint: Draft, Validated, Rejected + Approved, Retired)."""
ALLOWED = {"DRAFT": {"VALIDATED", "REJECTED", "RETIRED"},
           "VALIDATED": {"APPROVED", "DRAFT", "REJECTED", "RETIRED"},
           "APPROVED": {"RETIRED", "DRAFT"},
           "REJECTED": {"DRAFT"},
           "RETIRED": set()}


def can_transition(a, b):
    return b in ALLOWED.get(a, set())
