"""Ekspor hasil ke GeoJSON (bisa dibuka di QGIS) dan peta Leaflet (JavaScript)."""
import json
from pathlib import Path

import pandas as pd

HTML = """<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Peta Pemilihan Lokasi Hub</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">
<style>html,body,#map{height:100%;margin:0}
.leg{background:#fff;padding:8px 10px;border-radius:6px;font:13px/1.4 system-ui}</style>
</head><body><div id="map"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script>
const DATA = __DATA__;
const map = L.map('map');
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  {maxZoom: 19, attribution: '&copy; OpenStreetMap'}).addTo(map);
const bounds = [];
DATA.demand.features.forEach(f => {
  const [lon, lat] = f.geometry.coordinates;
  L.circleMarker([lat, lon], {radius: 2 + Math.sqrt(f.properties.weekly_orders) / 3,
    color: '#888', weight: 0, fillOpacity: .35}).addTo(map);
  bounds.push([lat, lon]);
});
DATA.sites.features.forEach(f => {
  const p = f.properties, [lon, lat] = f.geometry.coordinates;
  const col = p.is_selected ? '#d64545' : (p.rank <= 3 ? '#1f9d55' : '#2f6fed');
  L.circleMarker([lat, lon], {radius: 9, color: '#fff', weight: 2, fillColor: col, fillOpacity: .95})
    .bindPopup(`<b>${p.name}</b><br>Peringkat: ${p.rank}<br>Skor: ${p.score.toFixed(3)}<br>` +
      `Cakupan: ${(p.coverage * 100).toFixed(1)}%<br>Jarak rata-rata: ${p.avg_dist_km.toFixed(2)} km<br>` +
      `Harga lahan: Rp ${p.land_price_mio} jt/m2<br>Risiko banjir: ${p.flood_risk}` +
      (p.is_selected ? '<br><b>Terpilih (greedy)</b>' : '')).addTo(map);
  bounds.push([lat, lon]);
});
map.fitBounds(bounds, {padding: [30, 30]});
const leg = L.control({position: 'bottomleft'});
leg.onAdd = () => { const d = L.DomUtil.create('div', 'leg');
  d.innerHTML = 'Abu-abu: pelanggan (ukuran = order)<br>Hijau: 3 skor tertinggi<br>' +
    'Merah: hub terpilih (max-coverage)<br>Biru: kandidat lain'; return d; };
leg.addTo(map);
</script></body></html>
"""


def _fc(df: pd.DataFrame, props: list[str]) -> dict:
    feats = []
    for r in df.to_dict("records"):
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {k: (r[k].item() if hasattr(r[k], "item") else r[k]) for k in props},
        })
    return {"type": "FeatureCollection", "features": feats}


def build_geojson(ranked: pd.DataFrame, demand: pd.DataFrame, selected_ids: list[int]) -> dict:
    ranked = ranked.copy()
    ranked["is_selected"] = ranked["id"].isin(selected_ids)
    site_cols = ["id", "name", "rank", "score", "coverage", "avg_dist_km",
                 "land_price_mio", "flood_risk", "road_access", "is_selected"]
    return {"sites": _fc(ranked, site_cols),
            "demand": _fc(demand, ["id", "district", "weekly_orders"])}


def write_outputs(data: dict, out_dir: str | Path, html_path: str | Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "sites.geojson").write_text(json.dumps(data["sites"]), encoding="utf-8")
    (out_dir / "demand.geojson").write_text(json.dumps(data["demand"]), encoding="utf-8")
    Path(html_path).write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
