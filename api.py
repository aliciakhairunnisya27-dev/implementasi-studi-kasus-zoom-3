"""API kecil (integrasi sistem): kirim bobot, terima peringkat lokasi.

Jalankan:  flask --app api run
Contoh  :  curl "http://127.0.0.1:5000/api/sites?radius=4&flood=0.4&price=0.1"
"""
from pathlib import Path

from flask import Flask, jsonify, request

from sitesel import data, scoring

DB = Path(__file__).parent / "data" / "sitesel.db"


def create_app(db_path=DB) -> Flask:
    app = Flask(__name__)
    if not Path(db_path).exists():
        data.init_db(db_path)
    cands, demand = data.load(db_path)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", candidates=len(cands), demand_points=len(demand))

    @app.get("/api/sites")
    def sites():
        try:
            radius = float(request.args.get("radius", 5.0))
            weights = {k: float(request.args[k]) for k in scoring.DEFAULT_WEIGHTS
                       if k in request.args} or None
            if weights:  # kriteria yang tidak dikirim dianggap bobot 0
                weights = {k: weights.get(k, 0.0) for k in scoring.DEFAULT_WEIGHTS}
            ranked = scoring.evaluate(cands, demand, radius_km=radius, weights=weights)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        cols = ["rank", "name", "lat", "lon", "score", "coverage", "avg_dist_km"]
        return jsonify(radius_km=radius, sites=ranked[cols].round(4).to_dict("records"))

    return app


app = create_app()
