# Self-test runner for todaybgm.
# Starts a local HTTP server on an isolated port (so it never touches the
# localhost:8000 dev origin's localStorage), opens tests/ in headless Edge
# with a throwaway profile, and reads the result the test page reports
# back via a fetch to /__RESULT__/... (visible in the server access log).
#
# Usage: powershell -ExecutionPolicy Bypass -File tests\run.ps1
# Exit codes: 0 = all pass, 1 = test failures, 2 = runner error

param(
  [int]$Port = 8765,
  [int]$TimeoutSec = 90,
  [string]$BrowserPath = ""   # optional: run in a specific Chromium browser (e.g. chrome.exe)
)

$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $env:TEMP "todaybgm-selftest-server.log"
$profileDir = Join-Path $env:TEMP "todaybgm-selftest-profile"
$testUrl = "http://127.0.0.1:$Port/tests/"

if (-not $BrowserPath) {
  $BrowserPath = @(
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
  ) | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $BrowserPath -or -not (Test-Path $BrowserPath)) { Write-Output "ERROR: no Chromium browser found (use -BrowserPath)"; exit 2 }
Write-Output "BROWSER: $BrowserPath"

if (Test-Path $log) { Remove-Item $log -Force }
if (Test-Path $profileDir) { try { Remove-Item $profileDir -Recurse -Force -ErrorAction Stop } catch {} }

$serverArgs = @("-m", "http.server", "$Port", "--bind", "127.0.0.1")
$server = Start-Process -FilePath "python" -ArgumentList $serverArgs -WorkingDirectory $root `
  -RedirectStandardError $log -WindowStyle Hidden -PassThru

$browser = $null
try {
  $up = $false
  foreach ($i in 1..20) {
    Start-Sleep -Milliseconds 250
    if ($server.HasExited) { break }
    try {
      $r = Invoke-WebRequest -Uri $testUrl -UseBasicParsing -TimeoutSec 2
      if ($r.StatusCode -eq 200) { $up = $true; break }
    } catch {}
  }
  if (-not $up) {
    Write-Output "ERROR: local server did not start on port $Port (port in use?)"
    if (Test-Path $log) { Get-Content $log -TotalCount 5 }
    exit 2
  }

  $browserArgs = @("--headless=new", "--disable-gpu", "--user-data-dir=$profileDir", "--no-first-run", $testUrl)
  $browser = Start-Process -FilePath $BrowserPath -ArgumentList $browserArgs -PassThru

  # The test page reports its verdict by fetching /__RESULT__/<encoded summary>;
  # that request line lands in the http.server access log. Poll for it.
  $result = $null
  $deadline = (Get-Date).AddSeconds($TimeoutSec)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
    if (Test-Path $log) {
      $hit = Select-String -Path $log -Pattern 'GET /__RESULT__/([^ ]+)' | Select-Object -Last 1
      if ($hit) { $result = $hit.Matches[0].Groups[1].Value; break }
    }
  }

  if (-not $result) {
    Write-Output "ERROR: no result within $TimeoutSec sec (open $testUrl manually to debug)"
    exit 2
  }
  $decoded = [System.Uri]::UnescapeDataString($result)
  Write-Output "RESULT: $decoded"
  if ($decoded -like "ALLPASS-*") {
    Write-Output "ALL TESTS PASSED"
    exit 0
  }
  Write-Output "TESTS FAILED (open $testUrl in a browser for details)"
  exit 1
} finally {
  if ($browser -and -not $browser.HasExited) { & taskkill /PID $browser.Id /T /F | Out-Null }
  if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue }
}
