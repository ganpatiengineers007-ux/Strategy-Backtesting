"""Quality status: ERROR => BLOCKED, warning => WARN, else PASS."""


def build_report(issues):
    errors = [i for i in issues if i["level"] == "ERROR"]
    warns = [i for i in issues if i["level"] == "WARN"]
    status = "BLOCKED" if errors else ("WARN" if warns else "PASS")
    codes = {}
    for i in issues:
        codes[i["code"]] = codes.get(i["code"], 0) + 1
    return {"status": status, "errors": len(errors), "warnings": len(warns), "codes": codes, "sample": issues[:20]}
