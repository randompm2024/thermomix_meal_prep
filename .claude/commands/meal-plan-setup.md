---
description: One-time setup wizard for the meal-plan skill. Installs the Cookidoo MCP, fills in the household persona, and verifies the MCP connection.
---

You are running the one-time setup wizard for this repo. The user just cloned it and wants a working `/meal-plan` skill on their machine. Walk them through every step. Use AskUserQuestion (not many separate prompts) to batch questions. Confirm before any system change. The user may be non-technical — explain what each step does in one line before running it.

**Tool guidance (read carefully — the wizard depends on you using the right tool at each step):**
- `Bash` for shell commands. Each Bash call is a fresh shell — `cd` does NOT persist. Always use absolute paths.
- `Read` for inspecting existing files (template, .env, .mcp.json.example).
- `Write` for creating new files (the filled persona, the .mcp.json, the .env file via heredoc through Bash).
- `Edit` for surgically modifying an existing file.
- `AskUserQuestion` for any user input. Batch up to 4 questions per call. Never ask one question at a time when 4 fit.

**Absolute paths:** Use `pwd` once at the start to determine the repo root, then build absolute paths from it. Don't rely on `cd`.

**Platform detection (first thing you do):** Run `uname -s 2>/dev/null || ver` to detect the OS. Branch behavior accordingly:
- `Darwin` → macOS — use the Unix paths and commands shown below as the default
- `Linux` → Linux (or WSL) — same as macOS, with minor install-tool differences (apt/dnf instead of brew)
- `MINGW*` / `MSYS*` / `CYGWIN*` → Git Bash on Windows — Unix-style commands work, but venv binaries live in `Scripts/` not `bin/`
- `MSYS_NT` or anything mentioning Windows from `ver` → native Windows shell (cmd or PowerShell) — fall back to platform-native commands

**Critical Windows note:** if the user is on native Windows without Git Bash or WSL, **stop and ask them to install Git Bash** (`winget install Git.Git`, ships with Git Bash) or [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install). Then ask them to re-launch Claude Code from inside Git Bash or the WSL shell. The wizard's heredoc/chmod/path conventions assume a Unix-style shell. You CAN attempt native PowerShell-only setup, but it's untested and you'll have to translate every shell command yourself — only attempt this if the user explicitly insists.

Throughout the wizard, where commands differ by platform, the Unix form is shown first and the Windows-Git-Bash form is shown after with `# Windows:` comments. Pick the right one for the detected platform.

---

## Phase 0 — Preflight

Tell the user what this wizard does, in 4-5 lines:
1. Detect a working Python 3.11+ on this machine
2. Install the local Cookidoo MCP (Python venv + dependencies, ~30-60s)
3. Collect their Cookidoo credentials and write them to a chmod-600 env file outside the repo
4. Walk them through filling the persona file (household, constraints, store, equipment)
5. Drop a `.mcp.json` so Claude Code auto-loads the MCP, then test it

Tell them: **"You'll see permission prompts each time I run a Bash command or write a file. Approve them. After we register the MCP, Claude Code will also ask you to approve the new MCP server on first use."**

