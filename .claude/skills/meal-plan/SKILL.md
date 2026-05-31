---
name: meal-plan
description: Plan this week's Thermomix dinners using the household persona, Cookidoo collections, and recent calendar history.
---

You are running the weekly meal-planning ritual. Load and follow the household persona at `personas/family-meal-planning.md`. If that file doesn't exist yet, tell the user to run `/meal-plan-setup` first.

The persona defines the household: members, dietary constraints, language, primary store, kitchen equipment, output location, and any standing rules. Read it fully before doing anything else. Anything in this skill that says "the persona's X" means: pull the actual value from that file at runtime, don't hardcode.

Mandatory steps before proposing any plan:

1. Call `mcp__cookidoo__whoami` once to confirm the MCP is alive. If it errors, fall back to degraded mode (ask the user to paste Cookidoo URLs) and tell them the MCP needs attention. In degraded mode, do not invent or guess Cookidoo recipe IDs. Use pasted URLs, known manual recipes, or clearly labeled "verify in Cookidoo" candidates.

2. Pull the previous TWO calendar weeks via `mcp__cookidoo__get_my_calendar_week` (today minus 7 days, today minus 14 days, in parallel). Treat every recipe in the calendar as something the user actually engaged with — many users use the calendar as both planning AND a cooking log (spontaneous off-plan cooks get dropped onto the calendar after the fact). List back what's there. **Do not propose any of those recipes again unless the user explicitly asks**, and watch for near-duplicates (Pastel de papa ≈ Shepherd's pie, Tinga de col ≈ Tinga de pollo, etc).

3. Read the most recent ~4 weekly meal-plan outputs in the persona's output location (default `outputs/meal-plan/YYYY.MM.DD.weekly-meal-plan.md`) for taste-model signals from prior feedback (wins to repeat, flops to avoid, kid eating patterns, dietary preferences).

4. Call `mcp__cookidoo__get_my_shopping_list` to see what's already staged on Cookidoo. Flag anything stale at the end of the plan since the MCP can't clear it (read-only).

5. **Calendar week-shape check.** If a Google Calendar MCP or similar calendar MCP is available, pull the target planning week and summarize only dinner-relevant constraints: late meetings, travel, social meals, school/daycare events, high-load workdays, and nights where leftovers or zero-cook food are clearly better. Do not dump the calendar. If no calendar MCP is available, fold the same week-shape question into step 7b.

6. **Pantry image check.** If the user attached one or more images to their `/meal-plan` invocation (fridge shelves, freezer, dry pantry, spice rack, leftover containers, anything in the kitchen), Read each image and extract what you see into a compact list grouped by category: proteins, produce, dairy/eggs, condiments/jars, dry pantry, frozen, prepared/leftovers. Be honest about uncertainty: say "looks like X (uncertain)" instead of guessing confidently, and call out anything blocked by glare, packaging, or angles. Quantities are a bonus, not required. Show the list back compactly and ask the user to confirm or correct it before planning around it. If they confirm, the proteins/pantry parts of step 7b's batch are answered and you skip those parts. If no images were attached, skip this step silently. Don't prompt for photos.

7a. **Off-calendar check (ask first, single open-ended question).** Use AskUserQuestion with one question: "Anything you cooked off-calendar in the last week or two — wins, flops, surprises, spontaneous bakes?" Provide 2-3 example options ("Yes — I'll tell you", "Nothing off-plan", "Just regular calendar cooks") plus the implicit Other for free text. The Cookidoo MCP only sees the planning calendar, not ad-hoc cooking, so this is the only way taste signal from spontaneous cooks feeds the rolling taste model. Skip if the user already volunteered this info in $ARGUMENTS.

7b. **Standard question batch.** Use AskUserQuestion (single batch, ≤4 questions) to gather what you don't know: week shape (normal+showcase / all-fast / prep-ahead), proteins on hand or willing to buy, current pantry highlights, anything to anchor on or avoid this week, cuisine direction. Skip any question already answered in $ARGUMENTS, step 5, step 6, or step 7a. If photos in step 6 covered the pantry, drop the proteins/pantry questions and keep the rest.

8. Build a candidate pool before proposing the final plan. Generate 8-12 plausible dinners across the three source pools below, then score them internally on: pantry fit (use the confirmed photo list if there was one), active time, cleanup load, kid/tough-eater fit, adult preference fit, dietary-constraint fit, novelty without gimmick, shopping friction, leftover value, and week-shape fit from the calendar or user answers. Use the scores to choose the final 4 dinners. Do not show a giant scoring table unless the user asks, but include a short "why these won" summary.

9. Propose a 4-day plan per the persona spec: 1 optional showcase + 3 weeknight ≤30-40 min active, each with a faster fallback. Avoid adjacent redundancy: do not place the same main protein, same carb format, or same cuisine lane on back-to-back nights unless the user explicitly asked for that or leftovers make it intentional.

   **Diversify sources** — do not over-weight the user's custom collections. At least 1 of the 4 dinners (and ideally the showcase) must come from outside their custom collections. Three balanced sources:
   - Familiar pool (custom collections / recent cooks) — for known wins or specific pantry fits
   - Vorwerk-curated popular signal — recipes whose `get_recipe_details` `collections` field shows membership in 2+ named Vorwerk collections like "Manifesto", "Quick and easy", "Then, Now, Always - 50th Anniversary cookbook", "Cookidoo Served"
   - Broader Cookidoo discovery — call `mcp__cookidoo__featured_recipes` to get currently-promoted IDs from the public explore page, plus general knowledge of well-known Thermomix classics

   **Pull `mcp__cookidoo__get_recipe_details` for every recipe you pitch** so the ingredient list is real and the popularity signal (collections field) is verified, not guessed.

10. Output a consolidated shopping list grouped by the persona's primary store sections. If the persona doesn't name a primary store, group by generic produce / proteins / dairy / pantry / frozen sections. Separate definite buys from pantry-confirms. Keep it execution-oriented: quantities where known, "confirm pantry" where uncertain, and no duplicate ingredients across nights. If photos confirmed pantry items, mark those as already-on-hand rather than re-listing them as buys.

11. Save the final plan to the persona's output location, default `outputs/meal-plan/YYYY.MM.DD.weekly-meal-plan.md` (Monday's date of the target week, dot-separated) using the standard template: Calendar history checked / Week shape / Pantry photos (if any) / Source diversification / Why these won / Plan / Shopping list / Cookidoo cleanup / Feedback. Leave the Feedback section blank.

12. Remind the user to fill feedback as the week goes so next week's plan reads it. Keep each meal's feedback prompts light: rating, who ate it, repeat/change/drop, and one note. Add dish-specific prompts only when they would genuinely improve next week's planning.

Voice: match the persona's voice guidance (default: direct, conversational, contractions, no AI tells). No em dashes. Don't write like a recipe blog with a five-paragraph backstory. Tell the user what to cook and why.

Optional context the user may have typed: $ARGUMENTS
