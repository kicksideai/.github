<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/kicksideai/docs/main/getting-started/assets/brand/kickside-logo-dark.png">
  <img src="https://raw.githubusercontent.com/kicksideai/docs/main/getting-started/assets/brand/kickside-logo-light.png" alt="KickSide" width="320">
</picture>

# KickSide community resources

Shared contribution, support, security, and conduct documents for the KickSide organization. The repository also contains the organization [profile](profile/README.md), pull request template, and the `setup-wippy` and `legal-check` composite actions used by repository workflows. `legal-check` fails when `THIRD_PARTY_NOTICES.md` no longer matches the locked npm and Cargo dependencies, or when a source file added in a pull request lacks an SPDX header; regenerate notices locally with `python3 actions/legal-check/notices.py --root <repo> --cache <cache-dir>`.

- [Contributing](CONTRIBUTING.md)
- [Contributor license agreement](CLA.md) (organization members are exempt)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Security reporting](SECURITY.md)
- [Support](SUPPORT.md)

The reusable CLA workflow (`.github/workflows/cla.yml`) skips the signature check for kicksideai organization members. It uses the CLA GitHub App installation token and requires the app permission Organization permissions -> Members: Read-only, in addition to Contents: Read and write on `.github-private`.

Product source lives in the repositories listed on the [KickSide organization](https://github.com/kicksideai). Product guides and shared images live in [docs](https://github.com/kicksideai/docs).

[Documentation](https://github.com/kicksideai/docs) · [KickSide](https://kickside.ai)
