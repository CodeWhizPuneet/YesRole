# Start the local app from any working directory after installing its dependencies.
param([uri]$TeacherUrl)

$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$python = Join-Path $project '.venv\Scripts\python.exe'
$frontend = Join-Path $project 'frontend'
$backend = Join-Path $project 'backend'
$vite = Join-Path $frontend 'node_modules\vite\bin\vite.js'
$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
$node = if ($env:YESROLE_NODE_EXE) { $env:YESROLE_NODE_EXE } elseif ($nodeCommand) { $nodeCommand.Source } else {
    $runtime = Get-AppxPackage -Name 'OpenAI.CodexPrimaryRuntime*' -ErrorAction SilentlyContinue | Sort-Object Version -Descending | Select-Object -First 1
    if ($runtime) { Join-Path $runtime.InstallLocation 'dependencies\node\bin\node.exe' }
}

if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $vite) -or -not $node -or -not (Test-Path -LiteralPath $node)) {
    throw 'Install Python and frontend dependencies using the PowerShell commands in README.md.'
}

$logs = Join-Path $project '.runtime'
New-Item -ItemType Directory -Force -Path $logs | Out-Null

if ($TeacherUrl) {
    if (-not $TeacherUrl.IsAbsoluteUri -or $TeacherUrl.Scheme -ne 'https' -or
        $TeacherUrl.AbsolutePath -ne '/' -or $TeacherUrl.Query -or $TeacherUrl.Fragment -or $TeacherUrl.UserInfo) {
        throw 'Pass the HTTPS URL printed by the tunnel, without a path.'
    }
    $env:VITE_HOSTED_DEMO = 'true'
    $env:VITE_API_URL = ''
    $env:YESROLE_WEB_ROOT = Join-Path $logs 'teacher-web'
    $env:YESROLE_DB = Join-Path $logs ('teacher-' + [guid]::NewGuid() + '.sqlite3')
    $env:YESROLE_ALLOWED_HOSTS = '127.0.0.1,localhost,' + $TeacherUrl.Host
    $env:YESROLE_CORS_ORIGINS = $TeacherUrl.GetLeftPart([UriPartial]::Authority)
    $env:YESROLE_OFFLINE = 'true'
    $bytes = [byte[]]::new(18)
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    $env:YESROLE_DEMO_PASSWORD = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    Push-Location $frontend
    try {
        & $node $vite build --outDir $env:YESROLE_WEB_ROOT
        if ($LASTEXITCODE -ne 0) { throw 'The teacher demo frontend build failed.' }
    } finally { Pop-Location }
    Write-Host "Open $env:YESROLE_CORS_ORIGINS after the server starts."
    Write-Host "Username: yesrole"
    Write-Host "Demo password: $env:YESROLE_DEMO_PASSWORD"
    Push-Location $backend
    try {
        & $python -m uvicorn app.hosted:create_default_app --factory --host 127.0.0.1 --port 8080 --no-access-log
        if ($LASTEXITCODE -ne 0) { throw 'The teacher demo server stopped with an error.' }
    } finally {
        Pop-Location
        Remove-Item Env:YESROLE_DEMO_PASSWORD -ErrorAction SilentlyContinue
    }
    return
}

$api = $null
$web = $null
$apiOptions = @{
    FilePath = $python
    WorkingDirectory = $backend
    WindowStyle = 'Hidden'
    ArgumentList = '-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log'
    RedirectStandardOutput = Join-Path $logs 'api.log'
    RedirectStandardError = Join-Path $logs 'api-error.log'
}
$webOptions = @{
    FilePath = $node
    WorkingDirectory = $frontend
    WindowStyle = 'Hidden'
    ArgumentList = '"{0}" --host 127.0.0.1' -f $vite
    RedirectStandardOutput = Join-Path $logs 'web.log'
    RedirectStandardError = Join-Path $logs 'web-error.log'
}
try {
    $api = Start-Process @apiOptions -PassThru
    $web = Start-Process @webOptions -PassThru
    Write-Host 'Open http://127.0.0.1:5173. Press Ctrl+C to stop both servers.'
    Write-Host "Server logs: $logs"
    while (-not $api.HasExited -and -not $web.HasExited) {
        Start-Sleep -Milliseconds 600
    }
    throw 'A YesRole service stopped. See api-error.log and web-error.log under .runtime.'
} finally {
    foreach ($process in @($web, $api)) {
        if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id }
    }
}

