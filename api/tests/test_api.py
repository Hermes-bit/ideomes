import time

import pytest
from app.main import app
from fastapi.testclient import TestClient

PROPRIO = {"X-Dev-User": "owner"}
AWA = {"X-Dev-User": "u_awa"}


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client:
        yield client


def test_regles_acces(c):
    assert c.put("/api/db/doc/actus/a1", json={"data": {"titre": "x"}}, headers=PROPRIO).status_code == 200
    assert c.get("/api/db/collection/actus", headers=AWA).status_code == 200
    assert c.put("/api/db/doc/actus/a2", json={"data": {}}, headers=AWA).status_code == 403
    assert c.get("/api/db/collection/reponses", headers=AWA).status_code == 403
    assert c.get("/api/db/doc/adminconf/credentials", headers=AWA).status_code == 403
    assert c.put("/api/db/doc/reponses/u_autre", json={"data": {}}, headers=AWA).status_code == 403
    assert c.get("/api/me", headers=AWA).json()["isOwner"] is False
    assert c.get("/api/me", headers=PROPRIO).json()["isOwner"] is True


def test_idee_declenche_zeus(c):
    item = {
        "id": "idee1",
        "domaine": "Eau",
        "probleme": "Pas de forage au quartier, les femmes marchent loin pour l'eau.",
        "ville": "Ouagadougou",
        "consentement": {"rgpd": True},
        "identite": {"type": "whatsapp"},
    }
    assert c.put("/api/db/doc/reponses/u_awa", json={"data": {"items": [item]}}, headers=AWA).status_code == 200
    for _ in range(80):
        d = c.get("/api/dossiers/idee1", headers=PROPRIO).json()
        if d["statut"] != "recu":
            break
        time.sleep(0.1)
    assert d["en_attente_de"] == ["comite"], d
    assert c.get("/api/dossiers/idee1", headers=AWA).status_code == 403
    r = c.post("/api/dossiers/idee1/decision", json={"point": "comite", "decision": "valide"}, headers=PROPRIO)
    assert r.status_code == 200 and r.json()["statut"] == "en_projet"
    notifs = c.get("/api/db/collection/notifications", headers=PROPRIO).json()["docs"]
    assert any(n["data"]["evenement"] == "decision_valide" for n in notifs)
    assert c.get("/api/synthese", headers=PROPRIO).status_code == 200


def test_assets(c):
    r = c.post("/api/assets", files={"fichier": ("a.png", b"\x89PNG\r\n", "image/png")}, headers=PROPRIO)
    aid = r.json()["id"]
    assert c.get(f"/_blob/{aid}").status_code == 200
    assert c.post("/api/assets", files={"fichier": ("a.png", b"x", "image/png")}, headers=AWA).status_code == 403
    assert c.delete(f"/api/assets/{aid}", headers=PROPRIO).json()["deleted"]
