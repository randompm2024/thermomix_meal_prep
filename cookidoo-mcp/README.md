# cookidoo-mcp (read-only)

Thin local MCP server that wraps [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api) and exposes only read tools to Claude Code.

## Why this exists

A community MCP at `alexandrepa/mcp-cookidoo` had `verify_ssl=False`, hardcoded French locale, and exposed write tools by default. This is a ~100-line replacement that keeps TLS verification on, reads localization from env, and only exposes read endpoints. If you bump dependencies or add tools, re-audit before shipping.

## Tools exposed

- `whoami` — user info + active subscription (smoke test)
- `get_recipe_details(recipe_id)` — full recipe by ID like `r59322`
- `list_my_collections(kind, page)` — `kind` is `managed`, `custom`, or `all`
- `get_my_calendar_week(any_day_in_week)` — ISO date string, returns the planned week
- `get_my_shopping_list` — current shopping list (recipes + ingredient items + additional items)
- `featured_recipes(limit)` — scrape the public explore page for currently-promoted recipe IDs and hydrate them
- `browse_managed_collection(collection_id)` — peek inside a Vorwerk-curated collection (uses a temporary add-then-remove if not already saved; cleanup is best-effort)

No long-term write tools. To add real writes later, expose them explicitly in `server.py` and re-audit.

## Setup

The `/meal-plan-setup` slash command does this automatically. Manual steps if you want them:

1. Create a venv and install deps:
   ```
   cd cookidoo-mcp
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.lock
   ```
2. Create `~/.config/cookidoo-mcp/.env` (chmod 600):
   ```
   COOKIDOO_EMAIL=you@example.com
   COOKIDOO_PASSWORD=your-cookidoo-password
   COOKIDOO_COUNTRY=us
   COOKIDOO_LANGUAGE=en-US
   ```
3. Smoke test:
   ```
   .venv/bin/python server.py
   ```
   (It should start and wait for MCP traffic. Ctrl-C to exit.)
4. Register with Claude Code via `.mcp.json` at the project root, or via your global `~/.claude.json` `mcpServers.cookidoo` entry. See `../.mcp.json.example`.

## Maintenance

- Pinned deps in `requirements.lock`. The underlying `cookidoo-api` is unofficial and can break with any Cookidoo frontend change.
- TLS verification is on (aiohttp default). Don't disable it.
- Credentials never logged or returned by tools. Keep the env file at chmod 600 and outside any cloud-synced folder.
- If a tool call fails with auth or parsing errors, drop into degraded mode (paste-the-URL) and re-check the upstream library.

## Credits

- Built on [miaucl/cookidoo-api](https://github.com/miaucl/cookidoo-api).
- MCP wrapper authored for this repo. MIT licensed.
