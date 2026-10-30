import json
import logging

from observability.logging import setup_logging


def test_json_log_format(capsys):
    setup_logging("INFO")
    logging.getLogger("t").info("hello")
    line = capsys.readouterr().err.strip().splitlines()[-1]
    assert json.loads(line)["msg"] == "hello"
