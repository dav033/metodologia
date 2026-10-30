# Bitácora opener for Windows (D-201): «en mi computador ↗» in the «Probar» panel opens bitacora://open/?port=N&path=/p.
# This script, installed once, handles those links on the owner's own computer: when localhost:N is not open yet it
# starts the SSH bridge (ssh -N -L N:127.0.0.1:N <destino>) in a minimized window, waits for the port, and opens
# http://localhost:N/p in the default browser.
#
# Install (once, no administrator needed):   powershell -ExecutionPolicy Bypass -File bitacora-opener.ps1
#   It asks how this computer reaches the Linux machine over SSH (the same destination you use for the panel's tunnel),
#   copies itself to %LOCALAPPDATA%\bitacora and registers the bitacora:// protocol for the current user.
# Uninstall:                                  powershell -ExecutionPolicy Bypass -File bitacora-opener.ps1 -Uninstall
param(
    [string]$Open = "",
    [switch]$Uninstall
)
$ErrorActionPreference = "Stop"
$Dir = Join-Path $env:LOCALAPPDATA "bitacora"
$Script = Join-Path $Dir "bitacora-opener.ps1"
$Config = Join-Path $Dir "opener.json"
$Key = "HKCU:\Software\Classes\bitacora"
$DefaultTarget = "-J root@185.147.157.25 -p 2222 david@127.0.0.1"

function Show-Error([string]$Text) {
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show($Text, "Bitácora") | Out-Null
}

function Test-Port([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $client.Connect("127.0.0.1", $Port); return $true } catch { return $false } finally { $client.Close() }
}

if ($Uninstall) {
    if (Test-Path $Key) { Remove-Item $Key -Recurse -Force }
    if (Test-Path $Dir) { Remove-Item $Dir -Recurse -Force }
    Write-Host "Abridor de Bitácora desinstalado."
    exit 0
}

if (-not $Open) {
    # install
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    $current = $DefaultTarget
    if (Test-Path $Config) { $current = (Get-Content $Config -Raw | ConvertFrom-Json).target }
    Write-Host "¿Cómo llega este computador al Linux por SSH? (Enter = $current)"
    $answer = Read-Host "Destino SSH"
    if ($answer.Trim()) { $current = $answer.Trim() }
    @{ target = $current } | ConvertTo-Json | Set-Content -Encoding UTF8 $Config
    Copy-Item -Force $PSCommandPath $Script
    New-Item -Force -Path $Key | Out-Null
    Set-ItemProperty -Path $Key -Name "(Default)" -Value "URL:Bitacora"
    Set-ItemProperty -Path $Key -Name "URL Protocol" -Value ""
    New-Item -Force -Path "$Key\shell\open\command" | Out-Null
    $command = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Script`" -Open `"%1`""
    Set-ItemProperty -Path "$Key\shell\open\command" -Name "(Default)" -Value $command
    Write-Host "Listo: los enlaces «en mi computador» abren el puente ($current) y la página en tu navegador."
    exit 0
}

# open: bitacora://open/?port=3002&path=/login
try {
    Add-Type -AssemblyName System.Web
    $uri = [System.Uri]$Open
    if ($uri.Scheme -ne "bitacora" -or $uri.Host -ne "open") { throw "enlace no reconocido: $Open" }
    $q = [System.Web.HttpUtility]::ParseQueryString($uri.Query)
    $port = 0
    if (-not [int]::TryParse($q["port"], [ref]$port) -or $port -lt 1024 -or $port -gt 65535) { throw "puerto no válido" }
    $path = $q["path"]
    if (-not $path) { $path = "/" }
    # only a path on the same local port: never another host, never a command
    if ($path -notmatch '^/[A-Za-z0-9_\-./\[\]]*$' -or $path.Contains("//")) { throw "ruta no válida: $path" }
    if (-not (Test-Path $Config)) { throw "el abridor no está instalado: ejecuta bitacora-opener.ps1 una vez" }
    $target = (Get-Content $Config -Raw | ConvertFrom-Json).target
    if (-not (Test-Port $port)) {
        $sshArgs = @("-N", "-o", "ExitOnForwardFailure=yes", "-o", "ServerAliveInterval=30", "-L", "${port}:127.0.0.1:${port}") +
                ($target -split '\s+' | Where-Object { $_ })
        Start-Process -FilePath "ssh.exe" -ArgumentList $sshArgs -WindowStyle Minimized
        $deadline = (Get-Date).AddSeconds(45)
        while (-not (Test-Port $port)) {
            if ((Get-Date) -gt $deadline) { throw "el puente SSH al puerto $port no abrió en 45 s (revisa la ventana minimizada de ssh)" }
            Start-Sleep -Milliseconds 500
        }
    }
    Start-Process "http://localhost:$port$path"
} catch {
    Show-Error ("Bitácora: " + $_.Exception.Message)
    exit 1
}
