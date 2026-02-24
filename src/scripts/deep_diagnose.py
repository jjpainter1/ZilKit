"""Deep diagnostic script to find all ZilKit-related registry entries."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import winreg
except ImportError:
    print("ERROR: winreg module not available")
    sys.exit(1)

from rich.console import Console
from rich.panel import Panel

console = Console(force_terminal=True)


def check_key_exists(hkey, path):
    """Check if a registry key exists."""
    try:
        with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY):
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def read_value(hkey, path, value_name=""):
    """Read a registry value."""
    try:
        with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            return val
    except:
        return None


def list_subkeys(hkey, path):
    """List all subkeys of a registry key."""
    subkeys = []
    try:
        with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, i)
                    subkeys.append(subkey)
                    i += 1
                except OSError:
                    break
    except:
        pass
    return subkeys


def main():
    console.print(Panel.fit(
        "[bold cyan]Deep Registry Diagnostic[/bold cyan]",
        border_style="cyan"
    ))
    
    # Check main menu
    console.print("\n[bold]1. MAIN MENU (HKCR)[/bold]")
    main_path = r"Directory\Background\shell\ZilKit"
    
    if check_key_exists(winreg.HKEY_CLASSES_ROOT, main_path):
        console.print(f"  [green]EXISTS[/green]: {main_path}")
        subcommands = read_value(winreg.HKEY_CLASSES_ROOT, main_path, "SubCommands")
        console.print(f"  SubCommands = \"{subcommands}\"")
        
        if subcommands:
            expected = subcommands.split(";")
            console.print(f"  [yellow]Looking for these CommandStore keys: {expected}[/yellow]")
    else:
        console.print(f"  [red]NOT FOUND[/red]: {main_path}")
    
    # Check CommandStore in HKLM
    console.print("\n[bold]2. COMMANDSTORE (HKLM) - All ZilKit/ZK related keys[/bold]")
    cs_base = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CommandStore\shell"
    
    all_subkeys = list_subkeys(winreg.HKEY_LOCAL_MACHINE, cs_base)
    
    # Filter for ZilKit-related keys
    zilkit_keys = [k for k in all_subkeys if k.startswith(("ZilKit", "ZK", "zk", "zilkit"))]
    
    if zilkit_keys:
        console.print(f"  Found {len(zilkit_keys)} ZilKit-related keys:")
        for key_name in sorted(zilkit_keys):
            full_path = f"{cs_base}\\{key_name}"
            muiverb = read_value(winreg.HKEY_LOCAL_MACHINE, full_path, "MUIVerb")
            default_val = read_value(winreg.HKEY_LOCAL_MACHINE, full_path, "")
            subcmds = read_value(winreg.HKEY_LOCAL_MACHINE, full_path, "SubCommands")
            has_cmd = check_key_exists(winreg.HKEY_LOCAL_MACHINE, f"{full_path}\\command")
            
            console.print(f"\n    [cyan]{key_name}[/cyan]")
            if muiverb:
                console.print(f"      MUIVerb: {muiverb}")
            if default_val:
                console.print(f"      @: {default_val}")
            if subcmds:
                console.print(f"      SubCommands: {subcmds}")
            if has_cmd:
                cmd = read_value(winreg.HKEY_LOCAL_MACHINE, f"{full_path}\\command", "")
                console.print(f"      [green]Has command subkey[/green]")
    else:
        console.print("  [red]No ZilKit-related keys found![/red]")
    
    # Check HKCU as well
    console.print("\n[bold]3. COMMANDSTORE (HKCU) - Check for duplicates[/bold]")
    hkcu_keys = list_subkeys(winreg.HKEY_CURRENT_USER, cs_base)
    zilkit_hkcu = [k for k in hkcu_keys if k.startswith(("ZilKit", "ZK", "zk", "zilkit"))]
    
    if zilkit_hkcu:
        console.print(f"  [yellow]Found {len(zilkit_hkcu)} keys in HKCU (potential conflict!):[/yellow]")
        for key_name in sorted(zilkit_hkcu):
            console.print(f"    - {key_name}")
    else:
        console.print("  [green]No ZilKit keys in HKCU (good)[/green]")
    
    # Summary
    console.print("\n[bold]4. DIAGNOSIS[/bold]")
    
    # Check if SubCommands matches existing keys
    if subcommands:
        expected_keys = subcommands.split(";")
        missing = []
        for key_name in expected_keys:
            if key_name not in zilkit_keys:
                missing.append(key_name)
        
        if missing:
            console.print(f"  [red]PROBLEM: SubCommands references keys that don't exist:[/red]")
            for m in missing:
                console.print(f"    [red]- {m} (MISSING)[/red]")
        else:
            console.print(f"  [green]All SubCommands keys exist in CommandStore[/green]")
    
    # Check for old-style keys that might conflict
    old_style = [k for k in zilkit_keys if k.startswith("ZilKit")]
    new_style = [k for k in zilkit_keys if k.startswith("ZK") and not k.startswith("ZilKit")]
    
    if old_style and new_style:
        console.print(f"\n  [yellow]WARNING: Both old and new style keys exist![/yellow]")
        console.print(f"    Old style (ZilKit*): {old_style}")
        console.print(f"    New style (ZK*): {new_style}")
        console.print(f"  [yellow]This could cause conflicts![/yellow]")
    
    console.print("\n[dim]Press any key to exit...[/dim]")
    try:
        input()
    except:
        pass


if __name__ == "__main__":
    main()
