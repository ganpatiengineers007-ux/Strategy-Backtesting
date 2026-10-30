import random


def bootstrap_mean_ci(values, n=1000, alpha=0.05, seed=7):
    if len(values) < 5:
        return None
    rng, k = random.Random(seed), len(values)
    means = sorted(sum(rng.choice(values) for _ in range(k)) / k for _ in range(n))
    return means[int(n * alpha / 2)], means[int(n * (1 - alpha / 2)) - 1]
