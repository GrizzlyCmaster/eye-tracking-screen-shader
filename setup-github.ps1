# Eye Tracking Screen Shader - GitHub Repository Setup
# This script configures the git repository for GitHub publication

Write-Host "=== Eye Tracking Screen Shader - GitHub Setup ===" -ForegroundColor Green

# Check if git is installed
$gitCheck = git --version 2>$null
if (-not $gitCheck) {
    Write-Host "ERROR: Git is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Git version: $gitCheck"

# Change to project directory
$projectDir = Split-Path -Parent $PSCommandPath
Set-Location $projectDir
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Cyan

# 1. Configure git user (if not already set)
Write-Host "`n1. Configuring git user..." -ForegroundColor Yellow
$gitUserName = git config user.name 2>$null
$gitUserEmail = git config user.email 2>$null

if (-not $gitUserName) {
    Write-Host "Enter your GitHub username:"
    $username = Read-Host
    git config user.name $username
    Write-Host "Username set: $username" -ForegroundColor Green
}
else {
    Write-Host "Git user already configured: $gitUserName" -ForegroundColor Green
}

if (-not $gitUserEmail) {
    Write-Host "Enter your GitHub email:"
    $email = Read-Host
    git config user.email $email
    Write-Host "Email set: $email" -ForegroundColor Green
}
else {
    Write-Host "Git email already configured: $gitUserEmail" -ForegroundColor Green
}

# 2. Check current status
Write-Host "`n2. Checking git status..." -ForegroundColor Yellow
git status

# 3. Remove old remote if changing repos
Write-Host "`n3. Git remote configuration..." -ForegroundColor Yellow
$currentRemote = git remote get-url origin 2>$null
if ($currentRemote) {
    Write-Host "Current remote: $currentRemote" -ForegroundColor Cyan
    Write-Host "If creating a NEW repository, you'll update this after creating the repo on GitHub."
}
else {
    Write-Host "No remote currently set. You'll add it after creating the GitHub repo." -ForegroundColor Cyan
}

# 4. Stage and commit
Write-Host "`n4. Preparing commit..." -ForegroundColor Yellow
Write-Host "Files to be committed:"
git diff --name-only --cached | ForEach-Object { Write-Host "  + $_" -ForegroundColor Green }

$proceed = Read-Host "`nAdd all changes and create initial commit? (y/n)"
if ($proceed -eq 'y' -or $proceed -eq 'Y') {
    Write-Host "Adding files..." -ForegroundColor Yellow
    git add .
    
    Write-Host "Creating commit..." -ForegroundColor Yellow
    git commit -m "Initial commit: Eye tracking screen shader with foveated rendering

- Added foveated rendering shader (motion-sickness safe)
- Python eye tracking application with webcam support
- Eye_tracker.exe executable (PyInstaller build)
- Complete documentation and setup guides
- Zoom/fisheye shader reference implementation"
    
    Write-Host "Commit created successfully!" -ForegroundColor Green
}
else {
    Write-Host "Skipped commit creation" -ForegroundColor Yellow
}

# 5. Final instructions
Write-Host "`n" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NEXT STEPS - Create GitHub Repository" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "
1. Go to https://github.com/new
2. Create a new repository with these settings:
   - Repository name: eye-tracking-screen-shader
   - Description: GPU-accelerated eye-tracking shader with foveated rendering for FPS gaming
   - Public (recommended for open source)
   - Do NOT initialize with README, .gitignore, or license (already have them)

3. After creating the repository, copy the remote URL from GitHub

4. Set the remote URL in this repository by running:
   git remote set-url origin https://github.com/YOUR_USERNAME/eye-tracking-screen-shader.git
   
   OR if no remote exists:
   git remote add origin https://github.com/YOUR_USERNAME/eye-tracking-screen-shader.git

5. Push to GitHub:
   git branch -M main
   git push -u origin main

6. (Optional) Add a LICENSE file:
   - Copy existing LICENSE to repository if you have one
   - Run: git add LICENSE && git commit -m 'Add license'
   - Run: git push

========================================
" -ForegroundColor Cyan

# 6. Optional: Set remote directly
$setRemote = Read-Host "`nWould you like to set the GitHub remote URL now? (y/n)"
if ($setRemote -eq 'y' -or $setRemote -eq 'Y') {
    Write-Host "Enter your GitHub username:"
    $githubUser = Read-Host
    $remoteUrl = "https://github.com/$githubUser/eye-tracking-screen-shader.git"
    
    git remote set-url origin $remoteUrl 2>$null
    if ($LASTEXITCODE -ne 0) {
        git remote add origin $remoteUrl
    }
    
    Write-Host "Remote set to: $remoteUrl" -ForegroundColor Green
    Write-Host "`nReady to push! Run: git push -u origin main" -ForegroundColor Green
}

Write-Host "`nSetup complete!" -ForegroundColor Green
