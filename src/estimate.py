"""Place Claude models on OpenAI's base-model log-perplexity scale.

Run:  python src/estimate.py
Writes results/estimates.csv (rounded), results/estimates.json (unrounded) and results/diagnostics.txt.

Every number here is a capability-equivalent estimate. None of them is a
measured loss for any Anthropic model. See README.md for the assumptions.
"""
import csv
import io
import json
import numpy as np
from common import RESULTS, load_eci, rows

SEED = 7          # fixed so the published numbers reproduce exactly
N = 40_000        # Monte Carlo draws per model
LOCAL = 0.5       # assumption A4: share of Epoch's published sd that is model-specific
SLOPE_LO, SLOPE_HI, SLOPE_MID = 1.0, 1.64, 1.4   # assumption A3: ECI points per 0.01 of loss, beyond the curve's ends

PUBLIC = ["Claude Opus 4.5", "Claude Opus 4.6", "Claude Opus 4.7", "Claude Opus 4.8", "Claude Fable 5",
          "Claude Opus 5", "Claude Fable 5.1", "Claude Opus 5.5", "Claude Fable 5.2"]
MODEL4_PLOT_DATE = "2026-10-15"   # METR: available to most Anthropic staff in October 2026

out = io.StringIO()
def say(*a):
    print(*a); print(*a, file=out)

rng = np.random.default_rng(SEED)
ECI = load_eci()

# --- 1. OpenAI's own curve: released models from GPT-5/5.1 on, as (ECI, loss) pairs -------------
curve = [(r["epoch_model"], float(r["log_perplexity"])) for r in rows("openai_product_to_base.csv") if r["on_2026_curve"] == "yes"]
ce = np.array([ECI[n][0] for n, _ in curve])
cl = np.array([l for _, l in curve])
csd = np.array([(ECI[n][2] - ECI[n][1]) / 3.92 for n, _ in curve])
say("OpenAI curve (ECI -> loss):")
for (n, l), e in zip(curve, ce):
    say(f"  {n:14s} ECI {e:6.2f}  loss {l:.3f}")
say("segment slopes, ECI points per 0.01 of loss:", (np.diff(ce) / (-np.diff(cl)) / 100).round(2))


def to_loss(e, ce=ce, cl=cl, slope=SLOPE_MID):
    """Loss of the OpenAI model with the same ECI. Linear between curve points, fixed slope beyond the ends."""
    e = np.asarray(e, float)
    res = np.interp(e, ce, cl)
    hi = e > ce[-1]; res[hi] = cl[-1] - (e[hi] - ce[-1]) / slope / 100
    lo = e < ce[0];  res[lo] = cl[0] + (ce[0] - e[lo]) / slope / 100
    return res


def mc(e_draws):
    """Propagate noise in the model's ECI, in the curve's ECIs, and in the extrapolation slope."""
    res = np.empty(N)
    for i in range(N):
        c = np.sort(ce + rng.normal(0, csd * LOCAL))
        res[i] = to_loss([e_draws[i]], c, cl, rng.uniform(SLOPE_LO, SLOPE_HI))[0]
    return res


# --- 2. Public Claude models -------------------------------------------------------------------
table = []
full = {}
say("\nPublic Claude models:")
for n in PUBLIC:
    e, lo, hi, d = ECI[n]
    sd = (hi - lo) / 3.92 * LOCAL
    q = np.percentile(mc(rng.normal(e, sd, N)), [10, 90])
    pt = float(to_loss([e])[0])
    full[n] = dict(date=d, point=pt, lo=float(q[0]), hi=float(q[1]))
    table.append([n, "public", d, f"{e:.2f}", f"{pt:.3f}", f"{q[0]:.3f}", f"{q[1]:.3f}", "Epoch ECI matched to OpenAI's curve"])
    say(f"  {n:18s} {d}  ECI {e:6.2f}  ->  {pt:.3f}   80% [{q[0]:.3f}, {q[1]:.3f}]")

