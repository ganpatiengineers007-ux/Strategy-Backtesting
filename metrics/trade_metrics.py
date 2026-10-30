def compute(trades):
    pnl = [t["pnl"] for t in trades]
    wins, losses = [x for x in pnl if x > 0], [x for x in pnl if x <= 0]
    gl = abs(sum(losses))
    return {"n_trades": len(pnl), "total_pnl": sum(pnl), "fees_total": sum(t["fees"] for t in trades),
            "avg_win": sum(wins) / len(wins) if wins else 0.0,
            "avg_loss": sum(losses) / len(losses) if losses else 0.0,
            "profit_factor": (sum(wins) / gl) if gl else None}
