# GitHub Setup Guide for ZilKit

Follow these steps to create the repo and push your first commit.

## Prerequisites

- **Git** installed ([git-scm.com](https://git-scm.com/download/win))
- **GitHub account**

---

## Step 1: Create the repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `ZilKit` (or your preferred name)
3. Description: `Windows context menu tool for FFmpeg operations, system shortcuts, and utilities`
4. Choose **Public**
5. **Do not** initialize with README, .gitignore, or license (we already have these)
6. Click **Create repository**

---

## Step 2: Initialize and push from your PC

Open **Command Prompt** or **PowerShell** in the ZilKit folder and run:

```batch
cd D:\Dropbox\PrestigeAV\CodeProjects\ZilKit

:: Initialize the repository
git init

:: Add all files (respects .gitignore)
git add .

:: Create the first commit
git commit -m "Initial commit: ZilKit v0.1.0"

:: Add your GitHub repo as the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ZilKit.git

:: Push to GitHub (use 'main' or 'master' depending on your default branch)
git branch -M main
git push -u origin main
```

**If using SSH instead of HTTPS:**
```batch
git remote add origin git@github.com:YOUR_USERNAME/ZilKit.git
```

---

## Step 3: Clone on your VM

On the VM, clone to a **local drive** (e.g. C:) so the elevated installer works:

```batch
cd C:\
git clone https://github.com/YOUR_USERNAME/ZilKit.git C:\Tools\ZilKit
cd C:\Tools\ZilKit
install.bat
```

---

## Daily workflow

**On your PC (after making changes):**
```batch
cd D:\Dropbox\PrestigeAV\CodeProjects\ZilKit
git add .
git commit -m "Description of your changes"
git push
```

**On your VM (to get updates):**
```batch
cd C:\Tools\ZilKit
git pull
:: Re-run install.bat only if install/registry code changed
```

---

## What's in .gitignore

The following are excluded from the repo:

- Python: `__pycache__`, `*.pyc`, `*.egg-info`, etc.
- Virtual envs: `.venv/`, `venv/`
- IDE/OS: `.vscode/`, `.idea/`, `Thumbs.db`
- Build artifacts: `build/`, `dist/`
- Logs: `*.log`, `logs/`
- Dropbox conflicted copies: `*conflicted*`
