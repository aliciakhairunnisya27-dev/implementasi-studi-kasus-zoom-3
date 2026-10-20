"""Analisis spasial: jangkauan layanan, jarak, dan skor multikriteria."""
import numpy as np
import pandas as pd

EARTH_KM = 6371.0088

DEFAULT_WEIGHTS = {
    "coverage": 0.35,   # % order yang berada dalam radius layanan
    "distance": 0.20,   # jarak rata-rata terbobot ke pelanggan (makin kecil makin baik)
    "price": 0.15,      # harga lahan (makin murah makin baik)
    "flood": 0.15,      # risiko banjir (makin kecil makin baik)
    "access": 0.15,     # akses jalan utama
}


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_KM * np.arcsin(np.sqrt(a))


def distance_matrix(cands: pd.DataFrame, demand: pd.DataFrame) -> np.ndarray:
    """Matriks jarak (kandidat x pelanggan) dalam km."""
    return haversine_km(cands["lat"].to_numpy()[:, None], cands["lon"].to_numpy()[:, None],
                        demand["lat"].to_numpy()[None, :], demand["lon"].to_numpy()[None, :])


def normalize_weights(weights: dict | None) -> dict:
    w = dict(DEFAULT_WEIGHTS if weights is None else weights)
    unknown = set(w) - set(DEFAULT_WEIGHTS)
    if unknown:
        raise ValueError(f"Kriteria tidak dikenal: {sorted(unknown)}")
    w = {k: float(w.get(k, 0.0)) for k in DEFAULT_WEIGHTS}
    if any(v < 0 for v in w.values()):
        raise ValueError("Bobot tidak boleh negatif")
    total = sum(w.values())
    if total <= 0:
        raise ValueError("Total bobot harus > 0")
    return {k: v / total for k, v in w.items()}


def _minmax(x: pd.Series) -> pd.Series:
    rng = x.max() - x.min()
    return pd.Series(0.5, index=x.index) if rng == 0 else (x - x.min()) / rng


def evaluate(cands: pd.DataFrame, demand: pd.DataFrame,
             radius_km: float = 5.0, weights: dict | None = None) -> pd.DataFrame:
    """Beri skor 0..1 untuk tiap lokasi kandidat dan urutkan dari terbaik."""
    if radius_km <= 0:
        raise ValueError("radius_km harus > 0")
    w = normalize_weights(weights)
    D = distance_matrix(cands, demand)
    orders = demand["weekly_orders"].to_numpy(dtype=float)
    total = orders.sum()

    out = cands.copy()
    out["coverage"] = ((D <= radius_km) * orders).sum(axis=1) / total
    out["avg_dist_km"] = (D * orders).sum(axis=1) / total
    out["score"] = (
        w["coverage"] * out["coverage"]
        + w["distance"] * (1 - _minmax(out["avg_dist_km"]))
        + w["price"] * (1 - _minmax(out["land_price_mio"]))
        + w["flood"] * (1 - out["flood_risk"])
        + w["access"] * out["road_access"]
    )
    out = out.sort_values("score", ascending=False).reset_index(drop=True)
    out["rank"] = out.index + 1
    return out


def greedy_hubs(cands: pd.DataFrame, demand: pd.DataFrame,
                k: int = 3, radius_km: float = 5.0) -> pd.DataFrame:
    """Pilih k hub dengan tambahan cakupan terbesar (greedy max-coverage)."""
    D = distance_matrix(cands, demand)
    orders = demand["weekly_orders"].to_numpy(dtype=float)
    covered = np.zeros(D.shape[1], dtype=bool)
    chosen, rows = [], []
    for step in range(1, min(k, len(cands)) + 1):
        gains = np.array([
            -1.0 if i in chosen else float(orders[(D[i] <= radius_km) & ~covered].sum())
            for i in range(len(cands))])
        best = int(gains.argmax())
        chosen.append(best)
        covered |= D[best] <= radius_km
        rows.append({"langkah": step, "id": int(cands.iloc[best]["id"]),
                     "name": cands.iloc[best]["name"],
                     "tambahan_order": gains[best],
                     "cakupan_kumulatif": orders[covered].sum() / orders.sum()})
    return pd.DataFrame(rows)
