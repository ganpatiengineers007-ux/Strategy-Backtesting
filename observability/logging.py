import json
import logging as _logging


class _Json(_logging.Formatter):
    def format(self, record):
        return json.dumps({"level": record.levelname, "name": record.name, "msg": record.getMessage()})


def setup_logging(level="INFO", as_json=True):
    h = _logging.StreamHandler()
    h.setFormatter(_Json() if as_json else _logging.Formatter("%(levelname)s %(name)s %(message)s"))
    root = _logging.getLogger()
    root.handlers[:] = [h]
    root.setLevel(level)
    return root
