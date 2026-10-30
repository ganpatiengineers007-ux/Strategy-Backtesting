"""Tiny numpy MLP (Adam, class weights, L2) + walk-forward probability helper. No external ML libs."""
from __future__ import annotations
import numpy as np


class MLP:
    def __init__(self, n_in: int, hidden=(16, 8), lr: float = 0.01, l2: float = 1e-4, seed: int = 0):
        r = np.random.default_rng(seed)
        sizes = [n_in, *hidden, 1]
        self.W = [r.normal(0, np.sqrt(2.0 / a), (a, b)) for a, b in zip(sizes[:-1], sizes[1:])]
        self.b = [np.zeros(b) for b in sizes[1:]]
        self.mW = [np.zeros_like(w) for w in self.W]; self.vW = [np.zeros_like(w) for w in self.W]
        self.mb = [np.zeros_like(b) for b in self.b]; self.vb = [np.zeros_like(b) for b in self.b]
        self.lr, self.l2, self.t, self.rng = lr, l2, 0, r
        self.mu = np.zeros(n_in); self.sd = np.ones(n_in)

    def _fwd(self, X):
        acts = [X]
        for i, (W, b) in enumerate(zip(self.W, self.b)):
            z = acts[-1] @ W + b
            z = np.maximum(z, 0.0) if i < len(self.W) - 1 else 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
            acts.append(z)
        return acts

    def fit(self, X, y, epochs: int = 40, batch: int = 256, pos_weight: float = 1.0):
        X = np.nan_to_num(np.asarray(X, float)); y = np.asarray(y, float)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Xs = (X - self.mu) / self.sd
        n = len(Xs)
        for _ in range(epochs):
            idx = self.rng.permutation(n)
            for s in range(0, n, batch):
                j = idx[s:s + batch]
                acts = self._fwd(Xs[j])
                w = np.where(y[j] > 0.5, pos_weight, 1.0)[:, None]
                delta = (acts[-1] - y[j][:, None]) * w / len(j)
                for i in reversed(range(len(self.W))):
                    gW = acts[i].T @ delta + self.l2 * self.W[i]
                    gb = delta.sum(0)
                    if i > 0:
                        delta = (delta @ self.W[i].T) * (acts[i] > 0)
                    self._adam(i, gW, gb)
        return self

    def _adam(self, i, gW, gb, b1=0.9, b2=0.999, eps=1e-8):
        self.t += 1
        for g, m, v, p in ((gW, self.mW, self.vW, self.W), (gb, self.mb, self.vb, self.b)):
            m[i] = b1 * m[i] + (1 - b1) * g
            v[i] = b2 * v[i] + (1 - b2) * g * g
            p[i] -= self.lr * (m[i] / (1 - b1 ** self.t)) / (np.sqrt(v[i] / (1 - b2 ** self.t)) + eps)

    def predict_proba(self, X) -> np.ndarray:
        Xs = (np.nan_to_num(np.asarray(X, float)) - self.mu) / self.sd
        return self._fwd(Xs)[-1][:, 0]


def walk_forward_probs(X, y, min_train: int, retrain_every: int, embargo: int,
                       epochs: int = 30, hidden=(16, 8), seed: int = 0, pos_weight: float = 1.0) -> np.ndarray:
    """Expanding-window walk-forward. Prediction at t uses a model fit on rows < t - embargo only
    (labels that peek `embargo` steps ahead are therefore never seen). NaN until min_train."""
    n = len(X)
    out = np.full(n, np.nan)
    t = min_train + embargo
    while t < n:
        end = min(t + retrain_every, n)
        tr = slice(0, t - embargo)
        ok = ~np.isnan(y[tr]) & ~np.isnan(X[tr]).any(1)
        if ok.sum() >= 50:
            m = MLP(X.shape[1], hidden=hidden, seed=seed).fit(X[tr][ok], y[tr][ok], epochs=epochs, pos_weight=pos_weight)
            out[t:end] = m.predict_proba(X[t:end])
        t = end
    return out