Ask one batch (up to 4 questions) using AskUserQuestion to confirm preflight:
- Do you have an active Cookidoo+ subscription? (Yes / No / Not sure)
- Which Thermomix model? (TM7 / TM6 / TM5 / Other / None yet)
- Where do you want generated meal plans saved? (`outputs/meal-plan/` inside this repo (Recommended) / Elsewhere — I'll specify)
- Are you OK with the wizard running Bash commands and writing files? (Yes / Walk me through each one)

If Cookidoo+ is "No," stop and explain that the entire skill is built on the Cookidoo API; without a subscription, almost none of the tools work. Offer to continue anyway in degraded mode (paste-the-URL only) but warn that it's much less useful.

## Phase 1 — Find a working Python 3.11+

Run these Bash commands in parallel to detect candidate Python binaries.

**macOS / Linux / Git Bash / WSL:**
```bash
pwd
python3 --version 2>&1
which -a python3 python3.11 python3.12 python3.13 2>&1 || true
ls /opt/homebrew/bin/python3.* 2>/dev/null || true
ls /usr/local/bin/python3.* 2>/dev/null || true
```

**Native Windows (PowerShell):**
```powershell
Get-Location
py -3 --version 2>&1
py -0   # lists all installed Python versions
where.exe python python3 python3.11 python3.12 python3.13 2>&1
```

From the output, pick the highest-version Python ≥ 3.11. Common cases:
- macOS with Homebrew: `/opt/homebrew/bin/python3.12` (or `.11`/`.13`)
- macOS without Homebrew: only `/usr/bin/python3` which is usually 3.9 — **stop and tell the user to install Python 3.12 with `brew install python@3.12`** or via [pyenv](https://github.com/pyenv/pyenv). Then ask them to re-run `/meal-plan-setup`.
- Linux: usually `/usr/bin/python3.11` or higher
- WSL2: `/usr/bin/python3` is often 3.10; `sudo apt install python3.12 python3.12-venv`
- Windows with Python launcher: `py -3.12` invokes the right binary; if no 3.11+ is installed, **stop and tell the user to install from [python.org](https://www.python.org/downloads/) or via `winget install Python.Python.3.12`**, then re-run.
- If `python3 --version` (or `py -3 --version`) shows ≥ 3.11, that's fine to use

**Save the chosen binary path** as `PY` for the rest of the wizard. On Windows-native, `PY` may be `py -3.12` (a launcher invocation, not a path). Tell the user which one you picked and why.

Save the repo root (output of `pwd` / `Get-Location`) as `REPO`. On Windows, normalize backslashes to forward slashes for the rest of the wizard — Python and JSON both accept forward slashes on Windows, and it avoids escaping headaches.

## Phase 2 — Install the MCP

Tell the user this takes 30-60 seconds. Venv layout differs by platform — on Unix the binaries live in `.venv/bin/`, on Windows they live in `.venv/Scripts/` with `.exe` extensions.

**macOS / Linux / Git Bash / WSL:**
```bash
$PY -m venv $REPO/cookidoo-mcp/.venv
$REPO/cookidoo-mcp/.venv/bin/pip install --quiet -r $REPO/cookidoo-mcp/requirements.lock
cd $REPO/cookidoo-mcp && .venv/bin/python -c "import server; print('IMPORT OK')"
```

**Native Windows (PowerShell):**
```powershell
& $PY -m venv "$REPO/cookidoo-mcp/.venv"
& "$REPO/cookidoo-mcp/.venv/Scripts/pip.exe" install --quiet -r "$REPO/cookidoo-mcp/requirements.lock"
Set-Location "$REPO/cookidoo-mcp"; & ".venv/Scripts/python.exe" -c "import server; print('IMPORT OK')"
```

(The smoke-test step needs to `cd`/`Set-Location` because `server.py` isn't on the Python path otherwise — chain it as a single shell call so the directory change takes effect.)

**Save the venv binary directory** as `VENV_BIN` for the rest of the wizard:
- Unix: `VENV_BIN=$REPO/cookidoo-mcp/.venv/bin`
- Windows: `VENV_BIN=$REPO/cookidoo-mcp/.venv/Scripts`

Save whether the platform needs `.exe` suffixes as `EXE` (`""` on Unix, `".exe"` on Windows). You'll use these in `.mcp.json` later.

If pip fails:
- Network error → ask user to retry
- Python build error on macOS → `xcode-select --install`
- Python build error on Linux → install build tools (`sudo apt install build-essential python3-dev` or equivalent)
- Python build error on Windows → install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- `ensurepip is not available` on Linux → `sudo apt install python3.12-venv` (match version)
- Anything else → surface the exact error and stop

## Phase 3 — Cookidoo credentials

Use AskUserQuestion to collect, in one batch:
- Cookidoo email
- Cookidoo password (note: stored locally in a config dir outside the repo, restricted permissions, never committed, never logged)
- Country code (default: `us` — common: `us`, `gb`, `de`, `es`, `fr`, `ar`)
- Language (default: `en-US` — match country: `en-US`, `en-GB`, `de-DE`, `es-ES`, `fr-FR`, `es-AR`)

**Best approach: use the Write tool, not shell heredoc.** Heredocs have shell-escaping pitfalls (passwords with `$`, backticks, single quotes). Write tool sidesteps all of that.

Determine the env file path by platform:
- macOS / Linux / Git Bash / WSL: `~/.config/cookidoo-mcp/.env` (resolve `~` via the `HOME` env var)
- Native Windows: `$env:USERPROFILE\.config\cookidoo-mcp\.env` (use the `USERPROFILE` env var)

Save this as `ENV_FILE` for the rest of the wizard.

**Step 1 — create the directory:**

Unix / Git Bash / WSL:
```bash
mkdir -p "$(dirname $ENV_FILE)"
```

Windows PowerShell:
```powershell
New-Item -ItemType Directory -Force -Path (Split-Path $ENV_FILE)
```

**Step 2 — write the env file using the Write tool** with this literal content (substituting the user's actual values for the four placeholders — do NOT write the literal placeholder strings):

```
COOKIDOO_EMAIL=<user's email>
COOKIDOO_PASSWORD=<user's password>
COOKIDOO_COUNTRY=<user's country>
COOKIDOO_LANGUAGE=<user's language>
```

The Write tool takes the absolute path; pass the resolved `ENV_FILE` value.

**Step 3 — restrict permissions:**

Unix / Git Bash / WSL:
```bash
chmod 600 $ENV_FILE
ls -la $ENV_FILE   # should show -rw-------
```

Windows PowerShell (uses icacls to remove Inherited and grant only the current user):
```powershell
icacls $ENV_FILE /inheritance:r /grant:r "$env:USERNAME:(R,W)"
icacls $ENV_FILE   # verify only current user has rights
```

Do **not** echo the file contents, ever. After verification, confirm with the user that the file exists at the right path. Do not print the password back.

## Phase 4 — Register the MCP with Claude Code

Read `$REPO/.mcp.json.example`. The template uses `.venv/bin/python` (Unix-style), but on Windows the venv binary lives at `.venv/Scripts/python.exe`. Use Write to create `$REPO/.mcp.json` substituting:

- `{{REPO_ABSOLUTE_PATH}}` → the actual `$REPO` value (use forward slashes even on Windows — JSON and Python both handle them fine and it avoids escaping)
- The `command` path:
  - Unix: `$REPO/cookidoo-mcp/.venv/bin/python`
  - Windows: `$REPO/cookidoo-mcp/.venv/Scripts/python.exe`

Example final `.mcp.json` on macOS:
```json
{
  "mcpServers": {
    "cookidoo": {
      "command": "/Users/me/projects/thermomix_meal_prep/cookidoo-mcp/.venv/bin/python",
      "args": ["/Users/me/projects/thermomix_meal_prep/cookidoo-mcp/server.py"]
    }
  }
}
```

Example on Windows:
```json
{
  "mcpServers": {
    "cookidoo": {
      "command": "C:/Users/me/projects/thermomix_meal_prep/cookidoo-mcp/.venv/Scripts/python.exe",
      "args": ["C:/Users/me/projects/thermomix_meal_prep/cookidoo-mcp/server.py"]
    }
  }
}
```

Show the user the resulting `.mcp.json` contents so they can verify the paths look right.

Tell the user: **"Quit Claude Code completely and re-launch it from this same repo directory. On macOS that's Cmd-Q then `cd <repo> && claude`. On Windows that's closing the Claude Code window and running `claude` again from the repo directory in your terminal. On first use of the Cookidoo MCP, Claude Code will ask you to approve the new server — that's a security check, approve it."**

Stop here. The user will re-run `/meal-plan-setup` after restart, and the wizard's re-run logic (described below) will skip Phases 1-4 and pick up at Phase 5.

## Phase 5 — Smoke test the MCP (after restart)

Try calling `mcp__cookidoo__whoami`. Three outcomes:

- **Works** — print the user info and subscription expiry. Confirm the email matches what they entered. Move on.
- **MCP not loaded / tool not found** — they didn't restart Claude Code, or Claude Code didn't pick up `.mcp.json`. Tell them to fully quit (not just close the window) and relaunch from the repo root.
- **Auth error** — credentials are wrong. Read `~/.config/cookidoo-mcp/.env` (don't print the password to chat, just confirm the file exists and is readable). If the user wants to fix it, walk back to Phase 3 and rewrite the file.
- **Localization error** — country/language combo isn't supported by the underlying library. Default to `us`/`en-US` to confirm the rest works, then narrow down.

## Phase 6 — Fill the persona

Use Read to load `$REPO/personas/family-meal-planning.template.md`. Then walk the user through filling each `{{PLACEHOLDER}}` using AskUserQuestion in batches of up to 4. Group:

**Batch 1 — Household (4 questions):**
- Who's in the household? (free text — names/ages optional, roles like "primary cook" / "tough eater" / "pregnant" useful)
- Primary language for recipe titles? (English / Spanish / German / French / Italian / Other)
- Any cultural cuisine preferences? (free text — e.g., "Mediterranean", "Argentine", "no preference")
- Where do you live? (city + country, used for store grouping context)

**Batch 2 — Constraints (multiSelect):**
- Which dietary constraints apply? (Toddler-friendly with choking-hazard flags / Pregnancy-safe / Vegetarian / Vegan / Pescatarian / Gluten-free / Specific allergies / Religious or cultural rules / None)

For each one selected, follow up with the specifics in another batch (e.g., for allergies: "List them"; for pregnancy: "Through what date").

**Batch 3 — Logistics (4 questions):**
- Primary grocery store? (free text — drives shopping list grouping)
- Secondary store for bulk? (Costco / Sam's / BJ's / Other / None)
- Default shopping day? (e.g., Sunday / Saturday / Wednesday)
- Default cooking days for the week? (e.g., "Mon-Thu plus one weekend showcase")

**Batch 4 — Equipment + Output (4 questions):**
- Thermomix model? (confirm from preflight)
- Other relevant appliances? (oven, sous vide, pressure cooker, pizza stone, etc.)
- Output location? (default `outputs/meal-plan/` — confirm or change)
- Voice guidance? (Default: direct, conversational, no AI clichés / Custom — describe)

After all batches, use Write to save the filled persona to `$REPO/personas/family-meal-planning.md`. Build the file content by taking the template and substituting each placeholder with the user's answers. **Do not** save the unfilled template — the gitignore depends on this filename being `family-meal-planning.md`, not `family-meal-planning.template.md`.

Show the user a summary of what was filled in (not the full file — that's long). Ask if they want to edit anything before continuing.

## Phase 7 — Bootstrap the custom collections list

Tell the user: "Now I'll pull your Cookidoo custom collections and add them to your persona so the planner knows what to draw from."

Call `mcp__cookidoo__list_my_collections(kind="custom")`. Use Edit to replace the `{{COOKIDOO_COLLECTIONS}}` block in `$REPO/personas/family-meal-planning.md` with a formatted list of the user's actual collections (name + recipe count).

If the user has zero custom collections, tell them they can create some in the Cookidoo app and re-run this phase later by asking you to "refresh my custom collections in the persona."

## Phase 8 — Done

Tell the user:
1. Setup is complete.
2. Run `/meal-plan` any time to generate a weekly plan. The first run will have no prior weeks of feedback to learn from, so the plan will be more generic — that improves over the first 4-6 weeks.
3. Where their files are now:
   - Persona: `personas/family-meal-planning.md` (gitignored — yours alone)
   - Credentials: the env file you created in Phase 3 (outside the repo, restricted permissions)
   - MCP config: `$REPO/.mcp.json` (gitignored, machine-specific)
   - Future plans: their chosen output location

## Re-run logic

This wizard is safe to re-run. At the start, check what already exists and skip phases that are done. Use platform-appropriate file existence checks:

- venv exists (`.venv/bin/python` on Unix, `.venv/Scripts/python.exe` on Windows) and the import smoke test passes → Phase 1-2 done, skip
- env file exists at the platform-appropriate path → ask user if they want to keep or replace credentials
- `.mcp.json` exists at repo root → Phase 4 done, skip (but offer to re-create if paths look stale or platform changed)
- `personas/family-meal-planning.md` exists → ask user if they want to keep, edit, or fully refill
- `mcp__cookidoo__whoami` works → Phase 5 done, skip

Always finish by reminding the user how to run `/meal-plan`.
