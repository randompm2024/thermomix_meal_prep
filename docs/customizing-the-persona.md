# Customizing the persona

The persona file at `personas/family-meal-planning.md` is where every household-specific decision lives. The `/meal-plan` skill reads it on every run, so editing the persona changes how the planner behaves the very next time you run it. No restart required.

## What's in the persona

Two big sections:

**Project Instructions** — how the planner should behave. The ritual (call calendar first, ask off-calendar question, then standard 4-question batch, then propose). Source diversification rules. Output format for each recipe. Voice guidance.

**Memory** — facts about your household. Family setup, Cookidoo account, custom collections, dietary constraints, the rolling taste model (wins / good-but-not-weekly / drop-entirely), equipment, output location.

## Common edits

### Updating the rolling taste model

This is the most useful ongoing edit. After 4-6 weeks of cooking, patterns emerge. Promote them from the weekly feedback files into the persona's Memory section so future plans pick them up automatically.

Three buckets — keep them separate:

- **Wins to repeat** — actively-liked dishes the household wants again
- **Good but not weekly** — solid dishes that get tired with frequency. Note rotation cadence (e.g. "every 3-4 weeks")
- **Drop entirely** — actual flops, technique misses, kid refusals

Don't conflate "didn't love it this time" with "drop it." A bad night can sour a dish that's actually fine — wait for the second data point.

### Adding new custom collections

When you create a new Cookidoo collection, refresh the persona's "Known custom collections" section. The fastest way:

```
Call mcp__cookidoo__list_my_collections with kind="custom" and paste the result into my persona under "Known custom collections"
```

Group collections by purpose so the planner knows when to pull from each one. Example:

> When planning, default to pulling weeknight options from `Weeknight wins`, `Pasta`, `Grain bowls`. Reserve the showcase slot for `Curries` or `Showstoppers`.

### Changing the time budget

The default is 30-40 min active weeknight time. If your reality is tighter (small kids, demanding job) or looser (working from home, no kids), edit the `Time budget` line and the `weeknight cap` mention in the dietary constraints.

### Adding constraints

New allergy, new pregnancy, new diet, new religious observance — add it to **both** the "Constraints to respect on every plan" block in Project Instructions AND the "Standing dietary constraints" block in Memory. They duplicate intentionally so the planner sees the constraint regardless of which section it reads first.

### Switching primary store

Change `{{PRIMARY_STORE}}` everywhere it appears (project instructions and memory). The planner uses this to group the shopping list by section. If you switch from Whole Foods to HEB to Costco, the section names change but the underlying logic doesn't.

## Voice tuning

The default voice is direct and conversational with no AI clichés. If you want something different — more playful, more terse, in another language — edit the `Voice` line in the project instructions. Example tweaks:

- *"Reply in Spanish. Recipe titles in their original language. No translation."*
- *"Keep it under 15 lines per plan. I'll ask if I want more detail."*
- *"Use casual French throughout. Tu, not vous."*

## What NOT to do

- Don't put credentials in the persona file. The MCP reads them from env. The persona is just a markdown file that any AI can see — credentials in there leak.
- Don't list specific recipe IDs as "always pick these." The taste model bucket is the right place — IDs go stale when Cookidoo refreshes their catalog.
- Don't try to make the persona do what the skill should do. If you find yourself writing "always pull the calendar week first," that belongs in the SKILL.md (and is already there). The persona is for household facts, not workflow.

## Resetting

If your persona gets messy after months of edits, delete `personas/family-meal-planning.md` and run `/meal-plan-setup` again. The wizard will walk you through filling a fresh copy from the template, and you can copy over any sections you want to keep (especially the rolling taste model, which represents real cooking history).
