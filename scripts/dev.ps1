# Windows (PowerShell) : .\scripts\dev.ps1 install | api | seed | test | demo
param([string]$cible = "api")
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"
switch ($cible) {
  "install" {
    python -m venv .venv
    & $py -m pip install -r requirements.txt
    & $py -m pip install -e agents
    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
  }
  "api"   { & $py web\build.py; Push-Location api; & ..\$py -m uvicorn app.main:app --reload --port 8000; Pop-Location }
  "seed"  { & $py scripts\seed.py }
  "demo"  { & $py -m ideomes_agents.cli demo }
  "test"  { Push-Location agents; & ..\$py -m pytest -q; Pop-Location; Push-Location api; & ..\$py -m pytest -q; Pop-Location }
  default { Write-Host "Cibles : install, api, seed, demo, test" }
}
