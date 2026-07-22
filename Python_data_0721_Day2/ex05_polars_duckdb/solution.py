from pathlib import Path
import time

import pandas as pd
import polars as pl


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "events_large.csv"
)


print("=== STEP 1: Pandas 기준선 ===")

start = time.perf_counter()

df = pd.read_csv(DATA_PATH)

res_pandas = (
    df[df["status"] == "ok"]
    .groupby("event_type")
    .agg(
        cnt=("value", "count"),
        avg=("value", "mean"),
    )
    .sort_values("cnt", ascending=False)
    .reset_index()
)

t_pandas = (time.perf_counter() - start) * 1000

print(f"Pandas 실행 시간: {t_pandas:.0f} ms")
print(res_pandas)

print("\n=== STEP 2: Polars Lazy 방식 ===")

start = time.perf_counter()

res_polars = (
    pl.scan_csv(DATA_PATH)
    .filter(pl.col("status") == "ok")
    .group_by("event_type")
    .agg(
        [
            pl.len().alias("cnt"),
            pl.col("value").mean().alias("avg"),
        ]
    )
    .sort("cnt", descending=True)
    .collect()
)

t_polars = (time.perf_counter() - start) * 1000

print(f"Polars 실행 시간: {t_polars:.0f} ms")
print(res_polars)