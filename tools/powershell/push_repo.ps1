<#
Safe Git push helper.
Run from repo root after syncing/copying files.
#>

param(
    [string]$Message = "Update unified AI system repository"
)

$ErrorActionPreference = "Stop"

git status

git add .

git status

$changes = git status --porcelain
if ([string]::IsNullOrWhiteSpace($changes)) {
    Write-Host "No changes to commit." -ForegroundColor Yellow
    exit 0
}

git commit -m $Message

git push

Write-Host "GitHub push completed." -ForegroundColor Green
