"""GammaBlastStrategy: Gamma exposure based strategy for index options.
Requires option chain + OI data; engine blocks backtest if missing."""
from strategies.base import Strategy
from strategies.models import Signal


class GammaBlastStrategy(Strategy):
    strategy_id = "gamma_blast"
    required_data = ("option_chain", "oi")

    def __init__(self, params=None):
        super().__init__(params)
        # Default parameters
        self.params.setdefault("gamma_threshold", 1000000)  # Gamma exposure threshold
        self.params.setdefault("iv_threshold", 0.20)  # IV percentile threshold
        self.params.setdefault("stop_pct", 1.0)  # Stop loss %
        self.params.setdefault("target_pct", 2.0)  # Target %
        self.params.setdefault("entry_hour", 9)  # Entry hour (IST)
        self.params.setdefault("entry_minute", 30)  # Entry minute
        self.params.setdefault("exit_hour", 15)  # Exit hour
        self.params.setdefault("exit_minute", 15)  # Exit minute

    def on_bar(self, ctx):
        p, bar = self.params, ctx.bar
        t = int(bar.ts[11:13]) * 60 + int(bar.ts[14:16])

        if ctx.position is not None:
            if t >= p["exit_hour"] * 60 + p["exit_minute"]:
                return Signal("EXIT", reason="EOD_EXIT")
            return None

        # Only trade at entry time
        if t != p["entry_hour"] * 60 + p["entry_minute"]:
            return None

        # Need option chain data in extras
        if not hasattr(bar, 'extras') or 'option_chain' not in bar.extras:
            return None

        chain = bar.extras['option_chain']
        if not chain:
            return None

        # Find ATM strike
        spot = bar.close
        atm_strike = min(chain, key=lambda x: abs(x.get('strike', 0) - spot))
        
        # Get CE and PE for ATM
        ce = next((c for c in chain if c.get('strike') == atm_strike.get('strike') and c.get('opt_type') == 'CE'), None)
        pe = next((c for c in chain if c.get('strike') == atm_strike.get('strike') and c.get('opt_type') == 'PE'), None)
        
        if not ce or not pe:
            return None

        # Calculate total gamma exposure
        ce_gamma = ce.get('gamma', 0) * ce.get('oi', 0)
        pe_gamma = pe.get('gamma', 0) * pe.get('oi', 0)
        total_gamma = ce_gamma + pe_gamma

        # Check IV
        ce_iv = ce.get('iv', 0)
        pe_iv = pe.get('iv', 0)
        avg_iv = (ce_iv + pe_iv) / 2

        # Signal logic: High gamma + low IV = potential gamma blast
        if total_gamma > p["gamma_threshold"] and avg_iv < p["iv_threshold"]:
            # Direction based on put/call gamma imbalance
            if ce_gamma > pe_gamma:
                # Call gamma dominant - expect upside
                return Signal(
                    "BUY",
                    stop_loss=round(bar.close * (1 - p["stop_pct"] / 100), 2),
                    target=round(bar.close * (1 + p["target_pct"] / 100), 2),
                    reason=f"gamma_blast_call: gamma={total_gamma:.0f}, iv={avg_iv:.2f}"
                )
            else:
                # Put gamma dominant - expect downside (but we only go long in this framework)
                return Signal(
                    "BUY",
                    stop_loss=round(bar.close * (1 - p["stop_pct"] / 100), 2),
                    target=round(bar.close * (1 + p["target_pct"] / 100), 2),
                    reason=f"gamma_blast_put: gamma={total_gamma:.0f}, iv={avg_iv:.2f}"
                )

        return None
