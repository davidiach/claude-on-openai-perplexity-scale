"""Draw the chart from data/ and results/estimates.json.

Run:  python src/estimate.py && python src/chart.py
Writes results/model4_on_openai_scale.png (2400 x 1350).
"""
import datetime as dt
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as md
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.lines import Line2D
from common import RESULTS, rows

plt.rcParams["font.family"] = ["Inter", "DejaVu Sans"]   # Inter if installed
SURF, INK, INK2, MUTE, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8983", "#e7e6e1"
BLUE, ORNG, ORNG_L = "#2a78d6", "#eb6834", "#f6b79d"
D = lambda s: dt.datetime.strptime(s, "%Y-%m-%d")

est = json.loads((RESULTS / "estimates.json").read_text(encoding="utf-8"))
oa_rows = [r for r in rows("openai_log_perplexity.csv") if r["plot_date"]]
OA = [(r["label"], r["plot_date"], float(r["log_perplexity"])) for r in oa_rows if r["released"] == "yes"]
INT = next((r["plot_date"], float(r["log_perplexity"])) for r in oa_rows if r["released"] == "no")
SHORT = {"GPT-5.3-Codex / 5.4": "GPT-5.4"}
# Opus 4.5 is computed but not drawn: it falls on the flat GPT-5.1 -> GPT-5.2 stretch, where the range is artificially narrow.
CL = ["Claude Opus 4.6", "Claude Opus 4.7", "Claude Opus 4.8", "Claude Fable 5", "Claude Opus 5", "Claude Fable 5.1", "Claude Opus 5.5", "Claude Fable 5.2"]

fig = plt.figure(figsize=(12, 6.75), dpi=200, facecolor=SURF)
ax = fig.add_axes([0.062, 0.215, 0.725, 0.535], facecolor=SURF)
ax.set_xlim(D("2025-11-20"), D("2026-12-06")); ax.set_ylim(0.676, 0.902)
ax.axhspan(0.68, 0.70, color=BLUE, alpha=0.07, lw=0)
ax.text(D("2025-11-27"), 0.690, "OpenAI’s “?” window, 0.68–0.70", color=INK2, fontsize=9.5, va="center")
for y in (0.70, 0.75, 0.80, 0.85, 0.90):
    ax.axhline(y, color=GRID, lw=0.8, zorder=0)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#c9c8c2"); ax.spines["bottom"].set_linewidth(0.8)
ax.set_yticks([0.70, 0.75, 0.80, 0.85, 0.90]); ax.set_yticklabels(["0.70", "0.75", "0.80", "0.85", "0.90"])
ax.tick_params(axis="y", length=0, labelsize=10.5, labelcolor=INK2, pad=6)
ax.xaxis.set_major_locator(md.MonthLocator(bymonth=[1, 3, 5, 7, 9, 11]))
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
    lambda v, p: md.num2date(v).strftime("%b") + ("\n2026" if md.num2date(v).month == 1 else "")))
ax.tick_params(axis="x", length=3.5, color="#c9c8c2", labelsize=10.5, labelcolor=INK2, pad=5)

# OpenAI, published
ox = [D(d) for _, d, _ in OA]; oy = [l for *_, l in OA]
ax.plot(ox, oy, color=BLUE, lw=2, solid_capstyle="round", solid_joinstyle="round", zorder=3)
ax.scatter(ox, oy, s=62, color=BLUE, edgecolor=SURF, linewidth=1.6, zorder=4)
ax.scatter([D(INT[0])], [INT[1]], s=78, marker="s", facecolor=SURF, edgecolor=BLUE, linewidth=2, zorder=4)
olab = {"GPT-5.2": (-2, -13, "left"), "GPT-5.4": (-7, -11, "right"), "GPT-5.5": (-8, -9, "right"),
        "GPT-5.6 Sol": (5, 19, "left"), "GPT-6 Astra": (-9, -8, "right")}
for n, d, l in OA:
    n = SHORT.get(n, n)
    if n in olab:
        dx, dy, ha = olab[n]
        ax.annotate(n, (D(d), l), xytext=(dx, dy), textcoords="offset points", ha=ha, va="top", fontsize=10, color=INK2)

# Claude, public
for n in CL:
    r = est[n]; x = D(r["date"])
    ax.plot([x, x], [r["lo"], r["hi"]], color=ORNG_L, lw=2, solid_capstyle="round", zorder=2)
    ax.scatter([x], [r["point"]], s=62, color=ORNG, edgecolor=SURF, linewidth=1.6, zorder=5)
clab = {"Claude Opus 4.6": (7, 9, "left"), "Claude Opus 4.7": (7, 8, "left"), "Claude Opus 4.8": (8, 7, "left"),
        "Claude Fable 5": (-9, -16, "right"), "Claude Opus 5": (8, 7, "left"), "Claude Fable 5.1": (6, 11, "left"),
        "Claude Opus 5.5": (9, 5, "left")}
for n, (dx, dy, ha) in clab.items():
    r = est[n]
    ax.annotate(n.replace("Claude ", ""), (D(r["date"]), r["point"]), xytext=(dx, dy), textcoords="offset points",
                ha=ha, va="bottom", fontsize=10, color=INK2)

