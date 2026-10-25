<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/kicksideai/docs/main/getting-started/assets/brand/kickside-logo-dark.png">
  <img src="https://raw.githubusercontent.com/kicksideai/docs/main/getting-started/assets/brand/kickside-logo-light.png" alt="KickSide" width="320">
</picture>

### Where the software you build with AI keeps running.

KickSide is a self-hosted application for agents, knowledge, records and durable workflows, plus the module system you extend it with. Every feature, including the ones we ship, is an independently versioned Lua module on the [Wippy](https://wippy.ai) runtime. Install what you need, write the rest from a template, and run all of it on your own infrastructure.

```sh
mkdir my-kickside && cd my-kickside
wippy run kickside/kickside -c --profile quickstart   # then open http://localhost:8085
```

[Install guide](https://github.com/kicksideai/docs/blob/main/getting-started/index.md) · [Build a module](https://github.com/kicksideai/docs/blob/main/building-modules/index.md) · [Docs](https://github.com/kicksideai/docs) · [kickside.ai](https://kickside.ai)

![KickSide with fictional demonstration data: an agent chat, the CRM pipeline, a visual workflow, and a knowledge base](https://raw.githubusercontent.com/kicksideai/docs/main/assets/readme/kickside-overview.webp)

## Under the hood

- **Durable flows.** Workflows compile to a DAG with branch, loop, for-each and wait nodes. A wait parks in the database and resumes on a signal, after a restart too. Publishing freezes an immutable version, and every run gets its own IDs.
- **Event-sourced state.** Each component appends immutable facts to its own thread, with optimistic concurrency and deduplication on external IDs. Projections fold those events into the read models your endpoints query.
- **Agents run as someone.** Scheduled and deferred work carries an execution identity and re-checks that principal's authority when it starts. Acting for someone else needs an explicit delegate grant.
- **Delivery guarantees you declare.** A write destination states exactly-once, at-least-once or at-most-once and receives a per-delivery idempotency key.
- **MCP in both directions.** Claude and other MCP clients reach KickSide tools over OAuth or scoped, revocable credentials. KickSide agents call remote MCP servers through a connector.
- **Deny wins.** Group policies union and denies take precedence. The router checks each endpoint by exact ID before the handler applies its own resource ACL. Delegation fences invalidate reduced delegated authority.
- **Contracts between modules.** Modules talk through JSON-schema contracts instead of reading each other's tables, so you can swap an implementation without touching its callers.
- **SQLite or PostgreSQL.** Module test suites run against both.

## Repositories

| Repository | What you get |
| --- | --- |
| [kickside](https://github.com/kicksideai/kickside) | The application. Core services (threads, jobs, contracts, execution identity) and the platform modules for agents, models, connections, knowledge, workflows and security. |
| [crm](https://github.com/kicksideai/crm) | Typed records that start with an empty schema. You define the objects, fields and relations; it gives you table and board views, imports, history and 17 agent tools. |
| [providers](https://github.com/kicksideai/providers) | Connectors for GitHub, GitLab, Bitbucket, Google, Slack, Discord, Telegram, Atlassian, HubSpot and remote MCP servers. Also the kb10 retrieval engine, web search, code execution, speech-to-text, OCR and SSO providers. |
| [components](https://github.com/kicksideai/components) | Dashboard, a research agent, first-agent onboarding and OAuth2/OIDC single sign-on. |
| [chestor](https://github.com/kicksideai/chestor) | Workspace modules: a shared entry tree, a semantic graph editor, an agent work journal, roadmaps and database schema diagrams. |
| [converters](https://github.com/kicksideai/converters) | Rust compiled to WebAssembly, called from Lua: documents to Markdown, HTML to PDF, PDF pages to images. MIT. |
| [module](https://github.com/kicksideai/module) | The template for your own module: a sink, a Block, migrations, an API, a Vue component, SQLite and PostgreSQL tests and a release pipeline. MIT. |
| [docs](https://github.com/kicksideai/docs) | Install and usage guides, the module authoring handbook and reference. |

## License in one paragraph

KickSide uses the [KickSide Community License 1.0](https://github.com/kicksideai/kickside/blob/main/LICENSE.md). It permits internal production use, applications built on KickSide, client services, and independently published modules, subject to the linked terms. Commercial licensing applies to commercial provision of KickSide itself and the third-party registry services described in section 2. The Wippy runtime is MPL-2.0. The module template and converters are MIT.

[Contribute](https://github.com/kicksideai/.github/blob/main/CONTRIBUTING.md) · [Support](https://github.com/kicksideai/.github/blob/main/SUPPORT.md) · [Report a vulnerability](https://github.com/kicksideai/.github/blob/main/SECURITY.md)
