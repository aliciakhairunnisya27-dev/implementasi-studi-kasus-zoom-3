# Pemilihan Lokasi Hub Logistik dengan GIS (Python + SQL + JavaScript)

Studi kasus dari materi **"Career and Competition in Industrial Era with GIS"**.
Proyek ini menunjukkan bagaimana mahasiswa Teknik Informatika dapat menjadi
*pengembang* GIS, bukan hanya pengguna aplikasi, memakai perangkat **open source**.

> Semua data di repositori ini **sintetis** (dibangkitkan acak) untuk pembelajaran.
> Hasilnya bukan rekomendasi bisnis nyata.

## Studi kasus

Sebuah perusahaan distribusi ingin membuka **satu atau beberapa hub** di kota
tujuan. Tersedia 12 lokasi kandidat dan 400 titik pelanggan dengan jumlah order
mingguan berbeda. Manajemen ingin tahu:

1. Lokasi mana yang paling strategis? (cakupan layanan, jarak, harga lahan, risiko banjir, akses jalan)
2. Jika membuka *k* hub, kombinasi mana yang menjangkau order terbanyak?
3. Bagaimana peringkat berubah jika prioritas manajemen berubah (misalnya risiko banjir lebih penting)?

## Kaitan dengan materi

| Materi | Implementasi di repo ini |
|---|---|
| Pengelolaan basis data (SQL) | `sitesel/data.py`: skema, `GROUP BY`, SQLite |
| Python | `sitesel/scoring.py`: jarak haversine, skor multikriteria, greedy max-coverage |
| JavaScript | `docs/index.html`: peta interaktif Leaflet |
| Integrasi sistem lewat API | `api.py`: endpoint Flask untuk menghitung peringkat dengan bobot kustom |
| Analisis dan visualisasi data | `output/ranking.csv`, peta web, GeoJSON |
| QGIS / perangkat open source | `output/*.geojson` bisa langsung dibuka di QGIS |
| Workflow + pemeriksaan hasil AI | `tests/`: tes otomatis untuk memverifikasi hasil kode |

## Struktur

```
gis-site-selection/
├── sitesel/          # modul inti (data, scoring, export)
├── tests/            # pytest
├── docs/index.html   # peta web (dibuat run.py, bisa di-host GitHub Pages)
├── output/           # ranking.csv + GeoJSON
├── run.py            # pipeline lengkap
├── api.py            # API Flask
└── requirements.txt
```

## Cara menjalankan

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run.py --radius 5 --k 3     # analisis + buat peta
pytest                             # jalankan tes
flask --app api run                # jalankan API
```

Contoh memanggil API:

```bash
curl "http://127.0.0.1:5000/api/sites?radius=4&flood=0.6&price=0.4"
```

Kriteria yang bisa diberi bobot: `coverage`, `distance`, `price`, `flood`, `access`.
Kriteria yang tidak dikirim dianggap berbobot 0, dan bobot dinormalisasi otomatis.

Buka `docs/index.html` di browser untuk melihat peta (butuh internet untuk
pustaka Leaflet dan tile OpenStreetMap). Untuk QGIS: *Layer → Add Layer → Add
Vector Layer*, lalu pilih `output/sites.geojson`.

## Metode singkat

- **Skor lokasi** = jumlah berbobot dari: cakupan order dalam radius, jarak rata-rata
  terbobot (min-max, dibalik), harga lahan (min-max, dibalik), `1 - risiko banjir`, dan akses jalan.
- **Hub terpilih** memakai algoritma *greedy maximum coverage*: tiap langkah memilih
  lokasi yang menambah cakupan order terbesar dari pelanggan yang belum terjangkau.
- Jarak memakai garis lurus (haversine), **bukan** jarak tempuh jalan.

## Keterbatasan dan pengembangan lanjut

- Ganti jarak garis lurus dengan waktu tempuh jaringan jalan (OSRM, OSMnx, pgRouting).
- Ganti SQLite dengan PostgreSQL + PostGIS agar query spasial dilakukan di database.
- Gunakan data nyata: titik pelanggan, peta risiko banjir, harga lahan.
- Bobot saat ini ditetapkan manual; pertimbangkan AHP atau sensitivity analysis.
- Greedy memberi hasil baik tetapi tidak dijamin optimal; bandingkan dengan solver (mis. OR-Tools).

## Mengunggah ke GitHub

```bash
git init
git add .
git commit -m "Studi kasus GIS: pemilihan lokasi hub"
git branch -M main
git remote add origin https://github.com/USERNAME/gis-site-selection.git
git push -u origin main
```

Untuk menampilkan peta online: **Settings → Pages → Deploy from a branch →
`main` / folder `/docs`**.

## Lisensi

MIT


## Publikasikan sebagai website GitHub Pages

1. Unggah seluruh isi folder `gis-site-selection` ke repository GitHub.
2. Buka **Settings → Pages**.
3. Pada **Build and deployment**, pilih **Deploy from a branch**.
4. Pilih branch `main` dan folder `/(root)`, lalu klik **Save**.
5. Tunggu beberapa menit. Website akan tersedia di alamat yang ditampilkan pada bagian Pages.

File `index.html` di root dibuat khusus agar GitHub Pages bisa langsung menampilkan peta interaktif.
Peta membutuhkan koneksi internet untuk memuat Leaflet dan peta dasar OpenStreetMap.

## Catatan menjalankan backend

GitHub Pages hanya meng-host file statis. Peta pada `index.html` bisa ditampilkan di GitHub Pages,
tetapi API Flask (`api.py`) dan pipeline Python (`run.py`) perlu dijalankan secara lokal atau
di-host pada layanan yang mendukung Python. Untuk menjalankannya di komputer, ikuti bagian
**Cara menjalankan** di atas.
