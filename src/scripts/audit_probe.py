"""Temporary audit probe: schema + date-range inventory for data/ on disk."""

import os

import polars as pl

from src.events.paths import REPO_ROOT

p = REPO_ROOT / "data" / "GOLDEN_PARQUET" / "ABB.NS.parquet"
lf = pl.scan_parquet(p)
print("PARQUET schema:", dict(lf.collect_schema()))
print(
    lf.select(
        pl.len().alias("rows"),
        pl.col("date").min().alias("min"),
        pl.col("date").max().alias("max"),
    ).collect()
)

print("--- GOLDEN CSV head (ABB.NS) ---")
print(pl.read_csv(REPO_ROOT / "data" / "GOLDEN" / "ABB.NS.csv", n_rows=3))
n = pl.scan_csv(REPO_ROOT / "data" / "GOLDEN" / "ABB.NS.csv").select(pl.len()).collect().item()
print("csv rows:", n)

print("--- IV / option parquets ---")
for f in [
    REPO_ROOT / "data" / "GOLDEN_IV" / "atm_iv_daily.parquet",
    REPO_ROOT / "data" / "GOLDEN_IV" / "atm_iv_daily_2020_2022.parquet",
    REPO_ROOT / "data" / "GOLDEN_IV" / "option_marks_daily.parquet",
    REPO_ROOT / "data" / "GOLDEN_IV" / "nifty_option_snapshots_zenodo.parquet",
]:
    if not os.path.exists(f):
        print(f, "MISSING")
        continue
    lf2 = pl.scan_parquet(f)
    sch = dict(lf2.collect_schema())
    rows = lf2.select(pl.len()).collect().item()
    print(f, "rows=", rows)
    print("   cols=", list(sch))
    for c in sch:
        if "date" in c.lower() or "expiry" in c.lower():
            print("   ", c, lf2.select(pl.col(c).min(), pl.col(c).max()).collect().row(0))
            break
