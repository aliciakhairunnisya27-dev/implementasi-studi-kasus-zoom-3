"""Pipeline lengkap: data -> SQL -> analisis -> GeoJSON + peta web.

Contoh:  python run.py --radius 5 --k 3
"""
import argparse
from pathlib import Path

from sitesel import data, export, scoring

ROOT = Path(__file__).parent


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--radius", type=float, default=5.0, help="radius layanan (km)")
    ap.add_argument("--k", type=int, default=3, help="jumlah hub yang dipilih")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--candidates", type=int, default=12)
    a = ap.parse_args()

    db = ROOT / "data" / "sitesel.db"
    data.init_db(db, seed=a.seed, n_candidates=a.candidates)
    cands, demand = data.load(db)

    print("== Ringkasan permintaan per kecamatan (SQL) ==")
    print(data.district_summary(db).to_string(index=False))

    ranked = scoring.evaluate(cands, demand, radius_km=a.radius)
    hubs = scoring.greedy_hubs(cands, demand, k=a.k, radius_km=a.radius)

    print(f"\n== Peringkat lokasi (radius {a.radius} km) ==")
    cols = ["rank", "name", "score", "coverage", "avg_dist_km",
            "land_price_mio", "flood_risk", "road_access"]
    print(ranked[cols].round(3).to_string(index=False))
    print(f"\n== {a.k} hub dengan cakupan gabungan terbaik ==")
    print(hubs.round(3).to_string(index=False))

    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    ranked[cols].round(4).to_csv(out / "ranking.csv", index=False)
    geo = export.build_geojson(ranked, demand, hubs["id"].tolist())
    export.write_outputs(geo, out, ROOT / "docs" / "index.html")
    print("\nTersimpan: output/ranking.csv, output/sites.geojson, output/demand.geojson, docs/index.html")


if __name__ == "__main__":
    main()
