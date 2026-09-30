"""Assemble web/dist/index.html à partir de web/src/ideomes.src.html.

- remplace les emplacements __WORD__, __IDEO__, __FAV__ (logos et icône d'onglet en base64) et __BF__ (limites administratives) ;
- insère le shim local (window.claude.use -> API FastAPI) avant le script de l'appli.
Usage : python web/build.py   (relancez-le après chaque modification de src/)
"""

from __future__ import annotations

import base64
from pathlib import Path

ICI = Path(__file__).resolve().parent
SRC, ASSETS, DIST = ICI / "src", ICI / "assets", ICI / "dist"


def b64(nom: str) -> str:
    return base64.b64encode((ASSETS / nom).read_bytes()).decode()


def construire() -> Path:
    html = (SRC / "ideomes.src.html").read_text(encoding="utf-8")
    html = (
        html.replace("__WORD__", b64("geomessen-wordmark.png"))
        .replace("__IDEO__", b64("ideomes-logo.png"))
        .replace("__FAV__", b64("ideomes-favicon.png"))
        .replace("__BF__", (ASSETS / "bf-limites.json").read_text(encoding="utf-8").strip())
    )
    shim = "<script>\n" + (SRC / "claude-shim.js").read_text(encoding="utf-8") + "\n</script>\n"
    i = html.index("<script>")
    html = html[:i] + shim + html[i:]
    if not html.lstrip().lower().startswith("<!doctype"):
        html = (
            '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + html
            + "\n</html>\n"
        )
    DIST.mkdir(exist_ok=True)
    out = DIST / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    p = construire()
    print(f"OK : {p} ({p.stat().st_size // 1024} Ko)")
