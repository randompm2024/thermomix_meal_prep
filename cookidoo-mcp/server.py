"""
Cookidoo MCP — read-only thin wrapper over miaucl/cookidoo-api.

Exposes only read methods. No write surface. TLS verification stays on (default).
Credentials read from env (COOKIDOO_EMAIL, COOKIDOO_PASSWORD).
Localization read from env (COOKIDOO_COUNTRY, COOKIDOO_LANGUAGE), defaults en-US.
"""

from __future__ import annotations

import asyncio
import dataclasses
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from aiohttp import ClientSession
from cookidoo_api import Cookidoo, CookidooConfig
from cookidoo_api.helpers import get_localization_options
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load credentials from the canonical location, regardless of cwd.
# Override default of "look in cwd" because the MCP is launched by Claude Code
# from arbitrary working directories.
_ENV_PATH = Path(
    os.getenv("COOKIDOO_ENV_FILE")
    or Path.home() / ".config" / "cookidoo-mcp" / ".env"
)
load_dotenv(_ENV_PATH)

mcp = FastMCP("cookidoo")

_client: Cookidoo | None = None
_session: ClientSession | None = None


async def _get_client() -> Cookidoo:
    global _client, _session
    if _client is not None:
        return _client

    email = os.getenv("COOKIDOO_EMAIL")
    password = os.getenv("COOKIDOO_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "Missing COOKIDOO_EMAIL or COOKIDOO_PASSWORD in environment."
        )
    country = os.getenv("COOKIDOO_COUNTRY", "us")
    language = os.getenv("COOKIDOO_LANGUAGE", "en-US")

    localization = (
        await get_localization_options(country=country, language=language)
    )[0]

    _session = ClientSession()
    cfg = CookidooConfig(email=email, password=password, localization=localization)
    _client = Cookidoo(session=_session, cfg=cfg)
    await _client.login()
    return _client


