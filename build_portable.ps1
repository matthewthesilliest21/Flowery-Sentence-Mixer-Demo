$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
$BundlePath = Join-Path $ProjectRoot 'dist\VoiceLineMixer'
$ZipPath = Join-Path $ProjectRoot 'dist\VoiceLineMixer-portable.zip'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Project Python environment not found. Create .venv and install requirements.txt plus requirements-build.txt first.'
}

& $Python -m PyInstaller --noconfirm --clean --onedir --windowed `
    --name VoiceLineMixer `
    --add-data "$ProjectRoot\data\library.json;data" `
    --add-data "$ProjectRoot\input_audio;input_audio" `
    --collect-all cmudict `
    --copy-metadata cmudict `
    --hidden-import pronouncing `
    (Join-Path $ProjectRoot 'app.py')
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Copy-Item -LiteralPath (Join-Path $ProjectRoot 'README.md') -Destination (Join-Path $BundlePath 'README.txt') -Force
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -LiteralPath $BundlePath -DestinationPath $ZipPath -CompressionLevel Optimal
Write-Output "Portable release created: $ZipPath"
