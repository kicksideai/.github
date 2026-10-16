# Contributing to KickSide

Contributions to KickSide repositories include code, documentation, tests, and
reproducible issue reports. Follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Before you start

Check existing issues and [KickSide Discussions](https://github.com/kicksideai/kickside/discussions).
Use an issue to discuss substantial behavior or API changes before implementing
them. Report vulnerabilities privately under [SECURITY.md](SECURITY.md).

A signed [Individual Contributor License Agreement](CLA.md) is required from
contributors outside the KickSide organization before contributions are merged.
Members of the kicksideai organization are exempt; the CLA check passes for
them without a signature. The CLA check posts the required instruction on a
pull request when an external contributor needs to sign. Read the agreement and
comment exactly:

```
I have read and agree to the KickSide Individual Contributor License Agreement, Version 1.0.
```

The check records the signature against the contributor's GitHub account in a
private organization record. Do not put legal names, email addresses, or signed
forms in an issue or PR. GitHub bot accounts are allowlisted. For a corporate
CLA or account correction, contact
[licensing@wippy.ai](mailto:licensing@wippy.ai).

## Development setup

Development and contributions happen on GitHub. Fork the repository and create
a focused branch for your change. Read
its README and any repository-specific CONTRIBUTING.md first; the checked-in
Makefiles and CI workflows define the supported commands and tool versions.

Install the [Wippy CLI](https://hub.wippy.ai/releases). UI repositories also
require Node.js and npm; converter builds need their documented Rust or Docker
toolchains. Some repository checks require Python 3. Use the
[developer handbook](https://hub.wippy.ai/kickside/kickside/wiki/docs/kickside-development/developer-handbook.md) for contracts, registry declarations, host
requirements, migrations, and the development loop. For a new module, use
[kicksideai/module](https://github.com/kicksideai/module).

Keep credentials and generated local runtime state out of Git. Build UI through
the repository's Makefiles and include regenerated tracked served assets with
their source changes. Preserve third-party notices and licenses.

## Testing

Run the relevant build, lint, and test targets documented in the repository.
Add tests for behavior changes. Persistence and migration changes must exercise
both SQLite and PostgreSQL where those backends apply; describe any unsupported
backend or validation limitation in the PR. UI changes need their type checks,
production build, and relevant interaction tests. Documentation changes need
link checks and an accurate description of the code.

Record the commands and results in the PR, including checks you could not run
and the reason. CI must pass before merge.

## Commits and pull requests

1. Keep commits focused. Use a short imperative subject with a prefix such as
   `docs: clarify setup`, `fix: handle empty records`, or `feat: add a provider`.
2. Open a GitHub pull request to the repository with the problem, resulting behavior,
   linked issues, and validation results. Include screenshots for UI changes
   when they help review.
3. Complete the PR checklist, including lint, applicable database tests,
   generated assets, documentation, and CLA status.
4. Address maintainer feedback and keep the PR current with its target branch.
   Maintainers approve and merge; avoid unrelated formatting or refactors.

## Help

See [SUPPORT.md](SUPPORT.md). For licensing or contribution-agreement questions,
email [licensing@wippy.ai](mailto:licensing@wippy.ai).