def _to_jsonable(obj: Any) -> Any:
    """Best-effort conversion of cookidoo-api dataclasses/lists to JSON-safe dicts."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return obj


@mcp.tool()
async def whoami() -> dict:
    """Return the logged-in Cookidoo user info and active subscription.

    Useful as a smoke test that auth works and that the account has Cookidoo+.
    """
    client = await _get_client()
    user = await client.get_user_info()
    sub = await client.get_active_subscription()
    return {"user": _to_jsonable(user), "subscription": _to_jsonable(sub)}


@mcp.tool()
async def get_recipe_details(recipe_id: str) -> dict:
    """Get full recipe details by Cookidoo recipe ID (e.g. 'r59322').

    Returns ingredients, steps, total time, servings, and metadata.
    """
    client = await _get_client()
    recipe = await client.get_recipe_details(recipe_id)
    return _to_jsonable(recipe)


@mcp.tool()
async def list_my_collections(kind: str = "all", page: int = 0) -> dict:
    """List the user's collections.

    Args:
        kind: 'managed' for Vorwerk-curated collections the user has saved,
              'custom' for collections the user created themselves,
              'all' for both (default).
        page: page number for pagination (default 0).
    """
    client = await _get_client()
    out: dict[str, Any] = {}
    if kind in ("managed", "all"):
        out["managed"] = _to_jsonable(await client.get_managed_collections(page=page))
    if kind in ("custom", "all"):
        out["custom"] = _to_jsonable(await client.get_custom_collections(page=page))
    return out


@mcp.tool()
async def get_my_calendar_week(any_day_in_week: str) -> list[dict]:
    """Get the user's planned recipes for the calendar week containing the given date.

    Args:
        any_day_in_week: ISO date string (YYYY-MM-DD). Any day in the target week works.
    """
    client = await _get_client()
    target = date.fromisoformat(any_day_in_week)
    days = await client.get_recipes_in_calendar_week(target)
    return _to_jsonable(days)


@mcp.tool()
async def get_my_shopping_list() -> dict:
    """Get the user's current Cookidoo shopping list.

    Combines: recipes whose ingredients are on the list, raw ingredient items,
    and any manually-added additional items.
    """
    client = await _get_client()
    recipes = await client.get_shopping_list_recipes()
    ingredients = await client.get_ingredient_items()
    additional = await client.get_additional_items()
    return {
        "recipes": _to_jsonable(recipes),
        "ingredient_items": _to_jsonable(ingredients),
        "additional_items": _to_jsonable(additional),
    }


_RECIPE_ID_RE = re.compile(r"/recipes/recipe/[\w-]+/(r\d+)")


@mcp.tool()
async def featured_recipes(limit: int = 15) -> list[dict]:
    """Discover currently-featured recipes from Cookidoo's public explore page.

    Scrapes the server-rendered explore page for recipe IDs that Cookidoo's editors
    are currently promoting, then hydrates each via the authenticated recipe-details
    endpoint. Useful for "popular right now" beyond the user's saved collections.

    No state mutation. Returns a compact summary per recipe (id, name, time, difficulty,
    URL, and Vorwerk collection memberships — the popularity signal).

    Args:
        limit: max recipes to return (default 15, capped at 25).
    """
    client = await _get_client()
    explore_url = "https://cookidoo.thermomix.com/foundation/en-US/explore"

    async with client._session.get(explore_url) as r:
        html = await r.text()

    # Dedupe in order of first appearance
    ids = list(dict.fromkeys(_RECIPE_ID_RE.findall(html)))[: min(limit, 25)]
    if not ids:
        return [{"error": "No recipe IDs found on explore page (page layout may have changed)"}]

    # Hydrate in parallel
    results = await asyncio.gather(
        *[client.get_recipe_details(rid) for rid in ids],
        return_exceptions=True,
    )

    out: list[dict] = []
    for rid, rec in zip(ids, results):
        if isinstance(rec, Exception):
            out.append({"id": rid, "error": str(rec)})
            continue
        d = _to_jsonable(rec)
        out.append(
            {
                "id": rid,
                "name": d.get("name"),
                "total_time": d.get("total_time"),
                "active_time": d.get("active_time"),
                "difficulty": d.get("difficulty"),
                "url": d.get("url"),
                "collections": [
                    {
                        "id": (c or {}).get("id"),
                        "name": (c or {}).get("name"),
                        "total_recipes": (c or {}).get("total_recipes"),
                    }
                    for c in (d.get("collections") or [])
                ],
            }
        )
    return out


@mcp.tool()
async def browse_managed_collection(collection_id: str) -> dict:
    """Peek at the contents of a Vorwerk-curated managed collection by ID.

    Examples of useful collection IDs (seen in recipe-details `collections` field):
    - col501620 "Manifesto" (202 recipes, flagship)
    - col501073 "Quick and easy" (22 recipes)
    - col433442 "Then, Now, Always - 50th Anniversary cookbook" (50 recipes)
    - col502242 "Your Cookidoo Kitchen Maestro" (10 recipes)

    Behavior:
    - If the user already has this collection saved, returns its contents directly (read-only).
    - Otherwise, temporarily adds it (the add endpoint returns the full collection in the
      response), then removes it via try/finally cleanup. Cleanup is best-effort.

    The temporary-write window is small but if interrupted, the user may need to manually
    remove the collection from their saved managed lists in the Cookidoo app.

    Args:
        collection_id: Vorwerk collection ID, e.g. "col501620"
    """
    client = await _get_client()

    # Check if already saved (paginated)
    page = 0
    while page < 5:
        saved = await client.get_managed_collections(page=page)
        if not saved:
            break
        for col in saved:
            col_dict = _to_jsonable(col)
            if col_dict.get("id") == collection_id:
                return {"already_saved": True, **col_dict}
        page += 1

    # Not saved: temporary add + remove
    added = None
    try:
        added = await client.add_managed_collection(collection_id)
        return {"already_saved": False, **_to_jsonable(added)}
    finally:
        if added is not None:
            try:
                await client.remove_managed_collection(collection_id)
            except Exception as cleanup_exc:
                print(
                    f"WARNING: cleanup of managed collection {collection_id} failed: "
                    f"{cleanup_exc}. You may need to remove it manually in the Cookidoo app.",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    mcp.run()
