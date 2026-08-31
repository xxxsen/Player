# Retrom Player fork maintenance rules

This fork builds the EasyRPG browser core consumed by `retrom-project/retrom-runtime`.
It must remain independent of any Retrom host application API, database, review
workflow, credentials, or private game content.

## Repository identity

- `master` is an unmodified, fast-forward-only mirror of `upstream/master`.
- `retrom/0.8.1.1` is the only active Retrom maintenance baseline and the
  repository default branch. Retrom patches and release tags originate there,
  never from `master`.
- `upstream` must point to `https://github.com/EasyRPG/Player.git`.
- `retrom-fork.json` is the machine-readable upstream baseline and release
  contract. Never replace its tag or commit with a floating branch.
- Updating `master` must only fast-forward it to `upstream/master`. Updating the
  fixed Retrom baseline requires a reviewed `sync/upstream-<tag-or-git-commit>`
  branch and a new `retrom/<baseline>` branch; do not merge a moving upstream
  `master` into the fixed baseline.

## Branches and commits

- Use only short-lived `fix/<task>-<slug>`, `feat/<task>-<slug>`,
  `build/<task>-<slug>`, or `sync/upstream-<baseline>` branches.
- Branch names use lowercase ASCII and hyphens. Do not create branches named
  `temp`, `clean`, `final`, `runtime-clean`, or with an agent/user name.
- Create work branches from `retrom/0.8.1.1`, merge one logical change at a
  time back into that baseline, then delete the work branch.
- Never force-push, move, or delete another contributor's branch. A one-time
  repository normalization must be explicitly authorized by the maintainer.
- Preserve downstream patches as small reviewable commits so an upstream sync
  can reapply or retire them independently.

## Releases

- Release tags have the form `retrom-core-0.8.1.1-rN`, with optional
  `-rc.N` only for integration candidates.
- `rN` increases for any source, build, asset, or adapter-contract change while
  the upstream baseline remains `0.8.1.1`. A new upstream baseline restarts at
  `r1` under its own tag name.
- Create annotated tags only from a clean commit already merged into
  `retrom/0.8.1.1`. The tagged commit must retain the exact upstream tag commit
  recorded in `retrom-fork.json` as its unmodified ancestry baseline.
- Tags and published assets are immutable: never move a tag, overwrite an
  asset, or create aliases such as `latest`, `stable`, or `current`.
- Existing `rpg-runtime-*` tags are immutable historical records. Never create
  another tag in that retired namespace.
- The tag workflow is the only supported way to build and upload release
  assets. Observed hashes diagnose local/cache corruption; repository, tag,
  tag commit, asset filename, and adapter ABI define release identity.

Before publishing, run the checks relevant to the changed Player/build code and
verify that `.github/rpg-runtime/verify-release.py` accepts the produced pair.
Do not publish games, RTP, credentials, or host-specific code.
