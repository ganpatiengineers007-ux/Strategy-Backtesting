"""GammaBlastStrategy: PLACEHOLDER. Asli niyam yahan daalne hain.
Option chain + OI chahiye; na ho to engine backtest ko BLOCKED karta hai."""
from strategies.base import Strategy


class GammaBlastStrategy(Strategy):
    strategy_id = "gamma_blast"
    required_data = ("option_chain", "oi")

    def on_bar(self, ctx):
        return None  # TODO: real entry/exit rules
