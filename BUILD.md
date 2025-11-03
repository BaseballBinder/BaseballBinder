# Building and Releasing Baseball Binder

This document explains how to build the executable and create new releases.

## Prerequisites

- Python 3.11 or higher
- All dependencies from `requirements.txt`
- PyInstaller (`pip install pyinstaller`)

## Local Build

### Windows

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the build script:
   ```bash
   build.bat
   ```

3. The executable will be created in:
   ```
   releases\BaseballBinder-v{version}-{date}\BaseballBinder.exe
   ```

### Manual Build

If you prefer to build manually:

```bash
python -m PyInstaller BaseballBinder.spec --clean
```

The output will be in `dist/BaseballBinder/`.

## Creating a New Release

### Step 1: Update Version

1. Edit `version.json`:
   ```json
   {
     "version": "0.3.0",  // <-- Update this
     "release_date": "2025-01-10",  // <-- Update this
     "release_notes": [
       "New feature 1",
       "Bug fix 1",
       // ... add your changes
     ]
   }
   ```

### Step 2: Commit Changes

```bash
git add .
git commit -m "Release v0.3.0 - Description of changes"
```

### Step 3: Create and Push Tag

```bash
git tag v0.3.0
git push origin main
git push origin v0.3.0
```

### Step 4: GitHub Actions Will Automatically:

1. Build the Windows executable
2. Create a GitHub Release
3. Upload the executable as a release asset
4. Users will be notified of the update when they launch the app

## Release Workflow

The automated release process:

1. **Trigger**: Pushing a version tag (e.g., `v0.3.0`)
2. **Build**: GitHub Actions builds the executable on Windows
3. **Release**: Creates a GitHub Release with:
   - The tag version
   - Release notes
   - Windows executable (`.exe`)
   - Zipped distribution (`.zip`)
4. **Notification**: Users see update notification in-app

## Version Numbering

We use [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

Examples:
- `v0.2.0` → `v0.2.1`: Bug fix
- `v0.2.1` → `v0.3.0`: New feature
- `v0.3.0` → `v1.0.0`: Major release or breaking change

## Testing Before Release

Before creating a release tag:

1. Test the application locally
2. Build locally and test the executable
3. Ensure all features work as expected
4. Update `version.json` with accurate release notes
5. Commit and push to main
6. Create the version tag

## Rollback

If a release has issues:

1. Create a new patch version with fixes
2. Release the patched version
3. Optionally delete the problematic release from GitHub

## User Update Flow

When you release a new version:

1. User opens Baseball Binder
2. App checks GitHub for updates (after 2-second delay)
3. If update available, shows professional modal with:
   - Current version
   - New version
   - Release notes
   - Download button
4. User clicks "Download Update"
5. Browser opens to download the new `.exe`
6. User installs by replacing old executable

## Notes

- The app checks for updates once per day (stored in localStorage)
- Users can dismiss updates and be reminded the next day
- Only shows updates when a newer version has an `.exe` asset
- Production-ready system with proper error handling
