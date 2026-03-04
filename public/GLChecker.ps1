# FUChecker.ps1
param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Student
)

$ErrorActionPreference = "Stop"

$server = "http://10.0.24.149:8081/submit-all"

# Hardcoded tester flag to be sent to the server
# (Your backend's choose_project_and_args will map this to the tester)
$argsStr = "-FUL"

# Collect .java files in current directory (non-recursive)
$javaFiles = Get-ChildItem -File -Filter "*.java" | Sort-Object Name

if (-not $javaFiles -or $javaFiles.Count -eq 0) {
  throw "No .java files found in: $(Get-Location)"
}

# Build curl.exe -F arguments for all java files
$fileFormArgs = @()
foreach ($f in $javaFiles) {
  $fileFormArgs += @("-F", "files=@$($f.Name)")
}

# Submit (always includes args=-FUL)
curl.exe `
  -F "student=$Student" `
  -F "args=$argsStr" `
  @fileFormArgs `
  $server