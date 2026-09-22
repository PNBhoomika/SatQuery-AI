# test_contract.ps1
# Verifies the ACTUAL data contract between modules, not just that they start.
# This checks: module-a output shape -> module-b input, module-a output -> module-c input.
#
# NOTE: This is a stub. Each check below currently only verifies the module
# is reachable and returns *something*. As each teammate's real endpoint
# lands, replace the marked TODO block for that module with a real call
# and a real shape assertion.
#
# Usage: .\tests\integration\test_contract.ps1

Set-Location (Join-Path $PSScriptRoot "..\..")

Write-Host "==> Building and starting all services..."
docker compose up -d
Write-Host "==> Waiting for services to become healthy..."
Start-Sleep -Seconds 5

$fail = $false

function Check-Endpoint {
    param($name, $url, $method = "GET", $body = $null)
    try {
        if ($body) {
            $resp = Invoke-WebRequest -Uri $url -Method $method -Body $body -ContentType "application/json" -UseBasicParsing -TimeoutSec 5
        } else {
            $resp = Invoke-WebRequest -Uri $url -Method $method -UseBasicParsing -TimeoutSec 5
        }
        return $resp
    } catch {
        Write-Host "FAIL : $name -> $url  ($($_.Exception.Message))"
        $script:fail = $true
        return $null
    }
}

# ---------- Link 1: module-a (ingestion) is reachable ----------
Write-Host ""
Write-Host "-- Link 1: module-a (ingestion) --"
$aResp = Check-Endpoint "module-a health" "http://localhost:8001/health"
if ($aResp) {
    Write-Host "OK   : module-a reachable"
    # TODO (Member 1 lands real code): call the real tile-output endpoint here, e.g.
    #   $tile = Check-Endpoint "module-a tile output" "http://localhost:8001/tiles/latest"
    # Then assert $tile.Content has the COG path + metadata JSON keys expected
    # by module-b/module-c (e.g. "cog_path", "bbox", "timestamp", "qa_mask_path").
}

# ---------- Link 2: module-a output -> module-b embed() ----------
Write-Host ""
Write-Host "-- Link 2: module-a tile -> module-b embed() --"
$bResp = Check-Endpoint "module-b health" "http://localhost:8002/health"
if ($bResp) {
    Write-Host "OK   : module-b reachable"
    # TODO (Member 2 lands real code): once module-a returns a real tile reference,
    # POST it to module-b's embed endpoint and check the response contains an
    # embedding vector of the expected dimensionality, e.g.
    #   $embedBody = '{"tile_path": "<from module-a>"}'
    #   $embedResp = Check-Endpoint "module-b embed" "http://localhost:8002/embed" "POST" $embedBody
    #   assert ($embedResp.Content | ConvertFrom-Json).embedding.Length -eq <expected_dim>
}

# ---------- Link 3: module-a output -> module-c detect_change() ----------
Write-Host ""
Write-Host "-- Link 3: module-a tiles (t1, t2) -> module-c detect_change() --"
$cResp = Check-Endpoint "module-c health" "http://localhost:8003/health"
if ($cResp) {
    Write-Host "OK   : module-c reachable"
    # TODO (Member 3 lands real code): send two tile references (before/after) and
    # check the response contains a change_mask and confidence score, e.g.
    #   $changeBody = '{"tile_t1": "<path>", "tile_t2": "<path>"}'
    #   $changeResp = Check-Endpoint "module-c detect_change" "http://localhost:8003/detect_change" "POST" $changeBody
    #   assert ($changeResp.Content | ConvertFrom-Json).confidence -ne $null
}

# ---------- Link 4: module-d orchestrates a-b-c and talks to postgres ----------
Write-Host ""
Write-Host "-- Link 4: module-d (backend) orchestration + Postgres --"
$dResp = Check-Endpoint "module-d health" "http://localhost:8004/health"
if ($dResp) {
    Write-Host "OK   : module-d reachable"
    # TODO (Member 4 lands real code): hit module-d's real orchestration endpoint
    # (e.g. POST /process-tile) and confirm it internally calls module-a/b/c and
    # writes a row into PostGIS. Simplest first check: confirm module-d can reach
    # postgres at all, e.g. by exposing a /db-health endpoint on module-d that
    # does SELECT 1 against the DATABASE_URL, then:
    #   $dbResp = Check-Endpoint "module-d db-health" "http://localhost:8004/db-health"
}

# ---------- Link 5: module-e only talks to module-d, never to a/b/c directly ----------
Write-Host ""
Write-Host "-- Link 5: module-e (frontend) --"
$eResp = Check-Endpoint "module-e health" "http://localhost:8005/health"
if ($eResp) {
    Write-Host "OK   : module-e reachable"
    # No direct contract test needed here beyond reachability -- module-e's
    # correctness is validated by hitting module-d's API, which is already
    # covered by Link 4. This check just confirms the frontend container itself
    # is up and serving.
}

Write-Host ""
Write-Host "==> Tearing down..."
docker compose down

if ($fail) {
    Write-Host ""
    Write-Host "Contract test FAILED (one or more modules unreachable)"
    exit 1
} else {
    Write-Host ""
    Write-Host "Contract test PASSED (reachability only -- fill in TODOs as real endpoints land)"
}