# --- 3. Model 4: bridge Anthropic's own index (AECI) to Epoch's ECI ----------------------------
aeci = rows("anthropic_aeci.csv")
pairs = [(float(r["aeci"]), ECI[r["epoch_counterpart"]][0]) for r in aeci if r["epoch_counterpart"]]
A = np.array([p[0] for p in pairs]); E = np.array([p[1] for p in pairs])
b, a = np.polyfit(A, E, 1)
resid_sd = (E - (a + b * A)).std(ddof=2)
say(f"\nAECI -> ECI on {len(pairs)} models with both scores: slope {b:.3f}, offsets {(A - E).round(2)}, residual sd {resid_sd:.2f}")

by = {r["model"]: r for r in aeci}
m4, my = by["Internal Model"], by["Claude Mythos 5.2"]
M4, MY = float(m4["aeci"]), float(my["aeci"])
sd_m4 = (float(m4["local_ci_high"]) - float(m4["local_ci_low"])) / 3.92
sd_my = (float(my["local_ci_high"]) - float(my["local_ci_low"])) / 3.92
f52 = ECI["Claude Fable 5.2"]
anchor = f52[0] + b * (M4 - MY)       # route 1: Fable 5.2's ECI plus the AECI gap
line = a + b * M4                     # route 2: read Model 4 off the calibration line
say(f"Model 4 ECI-equivalent: anchored on Fable 5.2 = {anchor:.2f}; calibration line = {line:.2f}")

w = rng.uniform(0, 1, N)              # assumption A6: no preference between the two routes
dA = rng.normal(M4 - MY, np.hypot(sd_m4, sd_my), N)
f52_draw = rng.normal(f52[0], (f52[2] - f52[1]) / 3.92 * LOCAL, N)
e_anchor = f52_draw + b * dA
e_line = a + b * rng.normal(M4, sd_m4, N) + rng.normal(0, resid_sd, N)
e4 = w * e_anchor + (1 - w) * e_line
dr = mc(e4)
q = np.percentile(dr, [10, 90]); eq = np.percentile(e4, [10, 90])
centre = (anchor + line) / 2
pt = float(to_loss([centre])[0])
say(f"Model 4 ECI-equivalent: {centre:.1f}   80% [{eq[0]:.1f}, {eq[1]:.1f}]")
say(f"Model 4 loss-equivalent: {pt:.3f}   80% [{q[0]:.3f}, {q[1]:.3f}]")
say(f"P(Model 4 below GPT-6.2 Astra, 0.761) = {(dr < 0.761).mean():.2f}")
say(f"P(Model 4 at or below OpenAI's internal model, 0.732) = {(dr <= 0.732).mean():.2f}")
full["Anthropic Model 4"] = dict(date=MODEL4_PLOT_DATE, point=pt, lo=float(q[0]), hi=float(q[1]))
table.append(["Anthropic Model 4", "unreleased", MODEL4_PLOT_DATE, f"{centre:.2f}", f"{pt:.3f}", f"{q[0]:.3f}", f"{q[1]:.3f}",
              "AECI bridged to ECI, then matched to OpenAI's curve"])

# --- 4. Side checks ------------------------------------------------------------------------------
say(f"\nOpenAI's internal model (0.732) in ECI terms: {ce[-1] + 2.9 * SLOPE_LO:.1f} to {ce[-1] + 2.9 * SLOPE_HI:.1f}")
say("Same base model, different product (ECI gap):")
for lo_m, hi_m in [("GPT-4o (May 2024)", "o1"), ("GPT-4.1", "o3"), ("GPT-5.2", "GPT-5.2 Pro"), ("GPT-5.4", "GPT-5.4 Pro"), ("GPT-5.5", "GPT-5.5 Pro")]:
    say(f"  {lo_m} -> {hi_m}: {ECI[hi_m][0] - ECI[lo_m][0]:+.2f}")
say(f"GPT-5.5 Pro read off the curve: {to_loss([ECI['GPT-5.5 Pro'][0]])[0]:.3f} (its base model is published at 0.848)")

RESULTS.mkdir(exist_ok=True)
with open(RESULTS / "estimates.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["model", "status", "date", "eci_or_equivalent", "loss_equivalent", "range80_low", "range80_high", "basis"])
    wr.writerows(table)
(RESULTS / "estimates.json").write_text(json.dumps(full, indent=1), encoding="utf-8")   # unrounded, read by chart.py
(RESULTS / "diagnostics.txt").write_text(out.getvalue(), encoding="utf-8")
