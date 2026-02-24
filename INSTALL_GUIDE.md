# ZilKit Installation Guide

Simple installation for Windows 10/11 (including fresh VMs).

---

## Quick Install (Recommended)

1. **Copy the ZilKit folder** to a permanent location (e.g. `C:\Tools\ZilKit`).
2. **Double-click `install.bat`** in the ZilKit folder.
3. Approve the Administrator prompt when asked.
4. Follow the on-screen steps.

The installer will:
- Check for WinGet (Microsoft’s package manager)
- Install Python and FFmpeg via WinGet if they’re missing
- Install ZilKit’s dependencies
- Add ZilKit to your right-click context menu

**If Python or FFmpeg is installed during setup:**  
Close the window when prompted, then run `install.bat` again so Windows can refresh its settings.

---

## After Installation

1. Open File Explorer and go to any folder.
2. Right-click in the empty area (not on a file).
3. You should see **ZilKit** with submenus: **FFmpeg**, **Shortcuts**, **Utilities**.

If the menu doesn’t appear, restart Windows Explorer:
- Open Task Manager (Ctrl+Shift+Esc)
- Find “Windows Explorer” → Right-click → Restart

---

## Requirements

- **WinGet** – Usually included with Windows 10/11. If missing: [aka.ms/getwinget](https://aka.ms/getwinget)
- **Administrator rights** – Needed to add the context menu

---

## Uninstall

```batch
cd C:\Tools\ZilKit
python src\scripts\uninstall.py
```

Then restart Windows Explorer (same as after install).

---

## Troubleshooting

| Problem | Solution |
|--------|----------|
| **Context menu doesn’t appear** | Run `install.bat` as Administrator; restart Explorer |
| **WinGet not found** | Install from [aka.ms/getwinget](https://aka.ms/getwinget) |
| **Python/FFmpeg install fails** | Install manually from python.org and ffmpeg.org |
| **“Module not found”** | Run `install.bat` again after installing Python |

### Logs

`%LOCALAPPDATA%\ZilKit\logs\`

### Config

`%LOCALAPPDATA%\ZilKit\config.json`
