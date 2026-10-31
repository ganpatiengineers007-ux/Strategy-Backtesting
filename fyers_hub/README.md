# Fyers Data Hub (Strategy-Backtesting के लिए)

Fyers → **डेटा हब (SQLite)** → **DataHub reader** → आपकी strategy / backtest।
GTS या GTS-Tools से इसका कोई संबंध नहीं है। Secrets (टोकन, चाबियाँ) repo के बाहर `~/.fyers_hub/` में रहते हैं, इसलिए `git add .` से कभी push नहीं होंगे।

## फोल्डर
```
fyers_hub/
  auth/      store.py (टोकन फ़ाइल), flow.py (login, token, refresh), web.py (browser token app)
  client/    api.py (Fyers calls + retry + auto-refresh), limiter.py (rate limit)
  storage/   db.py (हब की टेबलें)
  ingest/    instruments.py (symbol master), history.py (पुरानी candles), quotes.py (लाइव भाव),
             chain.py (option chain + greeks), live.py (polling loop), ws.py (websocket 5S/1m)
  process/   resample.py (कोई भी timeframe), greeks.py, quality.py, ticks.py (tick → candle)
  serve/     hub.py  <- strategies सिर्फ़ यहीं से डेटा लेती हैं
  config/    watchlist.txt, underlyings.txt   tests/
```

## इंस्टॉल (एक बार)
```
cd ~/Strategy-Backtesting
unzip -n fyers_hub.zip
source .venv/bin/activate
pip install fyers-apiv3
python -m fyers_hub init
nano ~/.fyers_hub/.env        # FYERS_APP_ID, FYERS_SECRET_KEY, (चाहें तो FYERS_PIN) भरें
python -m fyers_hub doctor
```

## टोकन (रोज़ एक बार)
```
python -m fyers_hub auth
```
लिंक फ़ोन के browser में खोलें → Fyers login → login के बाद के page का **पूरा URL** copy करके terminal में paste करें।
टोकन फ़ाइल में सेव होता है, स्क्रीन पर दिखता नहीं। `FYERS_PIN` भरा हो तो `python -m fyers_hub refresh` से 15 दिन तक बिना login के नया टोकन मिलता है, और हब खुद भी refresh कर लेता है।
Browser वाला app: `.env` में `FYERS_REDIRECT_URI=http://127.0.0.1:8765/callback` रखें (Fyers app में भी वही), फिर `python -m fyers_hub token-app`।

## डेटा खींचना और प्रोसेस
| काम | कमांड |
|---|---|
| Symbol list/lot size | `python -m fyers_hub symbols --segments NSE_CM NSE_FO` |
| पुरानी candles (1m + 1D) और derived (2,3,5,10,15,30,60 मिनट, 15D) | `python -m fyers_hub backfill` |
| 5 सेकंड की candles (Fyers सिर्फ़ हाल के दिन देता है) | `python -m fyers_hub backfill --tf 5S --no-derive` |
| कोई और timeframe हब से बनाना | `python -m fyers_hub derive --to 7 20 45` |
| Option chain + greeks | `python -m fyers_hub chain --expiries 2` |
| लाइव (भाव + chain + आज की 1m candles) | `python -m fyers_hub live` |
| लाइव 5S/1m candles (websocket) | `python -m fyers_hub ws` |
| डेटा जाँच | `python -m fyers_hub validate` |
| CSV | `python -m fyers_hub export NSE:SBIN-EQ 5 --out sbin5.csv` |

Symbols `~/.fyers_hub/watchlist.txt` से आते हैं (चाहें तो `--symbols NSE:SBIN-EQ ...`)।

## Timeframe नियम
- `5S 10S 15S 30S 45S`, `1 2 3 5 10 15 30 60 120 240` (मिनट), `D` (1 दिन), `15D` (15 weekdays का block)।
- मिनट वाली candles session खुलने से बनती हैं (NSE 09:15, MCX 09:00)।
- `15D` = सोम–शुक्र के 15 दिन के block, एक तय पुरानी तारीख से गिने जाते हैं। पुराना डेटा बाद में जोड़ने पर भी block नहीं बदलते।
- हब में जो timeframe stored नहीं है वह `hub.candles()` माँगने पर उपलब्ध base से अपने आप बन जाता है।

## Strategy में इस्तेमाल
```python
from fyers_hub.serve.hub import DataHub

hub = DataHub()
bars = hub.candles("NSE:NIFTY50-INDEX", "5", start="2025-01-01")      # Bar(ts, open, high, low, close, volume)
df   = hub.candles("NSE:SBIN-EQ", "15", start="2025-01-01", as_df=True)  # pandas (IST index)
for bar in hub.iter_bars("NSE:SBIN-EQ", "1", "2025-01-01", "2025-03-31"):
    ...                                                                   # scalping / intraday
chain = hub.option_chain("NSE:NIFTY50-INDEX")                            # iv, delta, gamma, theta, vega, rho
atm   = hub.atm("NSE:NIFTY50-INDEX")                                     # expiry strategies
quote = hub.latest_quote("NSE:SBIN-EQ")                                  # scanner
stocks = hub.universe("equity")                                          # scanner की universe
```

## ज़रूरी बातें
- Fyers की limit `~/.fyers_hub/.env` में `FYERS_MAX_PER_SEC` / `FYERS_MAX_PER_MIN` से तय होती है। एक ही Fyers account पर दूसरा सिस्टम साथ चल रहा हो तो limit बँट जाती है।
- Greeks हम खुद निकालते हैं (Black-Scholes, risk-free rate `HUB_RISK_FREE_RATE`)।
- Holiday calendar शामिल नहीं है। `live` सिर्फ़ सोम–शुक्र बाज़ार के घंटों में चलता है।
- Tests: `python -m pytest fyers_hub/tests` (offline, Fyers नहीं बुलाते)।
