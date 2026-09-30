"""Remplit une base Supabase neuve : vidéo de contexte + 5 actualités « À la une » vérifiées.

Usage :
    SUPABASE_URL=https://xxxx.supabase.co SUPABASE_SERVICE_ROLE_KEY=... python scripts/seed_supabase.py

La clé service_role contourne le Row Level Security (RLS) : elle sert uniquement à ce script,
exécuté une fois depuis votre poste. Ne la mettez jamais dans web/, build.py ou un fichier commité —
seule SUPABASE_ANON_KEY (publique par conception) va dans le build du site.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

RACINE = Path(__file__).resolve().parents[1]
BUCKET = "ideomes-public"


def _check(r: httpx.Response) -> None:
    if r.is_error:
        sys.exit(f"Échec {r.status_code} sur {r.request.url} :\n{r.text}")


def main() -> None:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        sys.exit("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY sont requis (variables d'environnement).")
    if key.startswith("sb_publishable_"):
        sys.exit(
            "Ceci est la clé publishable (anon), pas la clé secret. "
            "Dans Supabase : Project Settings -> API, clé 'secret' (sb_secret_...), "
            "cliquez sur « Reveal » pour l'afficher."
        )

    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    with httpx.Client(base_url=url, headers=headers, timeout=120) as h:
        # 1. Vidéo de contexte + affiche -> Supabase Storage
        video = RACINE / "web" / "assets" / "ideomes-contexte.mp4"
        poster = RACINE / "web" / "assets" / "ideomes-contexte-poster.jpg"
        video_path, poster_path = "video/contexte.mp4", "video/poster.jpg"
        _check(h.post(
            f"/storage/v1/object/{BUCKET}/{video_path}",
            headers={"Content-Type": "video/mp4", "x-upsert": "true"},
            content=video.read_bytes(),
        ))
        _check(h.post(
            f"/storage/v1/object/{BUCKET}/{poster_path}",
            headers={"Content-Type": "image/jpeg", "x-upsert": "true"},
            content=poster.read_bytes(),
        ))

        # 2. config/video
        _check(h.post(
            "/rest/v1/documents",
            headers={"Prefer": "resolution=merge-duplicates"},
            json={"collection": "config", "doc_id": "video", "data": {"assetId": video_path, "posterId": poster_path, "lien": ""}},
        ))

        # 3. actus/<id> depuis scripts/seed/actus.json
        actus = json.loads((RACINE / "scripts" / "seed" / "actus.json").read_text(encoding="utf-8"))
        for doc_id, data in actus.items():
            _check(h.post(
                "/rest/v1/documents",
                headers={"Prefer": "resolution=merge-duplicates"},
                json={"collection": "actus", "doc_id": doc_id, "data": data},
            ))

    print(f"OK : vidéo + affiche téléversées, {len(actus)} actualités écrites.")


if __name__ == "__main__":
    main()
