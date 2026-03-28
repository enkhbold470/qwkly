# Agent Skills


Agent skills are portable instruction sets that teach AI coding agents how to perform tasks. Senso publishes official skills that give your agent deep knowledge of the Senso CLI — when to use each command, how to parse results, and how to orchestrate multi-step workflows.

Skills follow the open [Agent Skills](https://agentskills.io) standard and work with Claude Code, Cursor, Codex, GitHub Copilot, Gemini CLI, Cline, and other compatible agents.

## Install skills

The fastest way to install all Senso skills for your agent:

```bash
senso skills install --all
```

Or install individual skills by short name:

```bash
senso skills install search ingest content-gen
```

The CLI auto-detects which agent you're using. To target a specific agent:

```bash
senso skills install --all --agent claude
senso skills install --all --agent cursor
```

### Install via Shipables

You can also install directly from the [Shipables](https://shipables.dev) registry:

```bash
npx shipables install @senso/senso-search --claude
```

Or install all six at once:

```bash
npx shipables install @senso/senso-search @senso/senso-ingest @senso/senso-content-gen @senso/senso-brand-setup @senso/senso-kb-organize @senso/senso-review-publish --claude
```

Replace `--claude` with `--cursor`, `--codex`, `--copilot`, `--gemini`, or `--cline` for other agents.

## Available skills

Senso publishes six official skills:

| Skill | Short name | What it teaches your agent |
|-------|-----------|---------------------------|
| `@senso/senso-search` | `search` | Search the KB with the right variant (full answer, context chunks, or content IDs), parse results, and cite sources |
| `@senso/senso-ingest` | `ingest` | Upload files and raw text, target folders, handle duplicates, and poll processing status |
| `@senso/senso-content-gen` | `content-gen` | Run pre-flight checks, generate samples or batch runs, monitor progress, and handle timeouts |
| `@senso/senso-brand-setup` | `brand-setup` | Configure the brand kit and create content type templates with the right fields |
| `@senso/senso-kb-organize` | `kb-organize` | Browse the folder tree, create/move/rename nodes, and check sync status after changes |
| `@senso/senso-review-publish` | `review-publish` | Review pending content, approve/reject versions, publish to destinations, and manage ownership |

## How skills work

Once installed, skills activate automatically based on conversation context. You don't need to do anything special — just talk to your agent naturally:

```
You: "What's our current refund policy? Check Senso."

Agent runs:
  senso search "refund policy" --output json --quiet

Agent reads the JSON response and answers with cited sources
  from your verified knowledge base.
```

```
You: "Upload this quarter's compliance report to Senso."

Agent runs:
  senso ingest upload Q1-compliance-report.pdf --output json --quiet

Agent confirms the upload and reports the content ID.
```

```
You: "Generate a blog post about our new pricing model."

Agent checks:
  senso brand-kit get --output json --quiet
  senso content-types list --output json --quiet
  senso prompts list --output json --quiet

Agent runs:
  senso generate sample --prompt-id <id> --content-type-id <id> --output json --quiet

Agent shows you the generated content for review.
```

## Manage installed skills

List installed Senso skills:

```bash
senso skills list
```

See all available skills:

```bash
senso skills list-available
```

Remove a skill:

```bash
senso skills remove search
```

## Project vs. global install

By default, skills install at the project level (e.g., `.claude/skills/`). To install globally so skills are available in every project:

```bash
senso skills install --all --global
```

| Scope | Location (Claude Code) | When to use |
|-------|----------------------|-------------|
| Project | `.claude/skills/senso-search/` | Per-repo, committed with the project |
| Global | `~/.claude/skills/senso-search/` | Available everywhere on your machine |

## Next steps

- [Senso CLI](/docs/senso-for-agents) — Full CLI command reference
- [Quickstart](/docs/hello-world) — Walk through the core upload-and-search loop
- [API Reference](/api-reference) — Browse all endpoints the CLI wraps
