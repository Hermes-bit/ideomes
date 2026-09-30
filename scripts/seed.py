"""Remplit une base neuve : vidéo de contexte, 5 actualités « À la une » vérifiées, configuration Hermès.
Usage (API lancée) : python scripts/seed.py [--api http://localhost:8000]"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import httpx

RACINE = Path(__file__).resolve().parents[1]
PROPRIO = {"X-Dev-User": "owner"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:8000")
    a = p.parse_args()
    with httpx.Client(base_url=a.api, headers=PROPRIO, timeout=120) as h:
        video = RACINE / "web" / "assets" / "ideomes-contexte.mp4"
        poster = RACINE / "web" / "assets" / "ideomes-contexte-poster.jpg"
        v = h.post("/api/assets", files={"fichier": (video.name, video.read_bytes(), "video/mp4")}).json()
        pa = h.post("/api/assets", files={"fichier": (poster.name, poster.read_bytes(), "image/jpeg")}).json()
        h.put("/api/db/doc/config/video", json={"data": {"assetId": v["id"], "posterId": pa["id"], "lien": ""}})
        actus = json.loads((RACINE / "scripts" / "seed" / "actus.json").read_text(encoding="utf-8"))
        for doc_id, data in actus.items():
            h.put(f"/api/db/doc/actus/{doc_id}", json={"data": data})
        h.put(
            "/api/db/doc/config/hermes",
            json={"data": {"actif": True, "heure": "06:52", "fuseau": "Africa/Ouagadougou"}},
        )
    print(f"OK : vidéo {v['id']}, {len(actus)} actualités.")


if __name__ == "__main__":
    main()
