"""Assemble web/dist/index.html à partir de web/src/ideomes.src.html.

- remplace les emplacements __WORD__, __IDEO__, __FAV__ (logos et icône d'onglet en base64) et __BF__ (limites administratives) ;
- remplace __SUPABASE_URL__ et __SUPABASE_ANON_KEY__ (variables d'environnement du même nom) ;
- insère le SDK supabase-js (CDN) puis le shim local (window.claude.use -> Supabase) avant le script de l'appli.
Usage : SUPABASE_URL=... SUPABASE_ANON_KEY=... python web/build.py   (relancez après chaque modif de src/)
"""

from __future__ import annotations

import base64
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent
SRC, ASSETS, DIST = ICI / "src", ICI / "assets", ICI / "dist"
SUPABASE_JS_CDN = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"
SITE_URL = "https://hermes-bit.github.io/ideomes/"


def b64(nom: str) -> str:
    return base64.b64encode((ASSETS / nom).read_bytes()).decode()


def construire() -> Path:
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not supabase_url or not supabase_anon_key:
        print("Attention : SUPABASE_URL / SUPABASE_ANON_KEY absentes de l'environnement (page non fonctionnelle tant qu'elles ne sont pas définies).")

    html = (SRC / "ideomes.src.html").read_text(encoding="utf-8")
    html = (
        html.replace("__WORD__", b64("geomessen-wordmark.png"))
        .replace("__IDEO__", b64("ideomes-logo.png"))
        .replace("__FAV__", b64("ideomes-favicon.png"))
        .replace("__BF__", (ASSETS / "bf-limites.json").read_text(encoding="utf-8").strip())
        # Horodatage de compilation affiché en pied de page : permet de vérifier
        # d'un coup d'oeil si le navigateur sert bien la dernière version déployée.
        .replace("__BUILD__", "1.3 (" + datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC") + ")")
    )
    shim_src = (
        (SRC / "claude-shim.js")
        .read_text(encoding="utf-8")
        .replace("__SUPABASE_URL__", supabase_url)
        .replace("__SUPABASE_ANON_KEY__", supabase_anon_key)
    )
    shim = f'<script src="{SUPABASE_JS_CDN}"></script>\n<script>\n{shim_src}\n</script>\n'
    i = html.index("<script>")
    html = html[:i] + shim + html[i:]
    if not html.lstrip().lower().startswith("<!doctype"):
        og_image = SITE_URL + "ideomes-logo.png"
        og_desc = "Partagez les besoins et les idées qui amélioreraient votre quotidien au Burkina Faso."
        html = (
            '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'<meta property="og:type" content="website">\n'
            f'<meta property="og:site_name" content="Idéomès">\n'
            f'<meta property="og:title" content="Idéomès">\n'
            f'<meta property="og:description" content="{og_desc}">\n'
            f'<meta property="og:image" content="{og_image}">\n'
            f'<meta property="og:url" content="{SITE_URL}">\n'
            f'<meta name="twitter:card" content="summary">\n'
            f'<meta name="twitter:title" content="Idéomès">\n'
            f'<meta name="twitter:description" content="{og_desc}">\n'
            f'<meta name="twitter:image" content="{og_image}">\n'
            + html
            + "\n</html>\n"
        )
    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    out.write_text(html, encoding="utf-8")
    shutil.copyfile(ASSETS / "ideomes-logo.png", DIST / "ideomes-logo.png")
    return out


if __name__ == "__main__":
    p = construire()
    print(f"OK : {p} ({p.stat().st_size // 1024} Ko)")
