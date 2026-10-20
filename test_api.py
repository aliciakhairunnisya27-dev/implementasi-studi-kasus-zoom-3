from api import create_app
from sitesel import data


def client(tmp_path):
    db = tmp_path / "t.db"
    data.init_db(db)
    return create_app(db).test_client()


def test_health(tmp_path):
    r = client(tmp_path).get("/api/health")
    assert r.status_code == 200 and r.json["status"] == "ok"


def test_sites_custom_weights(tmp_path):
    r = client(tmp_path).get("/api/sites?radius=4&flood=1")
    assert r.status_code == 200
    assert r.json["sites"][0]["rank"] == 1


def test_sites_bad_input(tmp_path):
    c = client(tmp_path)
    assert c.get("/api/sites?radius=-1").status_code == 400
    assert c.get("/api/sites?radius=abc").status_code == 400
