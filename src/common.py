"""Shared loaders. All inputs live in ../data as plain CSV."""
import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"


def rows(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_eci():
    """model -> (eci, ci_low, ci_high, date). A missing interval is read as zero width."""
    out = {}
    for r in rows("epoch_eci_subset.csv"):
        e = float(r["eci"])
        lo = float(r["eci_ci_low"]) if r["eci_ci_low"] else e
        hi = float(r["eci_ci_high"]) if r["eci_ci_high"] else e
        out[r["model"]] = (e, lo, hi, r["date"])
    return out


def year_fraction(iso):
    y, m, d = map(int, iso.split("-"))
    return y + (date(y, m, d) - date(y, 1, 1)).days / 365.25
