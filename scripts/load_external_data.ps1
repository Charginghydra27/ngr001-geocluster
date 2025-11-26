# Load external weather databases (NOAA and US Weather Events)
# This supplements the existing manual data without replacing it.

# Optional: Pass a limit as first argument to load only N records per database (for testing)
# Example: .\load_external_data.ps1 10000

param(
    [int]$Limit = 0
)

$limitArg = ""
if ($Limit -gt 0) {
    $limitArg = "$Limit"
    Write-Host "Loading with limit of $Limit records per database"
}

if ($limitArg) {
    docker exec -i ngr001_api python -m app.load_external_data $limitArg
} else {
    docker exec -i ngr001_api python -m app.load_external_data
}
