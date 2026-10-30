def format_metrics(metrics):
    width = max((len(k) for k in metrics), default=0)
    return "\n".join(f"{k:<{width}}  {v}" for k, v in metrics.items())
