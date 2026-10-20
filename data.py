"""Data sintetis + penyimpanan SQLite (keterampilan SQL).

Semua data DIBUAT SECARA ACAK untuk pembelajaran. Ganti dengan data nyata
(misalnya titik pelanggan dari CSV/GeoJSON) tanpa mengubah modul lain.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# Pusat kota fiktif. Ubah sesuai wilayah yang ingin dianalisis.
CENTER = (-6.90, 107.60)

SCHEMA = """
DROP TABLE IF EXISTS demand;
DROP TABLE IF EXISTS candidates;
CREATE TABLE demand (
    id INTEGER PRIMARY KEY,
    district TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    weekly_orders INTEGER NOT NULL
);
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    land_price_mio REAL NOT NULL,   -- juta rupiah per m2
    flood_risk REAL NOT NULL,       -- 0 (aman) .. 1 (rawan)
    road_access REAL NOT NULL       -- 0 (sulit) .. 1 (dekat jalan utama)
);
"""

DISTRICTS = [
    # nama, offset lat, offset lon, sebaran (derajat), jumlah titik
    ("Pusat", 0.00, 0.00, 0.020, 150),
    ("Utara", 0.07, 0.02, 0.030, 90),
    ("Timur", -0.01, 0.09, 0.035, 90),
    ("Selatan", -0.08, -0.03, 0.040, 70),
]


def make_demand(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for name, dlat, dlon, spread, n in DISTRICTS:
        lat = rng.normal(CENTER[0] + dlat, spread, n)
        lon = rng.normal(CENTER[1] + dlon, spread, n)
        orders = np.clip(rng.lognormal(2.2, 0.7, n), 1, 200).astype(int)
        rows += [(name, a, b, int(o)) for a, b, o in zip(lat, lon, orders)]
    df = pd.DataFrame(rows, columns=["district", "lat", "lon", "weekly_orders"])
    df.insert(0, "id", range(1, len(df) + 1))
    return df


def make_candidates(n: int = 12, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    lat = rng.uniform(CENTER[0] - 0.10, CENTER[0] + 0.10, n)
    lon = rng.uniform(CENTER[1] - 0.08, CENTER[1] + 0.12, n)
    dist_center = np.hypot(lat - CENTER[0], lon - CENTER[1])
    # Lahan dekat pusat lebih mahal; ada derau acak
    price = np.clip(9 - 40 * dist_center + rng.normal(0, 0.8, n), 1.5, 12)
    flood = np.clip(rng.beta(2, 5, n) + 0.2 * (lat < CENTER[0] - 0.03), 0, 1)
    access = np.clip(rng.beta(4, 2, n), 0, 1)
    return pd.DataFrame({
        "id": range(1, n + 1),
        "name": [f"Lokasi-{i:02d}" for i in range(1, n + 1)],
        "lat": lat, "lon": lon,
        "land_price_mio": price.round(2),
        "flood_risk": flood.round(2),
        "road_access": access.round(2),
    })


def init_db(path: str | Path, seed: int = 42, n_candidates: int = 12) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.executescript(SCHEMA)
        make_demand(seed).to_sql("demand", con, if_exists="append", index=False)
        make_candidates(n_candidates, seed + 1).to_sql(
            "candidates", con, if_exists="append", index=False)


def load(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with sqlite3.connect(path) as con:
        cands = pd.read_sql_query(
            "SELECT id, name, lat, lon, land_price_mio, flood_risk, road_access "
            "FROM candidates ORDER BY id", con)
        demand = pd.read_sql_query(
            "SELECT id, district, lat, lon, weekly_orders FROM demand ORDER BY id", con)
    return cands, demand


def district_summary(path: str | Path) -> pd.DataFrame:
    """Contoh agregasi SQL: ringkasan permintaan per kecamatan."""
    q = """
    SELECT district,
           COUNT(*)           AS titik,
           SUM(weekly_orders) AS total_order_mingguan,
           ROUND(AVG(weekly_orders), 1) AS rata2_order
    FROM demand
    GROUP BY district
    ORDER BY total_order_mingguan DESC
    """
    with sqlite3.connect(path) as con:
        return pd.read_sql_query(q, con)
