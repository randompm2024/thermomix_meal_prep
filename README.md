# Thermomix Meal Prep

A weekly Thermomix dinner planner powered by Claude Code, your Cookidoo collections, and a household persona file you customize once.

Run `/meal-plan` and you get four dinners for the week — one optional showcase plus three weeknight cooks capped at 30-40 minutes active time, each with a faster fallback. Source-balanced across your custom collections, Vorwerk-curated popular recipes, and the public Cookidoo explore page. Auto-grouped shopping list. Reads the previous two weeks from your Cookidoo calendar so it doesn't propose the same thing twice. Learns from your weekly feedback over time.

## Demo

See [examples/weekly-meal-plan.example.md](examples/weekly-meal-plan.example.md) for what the planner produces. The fictional Garcia family is vegetarian with a peanut allergy and two picky kids.

## Prerequisites

You need all four of these before starting. The wizard will check for #4 but you have to handle #1-3 yourself.

1. **A Cookidoo+ subscription.** The whole skill is built on the Cookidoo API; without it, almost nothing works. Get one at [cookidoo.thermomix.com](https://cookidoo.thermomix.com).
2. **A Thermomix.** TM5/TM6/TM7 all fine. TM7-specific features get called out when relevant.
3. **Claude Code installed.** Install instructions at [claude.com/claude-code](https://claude.com/claude-code). After install, `claude --version` should work in your terminal.
4. **Python 3.11 or newer.** Check with `python3 --version` (or `py -3 --version` on Windows). If yours is older (macOS ships with 3.9), install a newer one:
   - macOS: `brew install python@3.12` (install Homebrew first if you don't have it: [brew.sh](https://brew.sh))
   - Linux: use your package manager (`apt install python3.12`, `dnf install python3.12`, etc.) or [pyenv](https://github.com/pyenv/pyenv)
   - Windows: `winget install Python.Python.3.12` or [python.org downloads](https://www.python.org/downloads/)

### Windows users — read this first

The setup wizard uses Unix-style shell commands (heredocs, chmod, `~`-expansion). Two paths that work:

- **Recommended: WSL2 (Windows Subsystem for Linux).** Install via `wsl --install` from PowerShell, then run everything inside the WSL Ubuntu terminal. Treats your machine as Linux for setup purposes — the wizard's default Unix commands work as-is. Install instructions: [learn.microsoft.com/wsl/install](https://learn.microsoft.com/en-us/windows/wsl/install).
- **Also works: Git Bash.** Comes free with [Git for Windows](https://git-scm.com/download/win). Provides a Unix-style shell on top of Windows. The wizard detects Git Bash and uses Unix commands.

Native cmd / PowerShell setup is partially supported by the wizard (it detects platform and falls back to PowerShell-friendly commands where it can), but it's untested. If you're on PowerShell and hit issues, switching to Git Bash is the fastest fix — it's a 5-minute install.

## Quick start

Open a terminal:

```
git clone https://github.com/randompm2024/thermomix_meal_prep.git
cd thermomix_meal_prep
claude
```

That last command launches Claude Code in this directory. Once it's open, type:

```
/meal-plan-setup
```

The wizard takes about 5 minutes. It will:
- Find a working Python 3.11+ on your machine and tell you which one it picked
- Install the local Cookidoo MCP (Python venv + dependencies)
- Ask for your Cookidoo email and password (stored locally at `~/.config/cookidoo-mcp/.env`, chmod 600, never committed, never sent anywhere except your local MCP)
- Walk you through filling the household persona — household members, dietary constraints, primary store, kitchen equipment, output location
- Drop a `.mcp.json` so Claude Code auto-loads the MCP
- Verify the MCP works end-to-end

**You'll see permission prompts.** Each Bash command, file write, and MCP call needs your approval the first time. Approve them. After Claude Code registers the MCP, it'll also ask you to approve the new MCP server itself — that's normal, approve it.

After setup, restart Claude Code (Cmd-Q and relaunch on macOS, or quit/relaunch the terminal session). Then in a fresh Claude Code session in this same directory:

```
/meal-plan
```

You'll get a plan for the week.

## What's in here

```
.claude/
  skills/meal-plan/SKILL.md             # the planner skill
  commands/meal-plan-setup.md           # one-time setup wizard (run this first)
  settings.example.json                 # recommended permission allowlist
cookidoo-mcp/                           # local read-only MCP server (Python)
  server.py
  requirements.lock
  README.md
personas/
  family-meal-planning.template.md      # household template (yours stays gitignored)
examples/
  persona-filled.example.md             # fictional Garcia family
  weekly-meal-plan.example.md           # sample plan output
docs/
  cookidoo-mcp-setup.md                 # manual MCP install if wizard breaks
  customizing-the-persona.md            # editing the persona over time
  troubleshooting.md                    # common errors and fixes
  other-ai-tools.md                     # Cursor/Aider/etc. usage
.mcp.json.example                       # MCP registration template
```

## What gets created on your machine after setup

- `personas/family-meal-planning.md` — your filled persona (gitignored, yours alone)
- `~/.config/cookidoo-mcp/.env` — your Cookidoo credentials (chmod 600, outside the repo)
- `cookidoo-mcp/.venv/` — Python venv with MCP dependencies (gitignored)
- `.mcp.json` — Claude Code MCP registration with absolute paths (gitignored, machine-specific)

Nothing personal ever gets committed back to the repo.

## Troubleshooting

If the wizard breaks or `/meal-plan` doesn't work, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Customizing the persona

After setup, edit `personas/family-meal-planning.md` directly any time — change the dietary constraints, add new collections, update the rolling taste model with what flopped this week. See [docs/customizing-the-persona.md](docs/customizing-the-persona.md).

## Using outside Claude Code

The skill and persona are plain markdown. Cursor, Aider, Codex, and similar tools can use them. The Cookidoo MCP follows the standard MCP spec and works with any MCP-compatible client. See [docs/other-ai-tools.md](docs/other-ai-tools.md).

## Privacy

- Cookidoo credentials live in `~/.config/cookidoo-mcp/.env` (chmod 600, outside the repo, never synced to a cloud folder if you keep your home dir local).
- The MCP is read-only — it can't post, edit, or delete anything in your Cookidoo account.
- Your filled persona and generated meal plans are gitignored by default.
- The Cookidoo API the MCP wraps is unofficial and can break with any frontend change. If a tool starts failing, drop into degraded mode (paste-the-URL) and check the upstream library for updates.

## Credits

- Cookidoo MCP built on [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api).
- Replaces the [alexandrepa/mcp-cookidoo](https://github.com/alexandrepa/mcp-cookidoo) community version with a tighter, read-only, TLS-verified implementation.
- Built for [Claude Code](https://claude.com/claude-code).

## License

MIT. See [LICENSE](LICENSE).
