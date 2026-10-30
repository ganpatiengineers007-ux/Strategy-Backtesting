"""Go validator service client (HTTP/JSON, contracts/openapi.yaml ke mutabik). URL na ho to saaf error."""
import json
import urllib.request


class GoValidatorClient:
    def __init__(self, base_url=None, timeout=10):
        self.base_url, self.timeout = base_url, timeout

    def validate(self, payload):
        if not self.base_url:
            raise RuntimeError("Go validator URL configure nahi hai")
        req = urllib.request.Request(self.base_url.rstrip("/") + "/validate", json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())
