# Security

Vulnerability public issue me mat daalo; repo owner ko private roop se batao.
Secrets (`.env`, tokens, broker keys) kabhi commit nahi.

- API key is required for all routes except `/health`; production refuses to start without a 32+ char key.
- The browser keeps the key only in `sessionStorage`; it is never bundled. Use HTTPS in production.
- nginx sets CSP, nosniff, DENY framing, referrer policy and HSTS on the TLS profile.
- Rate limiting is enabled in nginx and the backend; request logs include `X-Request-ID`.
- Docker runs the backend as UID 10001 and drops the API key before isolated strategy subprocesses.
- Live trading/order placement is intentionally absent. Do not add broker execution code here.
