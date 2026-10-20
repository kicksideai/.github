# Agent instructions

## Commits and pull requests

* Write each commit message and each pull request title in the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) format: `<type>[optional scope]: <description>`.
* Use one of these types: `feat`, `fix`, `perf`, `revert`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`, `style`.
* Use the module directory name as the scope when the change is in one module. Example: `fix(<module>): keep the event order during replay`.
* For a breaking change, put `!` after the type or scope, or add a `BREAKING CHANGE:` footer.
* When you squash-merge a pull request, its title becomes the commit message. Keep the title in the same format.

## Releases

* [Release Please](https://github.com/googleapis/release-please) reads the commit messages on `main` to find the next version and to write the changelog. It opens one release pull request, and a merge of that pull request makes the tags and the GitHub releases.
* Do not change `CHANGELOG.md`, `version.txt`, or `.release-please-manifest.json` manually. Release Please changes them.
