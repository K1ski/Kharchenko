$ErrorActionPreference = 'Stop'

$installer = Join-Path $env:RUNNER_TEMP 'tesseract-ocr-w64-setup.exe'
Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.3.20260724.exe' -OutFile $installer
$process = Start-Process -FilePath $installer -ArgumentList '/S' -Wait -PassThru
if ($process.ExitCode -ne 0) {
    throw "Tesseract installer failed with exit code $($process.ExitCode)"
}

$installed = Join-Path $env:ProgramFiles 'Tesseract-OCR'
if (!(Test-Path (Join-Path $installed 'tesseract.exe'))) {
    throw "Tesseract was not installed to $installed"
}

$runtime = Join-Path $PWD 'HedgeHelper_v0.1.0/tesseract_runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
Copy-Item -Path (Join-Path $installed '*') -Destination $runtime -Recurse -Force
New-Item -ItemType Directory -Force (Join-Path $runtime 'tessdata') | Out-Null

$modelBase = 'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/87416418657359cb625c412a48b6e1d6d41c29bd'
foreach ($language in @('eng', 'rus')) {
    Invoke-WebRequest -Uri "$modelBase/$language.traineddata" -OutFile (Join-Path $runtime "tessdata/$language.traineddata")
}
Invoke-WebRequest -Uri "$modelBase/LICENSE" -OutFile (Join-Path $runtime 'LICENSE-TESSDATA-FAST.txt')
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/tesseract-ocr/tesseract/main/LICENSE' -OutFile (Join-Path $runtime 'LICENSE-TESSERACT.txt')

$env:TESSDATA_PREFIX = $runtime
$exe = Join-Path $runtime 'tesseract.exe'
$version = (& $exe --version 2>&1 | Select-Object -First 1)
$languageOutput = & $exe --list-langs 2>&1
if ($LASTEXITCODE -ne 0 -or ($languageOutput -notcontains 'eng') -or ($languageOutput -notcontains 'rus')) {
    throw "Tesseract language verification failed: $($languageOutput -join ', ')"
}
"TESSDATA_PREFIX=$runtime" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
Write-Host "$version; bundled languages: rus+eng"
