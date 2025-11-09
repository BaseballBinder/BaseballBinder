# Vision UI Dashboard Restoration Script
# ⚠️ CAUTION: This will reset your theme to defaults
# Only run if you need to recover from a broken state

Write-Host "🧩 Starting Vision UI dashboard restoration..." -ForegroundColor Cyan

# 1️⃣ Kill any running Node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

# 2️⃣ Backup your custom code first
if (!(Test-Path "../_backup")) {
    New-Item -ItemType Directory -Path "../_backup" | Out-Null
}
Write-Host "Backing up custom files..."
Copy-Item "src/layouts/dashboard/index.js" "../_backup/dashboard_index_backup.js" -Force
Copy-Item "src/ChecklistTable.jsx" "../_backup/ChecklistTable_backup.jsx" -Force

# 3️⃣ Clean build & cache directories
Write-Host "Cleaning cache and modules..."
Remove-Item -Recurse -Force "node_modules" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".next" -ErrorAction SilentlyContinue
Remove-Item -Force "package-lock.json" -ErrorAction SilentlyContinue

# 4️⃣ Reinstall base Vision UI dependencies
Write-Host "Installing core dependencies..."
npm install react@18.3.1 react-dom@18.3.1
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material react-router-dom --legacy-peer-deps

# 5️⃣ Reinstall other essentials
npm install axios --legacy-peer-deps
npm install react-scripts --save-dev

# 6️⃣ Restore theme structure if missing
if (!(Test-Path "src/assets/theme")) {
    Write-Host "Restoring theme folder structure..."
    New-Item -ItemType Directory -Path "src/assets/theme/base" -Force | Out-Null
    New-Item -ItemType Directory -Path "src/assets/theme/functions" -Force | Out-Null
}

# 7️⃣ Write placeholder theme files (Claude will rebuild these)
@'
export default {
  colors: {
    background: "#181820",
    surface: "#232333",
    primary: "#7B61FF",
    secondary: "#A0233F",
    accent: "#C15C9B",
    text: {
      primary: "#E9E9EC",
      secondary: "#A9A9B3"
    }
  }
};
'@ | Out-File -Encoding utf8 "src/assets/theme/base/colors.js"

@'
export default function linearGradient(color1, color2, angle = 310) {
  return `linear-gradient(${angle}deg, ${color1}, ${color2})`;
}
'@ | Out-File -Encoding utf8 "src/assets/theme/functions/linearGradient.js"

@'
import colors from "./base/colors";
export default {
  palette: {
    background: { default: colors.background },
    primary: { main: colors.primary },
    secondary: { main: colors.secondary }
  },
  typography: {
    fontFamily: "Inter, sans-serif"
  }
};
'@ | Out-File -Encoding utf8 "src/assets/theme/theme.js"

# 8️⃣ Verify structure
Write-Host "`n✅ Structure check:" -ForegroundColor Cyan
Get-ChildItem "src/assets/theme" -Recurse

# 9️⃣ Rebuild the app
Write-Host "`n⚙️ Rebuilding frontend..."
npm run build

Write-Host "`n🎨 All theme scaffolding restored."
Write-Host "✅ Now open the project in VS Code, reinsert your ChecklistTable and dashboard, and let Claude restore gradients/shadows."
Write-Host "   Path: src/assets/theme/"
Write-Host "   Then run: npm start"
