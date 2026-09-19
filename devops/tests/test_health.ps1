# Brings the stack up, checks every module's /health, tears it down.
Set-Location (Join-Path $PSScriptRoot "..\..")

Write-Host "==> Building and starting all services..."
docker compose up -d

Write-Host "==> Waiting for services to become healthy..."
Start-Sleep -Seconds 5

$fail = $false
$ports = 8001,8002,8003,8004,8005
foreach ($port in $ports) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$port/health" -UseBasicParsing -TimeoutSec 3
        if ($resp.StatusCode -eq 200) {
            Write-Host "OK   : port $port healthy"
        } else {
            Write-Host "FAIL : port $port returned $($resp.StatusCode)"
            $fail = $true
        }
    } catch {
        Write-Host "FAIL : port $port not responding"
        $fail = $true
    }
}

Write-Host "==> Tearing down..."
docker compose down

if ($fail) {
    Write-Host "Integration test FAILED"
    exit 1
} else {
    Write-Host "Integration test PASSED"
}
