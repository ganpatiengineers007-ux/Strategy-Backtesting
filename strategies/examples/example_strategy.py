"""Example: naya strategy banane ka template. index 1 par BUY, stop/target % se."""
from strategies.base import Strategy
from strategies.models import Signal


class ExampleStrategy(Strategy):
    strategy_id = "example"
    required_data = ()

    def on_bar(self, ctx):
        if ctx.index == 1 and ctx.position is None:
            c = ctx.bar.close
            return Signal("BUY", stop_loss=round(c * 0.99, 2), target=round(c * 1.02, 2), reason="example")
        return None
