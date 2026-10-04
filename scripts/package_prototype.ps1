$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stage = Join-Path $projectRoot "work\package-build-$timestamp"
$output = Join-Path $projectRoot "outputs\SignBridge-UAE-prototype.zip"

New-Item -ItemType Directory -Path $stage -Force | Out-Null

$topFiles = @(
    ".gitignore",
    "app.py",
    "README.md",
    "requirements.txt",
    "run_tests.bat",
    "setup.ps1",
    "start_signbridge.bat",
    "THIRD_PARTY_NOTICES.md"
)

foreach ($file in $topFiles) {
    Copy-Item -LiteralPath (Join-Path $projectRoot $file) -Destination $stage
}

$outputDocs = @("BUILD_STATUS.md", "QUICK_START.md", "WHEN_YOU_RETURN.md")
$stagedOutputs = Join-Path $stage "outputs"
New-Item -ItemType Directory -Path $stagedOutputs -Force | Out-Null
foreach ($file in $outputDocs) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "outputs\$file") -Destination $stagedOutputs
}

$sourceDirectories = @("assets", "config", "docs", "scripts", "signbridge", "tests")
foreach ($directory in $sourceDirectories) {
    $source = Join-Path $projectRoot $directory
    $destinationRoot = Join-Path $stage $directory
    Get-ChildItem -LiteralPath $source -Recurse -File |
        Where-Object {
            $_.FullName -notmatch "\\__pycache__\\" -and $_.Extension -ne ".pyc"
        } |
        ForEach-Object {
            $relative = $_.FullName.Substring($source.Length).TrimStart("\")
            $destination = Join-Path $destinationRoot $relative
            New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force |
                Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $destination
        }
}

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $output -Force
$expandedOutput = Join-Path $projectRoot "outputs\SignBridge-UAE-prototype"
New-Item -ItemType Directory -Path $expandedOutput -Force | Out-Null
Copy-Item -Path (Join-Path $stage "*") -Destination $expandedOutput -Recurse -Force
Write-Output $output
