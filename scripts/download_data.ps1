# scripts\download_data.ps1
param(
  [switch]$LoadAfter = $false,
  [int]$Limit = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Paths ---
$repoRoot = Split-Path -Parent $PSCommandPath        # ...\scripts
$repoRoot = Split-Path -Parent $repoRoot             # project root
$dataDir  = Join-Path $repoRoot 'data'
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir | Out-Null }

# --- Helpers ---
function Ensure-KaggleCli {
  try { & kaggle --version | Out-Null; return } catch { }
  Write-Host "Installing Kaggle CLI (user scope)..." -ForegroundColor Yellow
  & python -m pip install --user kaggle
}

function Ensure-KaggleCreds {
  $credDir = Join-Path $env:USERPROFILE '.kaggle'
  $credFile = Join-Path $credDir 'kaggle.json'
  if (Test-Path $credFile) { return }
  Write-Host "`nKaggle credentials not found. Enter values from Kaggle > Account > Create New API Token." -ForegroundColor Yellow
  $u = Read-Host 'Kaggle username'
  $k = Read-Host 'Kaggle API key (stored locally)'
  if ([string]::IsNullOrWhiteSpace($u) -or [string]::IsNullOrWhiteSpace($k)) { throw "Username and key are required." }
  if (-not (Test-Path $credDir)) { New-Item -ItemType Directory -Path $credDir | Out-Null }
  @{ username = $u; key = $k } | ConvertTo-Json | Set-Content -Path $credFile -Encoding UTF8
  try {
    icacls $credDir  /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)(M)" | Out-Null
    icacls $credFile /inheritance:r /grant:r "$($env:USERNAME):(R)"       | Out-Null
    attrib +h $credFile
  } catch { }
}

function Test-IsZipMagic {
  param([Parameter(Mandatory)][string]$Path)
  if (-not (Test-Path $Path)) { return $false }
  $fs = [System.IO.File]::OpenRead($Path)
  try {
    $buf = New-Object byte[] 2
    $null = $fs.Read($buf,0,2)
    return ($buf[0] -eq 0x50 -and $buf[1] -eq 0x4B)  # 'P''K'
  } finally { $fs.Dispose() }
}

function Get-KaggleCsv {
  param(
    [Parameter(Mandatory)][string]$Dataset,       # e.g. 'sobhanmoosavi/us-accidents'
    [Parameter(Mandatory)][string[]]$Candidates,  # file paths inside the dataset
    [Parameter(Mandatory)][string]$OutName        # final CSV name we want in /data
  )

  $dest = Join-Path $dataDir $OutName
  if (Test-Path $dest) {
    Write-Host ("Already present: {0} - skipping download" -f (Split-Path $dest -Leaf)) -ForegroundColor DarkGray
    return $true
  }

  $tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP ("kaggle_dl_" + [guid]::NewGuid().ToString("N"))) -Force
  try {
    foreach ($f in $Candidates) {
      Write-Host ("Downloading {0} -> {1} ..." -f $Dataset, $f) -ForegroundColor Cyan
      & kaggle datasets download -d $Dataset -f $f -p $tmp.FullName -q --force

      # Pick the newest file Kaggle put there
      $dl = Get-ChildItem -Path $tmp.FullName -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
      if (-not $dl) { continue }

      # If the file is actually a ZIP (even if named .csv), expand it
      if (Test-IsZipMagic -Path $dl.FullName) {
        $zipPath = Join-Path $tmp.FullName 'payload.zip'
        Copy-Item $dl.FullName $zipPath -Force
        $unz = Join-Path $tmp.FullName 'unzipped'
        if (Test-Path $unz) { Remove-Item $unz -Recurse -Force -ErrorAction SilentlyContinue }
        Expand-Archive -LiteralPath $zipPath -DestinationPath $unz -Force

        # prefer exact leaf name, fallback to any CSV in the archive
        $leaf = Split-Path $f -Leaf
        $csv = Get-ChildItem -Path $unz -Recurse -ErrorAction SilentlyContinue -Filter $leaf | Select-Object -First 1
        if (-not $csv) { $csv = Get-ChildItem -Path $unz -Recurse -Filter *.csv | Select-Object -First 1 }
        if ($csv) { Copy-Item $csv.FullName $dest -Force; return $true }
      } else {
        # Not a zip – copy directly
        Copy-Item $dl.FullName $dest -Force
        return $true
      }
    }

    Write-Warning ("No file from {0} matched expected names: {1}" -f $Dataset, ($Candidates -join ', '))
    return $false
  }
  finally {
    Remove-Item $tmp.FullName -Recurse -Force -ErrorAction SilentlyContinue
  }
}

# --- Run ---
Write-Host "== ngr001-geocluster data downloader ==" -ForegroundColor Green
Write-Host ("Data folder: {0}" -f $dataDir)
Ensure-KaggleCli
Ensure-KaggleCreds

$ok = $true
$ok = $ok -and (Get-KaggleCsv -Dataset 'noaa/severe-weather-data-inventory' -Candidates @('hail-2015.csv','hail/hail-2015.csv') -OutName 'hail-2015.csv')
$ok = $ok -and (Get-KaggleCsv -Dataset 'sobhanmoosavi/us-weather-events'      -Candidates @('WeatherEvents_Jan2016-Dec2022.csv') -OutName 'WeatherEvents_Jan2016-Dec2022.csv')
$ok = $ok -and (Get-KaggleCsv -Dataset 'sobhanmoosavi/us-accidents'           -Candidates @('US_Accidents_March23.csv','US_Accidents_March23.csv.zip') -OutName 'US_Accidents_March23.csv')

Write-Host ""
Write-Host ("Downloaded files in {0}:" -f ${dataDir}) -ForegroundColor Green
Get-ChildItem -Path $dataDir -Filter *.csv -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize

if (-not $ok) { Write-Warning "One or more files failed to download. See messages above." }

if ($LoadAfter) {
  $loader = Join-Path (Join-Path $repoRoot 'scripts') 'load_external_data.ps1'
  if (Test-Path $loader) {
    Write-Host ("Running loader: {0}" -f $loader) -ForegroundColor Yellow
    if ($Limit -gt 0) { & $loader $Limit } else { & $loader }
  } else {
    Write-Warning ("Loader script not found at {0} (skipping load step)" -f $loader)
  }
}

Write-Host "Done."
