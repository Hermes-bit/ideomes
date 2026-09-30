import os
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(RACINE / "api"), str(RACINE / "agents")]
_tmp = tempfile.mkdtemp()
os.environ.update(LLM_MODE="simule", DATABASE_URL=f"sqlite:///{_tmp}/test.db", DOSSIER_BLOBS=f"{_tmp}/blobs")
