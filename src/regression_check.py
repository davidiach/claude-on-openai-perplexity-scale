"""Alternative specification: ECI = a + b*loss + c*time + d*reasoning, on OpenAI products.

Run:  python src/regression_check.py
Writes results/regression_check.txt.

Not used for the chart. It is here to show how unstable the loss slope is
and why loss and time cannot be separated inside 2026.
"""
import io
import numpy as np
from common import RESULTS, load_eci, rows, year_fraction

out = io.StringIO()
def say(*a):
    print(*a); print(*a, file=out)

ECI = load_eci()
prod = rows("openai_product_to_base.csv")
names = [r["epoch_model"] for r in prod]
X = np.array([[1, float(r["log_perplexity"]), year_fraction(r["date_override"] or ECI[r["epoch_model"]][3]) - 2025, int(r["reasoning"])] for r in prod])
y = np.array([ECI[n][0] for n in names])


def ols(X, y):
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    r = y - X @ beta
    cov = r @ r / (len(y) - X.shape[1]) * np.linalg.inv(X.T @ X)
    return beta, np.sqrt(np.diag(cov)), r


beta, se, r = ols(X, y)
say(f"n = {len(y)} OpenAI products")
say(f"ECI per 0.01 of loss: {-beta[1] / 100:.2f} +/- {se[1] / 100:.2f}")
say(f"ECI per year at fixed loss: {beta[2]:.1f} +/- {se[2]:.1f}")
say(f"ECI for a reasoning model: {beta[3]:.1f} +/- {se[3]:.1f}")
say(f"residual sd: {r.std(ddof=4):.2f} ECI = {r.std(ddof=4) / -beta[1]:.3f} of loss")
say(f"corr(loss, time), all products: {np.corrcoef(X[:, 1], X[:, 2])[0, 1]:.3f}")
say("\nresiduals:")
for n, ri in zip(names, r):
    say(f"  {n:24s} {ri:+.1f}")
say("\nleave-one-out, ECI per 0.01 of loss:")
for i, n in enumerate(names):
    bb = ols(np.delete(X, i, 0), np.delete(y, i))[0]
    say(f"  without {n:24s} {-bb[1] / 100:.2f}")
m = [i for i, p in enumerate(prod) if p["on_2026_curve"] == "yes" and p["epoch_model"] != "GPT-5.1"]
say(f"\nDec 2025 onward ({len(m)} products):")
say(f"  corr(loss, time) = {np.corrcoef(X[m, 1], X[m, 2])[0, 1]:.3f}")
say(f"  loss alone: {-np.polyfit(X[m, 1], y[m], 1)[0] / 100:.2f} ECI per 0.01")
say(f"  time alone: {np.polyfit(X[m, 2], y[m], 1)[0]:.1f} ECI per year")
RESULTS.mkdir(exist_ok=True)
(RESULTS / "regression_check.txt").write_text(out.getvalue(), encoding="utf-8")
