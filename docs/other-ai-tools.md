# Using this outside Claude Code

The skill and persona are plain markdown. The Cookidoo MCP is a standard MCP server. Both work with other AI tools, with some adaptation.

## Cursor / Windsurf / Codex / similar IDE agents

These tools support custom system prompts and context files. The flow:

1. **Install the MCP the same way.** The Python venv setup and `~/.config/cookidoo-mcp/.env` credentials are identical to the Claude Code setup.

2. **Register the MCP with your tool.** Cursor uses `.cursor/mcp.json`, Windsurf has its own settings UI, Codex has a config flag. Use the same `command` + `args` from `.mcp.json.example` — substitute the absolute path to your `cookidoo-mcp/.venv/bin/python` and `cookidoo-mcp/server.py`.

3. **Use the SKILL.md as a system prompt.** Copy the contents of `.claude/skills/meal-plan/SKILL.md` into your tool's system-prompt field, or save it as a project-level instruction file. The skill references the persona by relative path, which works regardless of tool.

4. **Persona stays put.** Your filled `personas/family-meal-planning.md` is just a file the AI reads. As long as the AI has filesystem read access to the repo, the skill can load it.

5. **No `/meal-plan-setup` slash command in non-Claude tools.** You'll do the persona fill manually — copy `personas/family-meal-planning.template.md` to `personas/family-meal-planning.md` and replace the `{{PLACEHOLDERS}}` yourself. The example at `examples/persona-filled.example.md` shows what a finished one looks like.

## Aider / generic CLI agents

Aider and similar terminal-first tools can read the markdown files but don't natively support MCP servers (yet). Two options:

- **Run the MCP separately as a long-lived process** and use a thin shell wrapper that calls into it. More plumbing than it's worth for one user.
- **Use the cookidoo-api Python library directly** and skip the MCP layer. Write a small Python script that calls `Cookidoo.get_recipes_in_calendar_week()` etc. and pipes the JSON to your AI agent. This is what the MCP does internally — see `cookidoo-mcp/server.py` for examples.

## Web Claude / ChatGPT / Gemini (no filesystem access)

The skill assumes the AI can call MCP tools and read local files. Without those, you'd have to:

1. Manually run the Cookidoo MCP queries yourself (or via a thin Python script).
2. Paste the JSON into the chat.
3. Paste the persona into the chat as context.

It works but loses the automation. If you're going this route, you might as well skip the persona file and just chat your constraints directly each week.

## Anything that supports MCP but not slash commands

You'll lose `/meal-plan` and `/meal-plan-setup` as slash commands, but the skill content still works as a one-shot instruction. Tell the AI:

> Read `.claude/skills/meal-plan/SKILL.md` from this repo and follow it.

It'll execute the same workflow.

## What you give up outside Claude Code

- The slash-command UX (`/meal-plan` vs. typing the instruction every time)
- The setup wizard (you'll do persona fill manually)
- Auto-loaded skill on session start (varies by tool)
- The `AskUserQuestion` UI for batched questions (most tools just ask in plain text)

What still works everywhere: the persona, the skill workflow, the MCP itself, the rolling taste model, the source-diversification logic.
