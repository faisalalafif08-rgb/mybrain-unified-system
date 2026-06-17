<#
Safe sync script for Fooocus and stable-diffusion-webui-master.

Purpose:
- Copy only code/config/docs from local engines into this GitHub repo workspace.
- Exclude heavy folders: models, outputs, venv, repositories, caches.
- Avoid browser upload limits such as 500 files.

Usage example:
  powershell -ExecutionPolicy Bypass -File tools\powershell\sync_visual_engines_to_repo.ps1 `
    -FooocusSource "D:\Fooocus" `
    -WebUISource "D:\stable-diffusion-webui-master"
#>

param(
    [string]$RepoRoot = (Resolve-Path ".").Path,
    [string]$FooocusSource = "D:\Fooocus",
    [string]$WebUISource = "D:\stable-diffusion-webui-master"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir($Path) {
    if (!(Test-Path $Path)) {
        New-Item -ItemType Directory -Force -Path $Path | Out-Null
    }
}

function Sync-Engine($Source, $Target, $Name) {
    if (!(Test-Path $Source)) {
        Write-Warning "$Name source not found: $Source"
        return
    }

    Ensure-Dir $Target

    Write-Host "Syncing $Name" -ForegroundColor Cyan
    Write-Host "From: $Source"
    Write-Host "To:   $Target"

    robocopy $Source $Target /E `
        /XD .git .github venv .venv env __pycache__ models outputs output repositories cache .cache tmp temp node_modules `
        /XF *.safetensors *.ckpt *.pt *.pth *.onnx *.bin *.gguf *.zip *.7z *.rar *.tar *.gz *.mp4 *.mov *.avi *.mkv *.webm *.wav *.mp3 *.flac *.png *.jpg *.jpeg *.webp *.db *.sqlite *.sqlite3 `
        /R:1 /W:1 /NFL /NDL /NP

    $code = $LASTEXITCODE
    if ($code -le 7) {
        Write-Host "$Name sync completed with robocopy code $code" -ForegroundColor Green
    } else {
        throw "$Name sync failed with robocopy code $code"
    }
}

$FooocusTarget = Join-Path $RepoRoot "unified_ai_system\05_specialized_systems\studio_vision\fooocus"
$WebUITarget = Join-Path $RepoRoot "unified_ai_system\05_specialized_systems\studio_vision\stable_diffusion_webui_master"

Ensure-Dir (Join-Path $RepoRoot "unified_ai_system\05_specialized_systems\studio_vision")
Ensure-Dir (Join-Path $RepoRoot "unified_ai_system\10_adapters\visual_engines")

Sync-Engine -Source $FooocusSource -Target $FooocusTarget -Name "Fooocus"
Sync-Engine -Source $WebUISource -Target $WebUITarget -Name "Stable Diffusion WebUI"

Write-Host ""
Write-Host "Next commands:" -ForegroundColor Yellow
Write-Host "git status"
Write-Host "git add ."
Write-Host "git commit -m \"Sync visual engines code references\""
Write-Host "git push"
