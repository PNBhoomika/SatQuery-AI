# Demo Environment Guide

## Prerequisites
- Docker Desktop installed and running
- Weights staged under weights\<module>\ with weights\checksums.sha256 present

## Bring the system up
```powershell
docker compose up -d --build
```

## Verify all modules are healthy
```powershell
.\tests\integration\test_health.ps1
```

## Verify data contracts between modules
```powershell
.\tests\integration\test_contract.ps1
```
Checks that module-a's tile output actually matches what module-b/c expect as
input, not just that containers start. Fill in the TODO blocks in this script
as each teammate's real endpoint lands.

## Verify weight integrity before the demo
```powershell
.\scripts\verify_checksums.ps1
```

## Build the index (reproducibility)
```powershell
.\scripts\build_index.ps1 -DataDir <data_dir> -OutDir <output_dir>
python scripts\scale_report.py <output_dir>
```

## Air-gapped packaging
Validated end-to-end on 19-09-2026 — bundle size: 276 MB (5 modules + Postgres/PostGIS).
Re-check this size once real model weights (CLIP, change-detection) are baked in.

```powershell
docker compose build
docker save -o bundle.tar (docker compose config --images)
```
Transfer `bundle.tar` to the offline machine (USB drive or LAN copy — 276 MB is quick either way).

On the offline machine:
```powershell
docker load -i bundle.tar
docker compose up -d
docker compose ps
```
All 6 services (module-a through module-e, postgres) should show `Up (healthy)` with zero network access required.

## Tear down
```powershell
docker compose down
```

## Known ports
| Service   | Port |
|-----------|------|
| module-a  | 8001 |
| module-b  | 8002 |
| module-c  | 8003 |
| module-d  | 8004 |
| module-e  | 8005 |
| postgres  | 5432 |