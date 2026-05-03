# Troubleshooting

Common errors and fixes, in roughly the order you'd hit them.

## Windows-specific issues

### "I'm on Windows and the wizard says it can't run the commands"

The wizard prefers a Unix-style shell. Two ways to get one:

1. **WSL2 (recommended for daily use):** open PowerShell as admin, run `wsl --install`, restart, then launch the Ubuntu shell from the Start menu. From there: `git clone`, `cd thermomix_meal_prep`, `claude`, `/meal-plan-setup`. Everything works as if you're on Linux.
2. **Git Bash (faster to set up):** install [Git for Windows](https://git-scm.com/download/win) — Git Bash comes bundled. Open Git Bash from the Start menu and run the wizard from there. The wizard detects Git Bash and uses Unix commands.

If you must use PowerShell or cmd directly, the wizard will try to fall back to PowerShell-equivalent commands but it's untested. Symptoms of an unsupported shell:
- "command not found: chmod" → Windows shell, no Unix tooling
- "<<EOF: not recognized" → cmd or PowerShell trying to run a heredoc
- The wizard substitutes `{{REPO_ABSOLUTE_PATH}}` literally → AI didn't detect platform

### "venv was created but Claude Code can't find python.exe"

On Windows, the venv binary is at `.venv\Scripts\python.exe`, not `.venv/bin/python` like Unix. Check `.mcp.json`:
```json
"command": "C:/Users/.../cookidoo-mcp/.venv/Scripts/python.exe"
```
If it says `bin/python` instead of `Scripts/python.exe`, the wizard didn't detect Windows. Edit `.mcp.json` manually to fix the path, then restart Claude Code.

### "PowerShell says script execution is disabled"

If you ran the wizard from PowerShell and got an execution policy error, allow scripts for the current user:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Setup wizard fails

### "Python 3.11+ not found"

Your system has Python but it's too old. macOS ships with Python 3.9, which won't work. Install a newer one:

- **macOS:** `brew install python@3.12` (install [Homebrew](https://brew.sh) first if needed)
- **Linux:** `sudo apt install python3.12` or equivalent for your distro, or use [pyenv](https://github.com/pyenv/pyenv)
- **Windows:** download from [python.org](https://www.python.org/downloads/)

Then re-run `/meal-plan-setup`.

### `pip install` fails

Most common causes:
- **Network error** — try again. The install pulls ~50 MB.
- **Build error mentioning "wheel" or "compiler"** on macOS — install Xcode Command Line Tools: `xcode-select --install`. Then re-run the wizard.
- **Permission denied** — you're trying to install into the system Python, not the venv. The wizard should never do this; if you're running pip manually, make sure you're using `cookidoo-mcp/.venv/bin/pip`, not `pip` or `python -m pip`.

### Wizard says venv creation failed

```
$ python3.12 -m venv cookidoo-mcp/.venv
The virtual environment was not created successfully because ensurepip is not available.
```

On Debian/Ubuntu, install `python3.12-venv`: `sudo apt install python3.12-venv`. Then re-run.

### Permission prompts seem stuck

If Claude Code keeps asking permission for the same Bash command, you might be denying it accidentally. Approve once, and it should remember for the rest of the session. To save permissions across sessions, edit `.claude/settings.local.json` (the wizard doesn't do this for you — you can copy `.claude/settings.example.json` as a starting point).

## MCP doesn't load after setup

### `mcp__cookidoo__whoami` returns "tool not found"

Claude Code didn't pick up the MCP. Three things to try, in order:

1. **Fully quit Claude Code** (Cmd-Q on macOS, not just close the window) and relaunch from the repo directory: `cd /path/to/thermomix_meal_prep && claude`. The `.mcp.json` is read on launch, not reload.
2. **Verify `.mcp.json` exists at the repo root** with `ls -la .mcp.json`. If it doesn't, the wizard didn't finish Phase 4 — re-run it.
3. **Check the paths in `.mcp.json`** are absolute and correct: `cat .mcp.json`. The `command` should point to the venv's Python (e.g. `/Users/you/projects/thermomix_meal_prep/cookidoo-mcp/.venv/bin/python`) and `args[0]` should point to `server.py`.

### Claude Code asks to approve the MCP server every time

That's the security check on first use. Approve once. If it keeps asking, the `.mcp.json` may have changed (e.g. you re-ran the wizard and paths shifted) — Claude Code treats a changed config as a new server.

### `mcp__cookidoo__whoami` returns an auth error

Your credentials in `~/.config/cookidoo-mcp/.env` are wrong. Check:

```bash
ls -la ~/.config/cookidoo-mcp/.env   # should show -rw------- (chmod 600)
```

If the file exists but auth still fails, the email or password is wrong. Re-run the wizard — it'll offer to overwrite the env file.

If the file doesn't exist, the wizard didn't finish Phase 3. Re-run.

### `mcp__cookidoo__whoami` returns a localization error

Your country/language combo isn't supported by the underlying `cookidoo-api` library. Try `us` / `en-US` to confirm the rest works, then narrow down to your locale. Common supported combos:

- `us` / `en-US`
- `gb` / `en-GB`
- `de` / `de-DE`
- `es` / `es-ES`
- `fr` / `fr-FR`
- `ar` / `es-AR`

Edit `~/.config/cookidoo-mcp/.env` directly to change them, then call `whoami` again (no Claude Code restart needed — the env is read on every tool call, not at server start).

## `/meal-plan` runs but produces a weird plan

### "I don't have a persona file"

You haven't run `/meal-plan-setup` yet, or it didn't reach Phase 6. Run the wizard.

### Recipes feel random / unconnected to your collections

The persona's "Known custom collections" section is probably empty. Ask Claude:

> Refresh my custom collections in the persona

It'll call `mcp__cookidoo__list_my_collections(kind="custom")` and update the file.

### Plans repeat recipes from last week

The skill is supposed to read the last two calendar weeks and avoid them. If it's not, check:
- The recipes are actually on your Cookidoo calendar (not just cooked from memory)
- The Cookidoo MCP is alive (`mcp__cookidoo__whoami`)
- The `get_my_calendar_week` tool returned data for both weeks (you can verify by asking Claude to call it and show the raw output)

### Shopping list isn't grouped by your store sections

The persona's `{{PRIMARY_STORE}}` placeholder didn't get filled, or it's set to a store the planner doesn't know how to section. Edit `personas/family-meal-planning.md` and replace any remaining `{{PRIMARY_STORE}}` with your actual store name. The planner uses generic produce/dairy/pantry sections as a fallback if it can't figure out store-specific ones.

## The Cookidoo API broke

The underlying `cookidoo-api` library is unofficial. Cookidoo can change their frontend at any time and break tools. Symptoms: tools that worked yesterday now error with parsing failures or 404s.

What to do:
1. Check [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api) for a new release.
2. Update: `cookidoo-mcp/.venv/bin/pip install --upgrade cookidoo-api`.
3. If that doesn't help, the library hasn't caught up to the change yet. Drop into degraded mode (paste recipe URLs into the chat) until upstream fixes it.

## Still broken

Open an issue on the repo with: the exact error message, your OS + Python version (`python3 --version`), and which phase of the wizard failed (or which `/meal-plan` step).