# Model 4, unreleased
m = est["Anthropic Model 4"]; mx = D(m["date"])
ax.plot([mx, mx], [m["lo"], m["hi"]], color=ORNG, lw=2.4, solid_capstyle="round", zorder=5)
ax.scatter([mx], [m["point"]], s=175, marker="D", facecolor=SURF, edgecolor=ORNG, linewidth=2.6, zorder=6)
tx = D("2026-08-30")
ax.annotate("", (mx, m["point"]), xytext=(tx, 0.7405), arrowprops=dict(arrowstyle="-", color=MUTE, lw=0.8, shrinkA=0, shrinkB=9), zorder=1)
ax.text(tx, 0.7405, "Anthropic Model 4 ", ha="right", va="bottom", fontsize=13, fontweight="bold", color=INK)
ax.text(tx, 0.7385, f"unreleased · about {m['point']:.2f} (range {m['lo']:.2f}–{m['hi']:.2f}) ", ha="right", va="top", fontsize=10.5, color=INK2)


def side(y_pt, y_lab, title, sub, mk, mfc, mec, x_pt):
    xe, xt, xl = D("2026-12-10"), D("2026-12-19"), D("2026-12-28")
    ax.plot([x_pt, xe], [y_pt, y_lab], color=MUTE, lw=0.8, clip_on=False, zorder=1)
    ax.plot([xt], [y_lab], marker=mk, ms=8.5, mfc=mfc, mec=mec, mew=1.8, clip_on=False, zorder=6)
    ax.text(xl, y_lab - 0.0005, title, fontsize=11.5, fontweight="bold", color=INK, va="bottom", ha="left", clip_on=False)
    ax.text(xl, y_lab + 0.0015, sub, fontsize=10, color=INK2, va="top", ha="left", clip_on=False)


top = OA[-1]; f52 = est["Claude Fable 5.2"]
side(top[2], 0.789, top[0], f"published · {top[2]:.3f}", "o", BLUE, SURF, D(top[1]) + dt.timedelta(days=5))
side(f52["point"], 0.757, "Claude Fable 5.2", f"estimate · about {f52['point']:.3f}", "o", ORNG, SURF, D(f52["date"]) + dt.timedelta(days=13))
side(INT[1], 0.725, "OpenAI internal model", f"unreleased · {INT[1]:.3f}", "s", SURF, BLUE, D(INT[0]) + dt.timedelta(days=5))

ax.text(D("2025-11-27"), 0.772, "How to read a Claude point", fontsize=10.5, fontweight="bold", color=INK, va="top")
ax.text(D("2025-11-27"), 0.7625, "Epoch AI scores that model about as capable as an\nOpenAI model whose base loss is the value shown.\nIt is not Anthropic’s own training loss.",
        fontsize=10, color=INK2, va="top", linespacing=1.3)
ax.set_ylabel("Base-model log-perplexity  (lower is better)", fontsize=10.5, color=INK2, labelpad=8)

fig.text(0.03, 0.945, "Anthropic’s internal Model 4 lands near 0.75 on OpenAI’s perplexity scale", fontsize=21.5, fontweight="bold", color=INK, va="center")
fig.text(0.03, 0.888, "That is past GPT-6.2 Astra (0.761) and short of OpenAI’s own unreleased model (0.732). Neither gap is outside the noise.", fontsize=12.2, color=INK2, va="center")
h = [Line2D([], [], color=BLUE, lw=2, marker="o", ms=7, mec=SURF, mew=1.2), Line2D([], [], ls="", marker="s", ms=7.5, mfc=SURF, mec=BLUE, mew=1.8),
     Line2D([], [], color=ORNG_L, lw=2, marker="o", ms=7, mfc=ORNG, mec=SURF, mew=1.2), Line2D([], [], color=ORNG, lw=2.2, marker="D", ms=8, mfc=SURF, mec=ORNG, mew=2)]
lg = fig.legend(h, ["OpenAI, published loss", "OpenAI internal, unreleased", "Claude, public (estimate, 80% range)", "Anthropic Model 4, unreleased (estimate)"],
                loc="center left", bbox_to_anchor=(0.024, 0.822), ncol=4, frameon=False, fontsize=10.5, handlelength=1.9, columnspacing=2.0, handletextpad=0.6)
for t in lg.get_texts():
    t.set_color(INK2)

fig.text(0.03, 0.085, "Method: each Claude model is placed at the loss of the OpenAI model with the same Epoch Capabilities Index score. Model 4 has no Epoch score; it is bridged from Anthropic’s own index\n(178.8 against 177.1 for Mythos 5.2, on 15 benchmarks). Assumes both labs get the same lift from post-training. Treat gaps under about 0.02 as ties.",
         fontsize=8.6, color=INK2, va="center", linespacing=1.5)
fig.text(0.03, 0.033, "Sources: OpenAI, “Perplexity and Intelligence” (22 Nov 2026) · Epoch AI ECI scores · Anthropic, Fable 5.2 / Mythos 5.2 system card · METR (5 Nov 2026).  Estimates made with Claude from public data.",
         fontsize=8.6, color=MUTE, va="center")
fig.savefig(RESULTS / "model4_on_openai_scale.png", dpi=200, facecolor=SURF)
print("wrote", RESULTS / "model4_on_openai_scale.png")
