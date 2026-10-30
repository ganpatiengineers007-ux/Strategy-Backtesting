"""Strategy lifecycle states."""
ALLOWED = {"DRAFT": {"VALIDATED", "RETIRED"}, "VALIDATED": {"APPROVED", "DRAFT", "RETIRED"},
           "APPROVED": {"RETIRED", "DRAFT"}, "RETIRED": set()}


def can_transition(a, b):
    return b in ALLOWED.get(a, set())
