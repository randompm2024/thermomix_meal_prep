# Cookidoo MCP setup

The `/meal-plan-setup` wizard handles all of this. This doc is for if you want to do it manually, debug a broken setup, or understand what's running on your machine.

## What the MCP is

A ~270-line Python script at `cookidoo-mcp/server.py` that wraps [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api) and exposes it to Claude Code via the [Model Context Protocol](https://modelcontextprotocol.io). Read-only by design — none of the exposed tools can modify your Cookidoo account.

## Why this exists vs. existing alternatives

The community MCP at `alexandrepa/mcp-cookidoo` had three issues:
1. `verify_ssl=False` (silently disables TLS cert checks)
2. Hardcoded French locale
3. Exposed write tools by default (could mutate your account if Claude misfired)

This replacement keeps TLS on, reads localization from env, and only exposes reads.

## Manual install

```bash
cd cookidoo-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
```

Pip install takes 30-60 seconds. If it fails, the most common cause is Python < 3.11 — check `python3 --version`.

## Credentials

Create `~/.config/cookidoo-mcp/.env`:

```
COOKIDOO_EMAIL=you@example.com
COOKIDOO_PASSWORD=your-cookidoo-password
COOKIDOO_COUNTRY=us
COOKIDOO_LANGUAGE=en-US
```

```bash
chmod 600 ~/.config/cookidoo-mcp/.env
```

Country/language affect localization. Common values:
- US English: `us` / `en-US`
- UK English: `gb` / `en-GB`
- Germany: `de` / `de-DE`
- Spain: `es` / `es-ES`
- France: `fr` / `fr-FR`
- Argentina: `ar` / `es-AR`

If your country isn't supported by the underlying library, the MCP will error on startup with a localization message — try a closer locale.

## Register with Claude Code

Copy `.mcp.json.example` to `.mcp.json` in the repo root and substitute the absolute path:

```json
{
  "mcpServers": {
    "cookidoo": {
      "command": "/Users/you/path/to/thermomix_meal_prep/cookidoo-mcp/.venv/bin/python",
      "args": [
        "/Users/you/path/to/thermomix_meal_prep/cookidoo-mcp/server.py"
      ]
    }
  }
}
```

Restart Claude Code (or reload). On first MCP use, Claude Code asks you to approve the new server — it's a security check, approve it.

## Smoke test

In Claude Code:

```
Call mcp__cookidoo__whoami
```

You should see your user info and active subscription. If you don't:

- **"MCP not loaded"** — restart Claude Code. The `.mcp.json` only registers on launch.
- **Auth error** — re-check the email/password in your env file. Cookidoo passwords are case-sensitive.
- **Localization error** — your country/language combo isn't supported. Try `us` / `en-US` to confirm the rest works, then narrow down.
- **TLS error** — your system date may be off, or there's a corporate proxy intercepting HTTPS. Don't disable TLS verification to work around this.

## Tools exposed

All prefixed `mcp__cookidoo__`:

| Tool | Returns | Use when |
|---|---|---|
| `whoami` | user + subscription | smoke test |
| `get_recipe_details(id)` | full recipe by ID like `r59322` | every recipe you pitch |
| `list_my_collections(kind, page)` | your custom and managed collections | initial persona fill, occasional refresh |
| `get_my_calendar_week(date)` | planned recipes for the week of that date | every planning session (last 2 weeks) |
| `get_my_shopping_list` | current shopping list | every planning session, to flag stale items |
| `featured_recipes(limit)` | currently-promoted recipes from explore | source diversification |
| `browse_managed_collection(id)` | contents of a Vorwerk collection | exploring collections you haven't saved |

## Maintenance

- The underlying `cookidoo-api` library is unofficial. Cookidoo can change their frontend at any time and break tools. Re-install with `pip install -r requirements.lock --upgrade` periodically, or pin a newer cookidoo-api version explicitly.
- If you bump deps or add new tools to `server.py`, re-audit before sharing changes.
- Credentials are read on first tool call, not at startup. The env file can be rotated without restarting Claude Code (next call picks up new values).

## Adding write tools (don't, unless you mean it)

The MCP intentionally doesn't expose write endpoints. The underlying library supports adding recipes to the calendar, modifying the shopping list, etc. If you want to add them, edit `server.py` directly — but understand that Claude could then mutate your Cookidoo account, including deleting your custom collections, adding the wrong week of recipes, etc. At minimum, gate write tools behind a separate confirmation prompt.
