# ============================================
# BaseballBinder Safe Cleanup & Restructure
# ============================================

$root = "C:\Users\jorda\Desktop\Baseball Check Lists\card-collection"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archive = Join-Path $root "_ARCHIVE_$timestamp"
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$assets = Join-Path $root "assets"
$excludePatterns = @('_ARCHIVE_*', '.venv', 'venv', 'node_modules', 'Lib', 'site-packages')


Write-Host "Creating archive at: $archive" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $archive | Out-Null

# Ensure new structure
New-Item -ItemType Directory -Force -Path $backend | Out-Null
New-Item -ItemType Directory -Force -Path $frontend | Out-Null
New-Item -ItemType Directory -Force -Path $assets | Out-Null

# Backup unwanted files/folders safely
$trash = @(
    "__pycache__",
    ".idea",
    ".vscode",
    ".venv",
    "dist",
    "build",
    "test",
    "backup",
    "old",
    "node_modules"
)

foreach ($t in $trash) {
    $targets = Get-ChildItem -Path $root -Recurse -Force -ErrorAction SilentlyContinue |
               Where-Object { $_.Name -eq $t }
    foreach ($target in $targets) {
        $dest = Join-Path $archive ($target.FullName -replace [regex]::Escape($root), "")
        New-Item -ItemType Directory -Force -Path (Split-Path $dest) | Out-Null
        Move-Item -Path $target.FullName -Destination $dest -Force
        Write-Host "Moved $($target.FullName) → $dest" -ForegroundColor Yellow
    }
}

# Move core backend files
$backendFiles = @("main.py", "requirements.txt")
foreach ($file in $backendFiles) {
    if (Test-Path (Join-Path $root $file)) {
        Move-Item (Join-Path $root $file) -Destination $backend -Force
        Write-Host "Moved $file to backend/" -ForegroundColor Green
    }
}

# Move checklists and verifier code to backend/app/core
$checklists = Join-Path $backend "app\core"
New-Item -ItemType Directory -Force -Path $checklists | Out-Null
Get-ChildItem "$root\checklists" -Recurse -File | ForEach-Object {
    Move-Item $_.FullName -Destination $checklists -Force
}
Write-Host "Moved checklists into backend/app/core" -ForegroundColor Green

# Move logos or PNGs to assets
Get-ChildItem -Path $root -Recurse -Include *.png,*.jpg,*.jpeg -ErrorAction SilentlyContinue |
    ForEach-Object {
        $dest = Join-Path $assets $_.Name
        Move-Item $_.FullName -Destination $dest -Force
        Write-Host "Moved asset $($_.Name)" -ForegroundColor Cyan
    }

Write-Host "`n✅ Cleanup complete. Backup saved to $archive" -ForegroundColor Green
