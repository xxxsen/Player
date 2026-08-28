# Retrom Player fork maintenance rules

This fork builds the EasyRPG browser core consumed by `xxxsen/retrom-runtime`.
It must remain independent of any Retrom host application API, database, review
workflow, credentials, or private game content.

## Repository identity

- `master` is the only long-lived Retrom maintenance branch.
- `upstream` must point to `https://github.com/EasyRPG/Player.git`.
- `retrom-fork.json` is the machine-readable upstream baseline and release
  contract. Never replace its tag or commit with a floating branch.
- Do not use GitHub's automatic **Sync fork** action. Upstream updates require a
  reviewed `sync/upstream-<tag-or-git-commit>` branch.

## Branches and commits

- Use only short-lived `fix/<task>-<slug>`, `feat/<task>-<slug>`,
  `build/<task>-<slug>`, or `sync/upstream-<baseline>` branches.
- Branch names use lowercase ASCII and hyphens. Do not create branches named
  `temp`, `clean`, `final`, `runtime-clean`, or with an agent/user name.
- Merge one logical change at a time into `master`, then delete its branch.
- Never force-push, move, or delete another contributor's branch. A one-time
  repository normalization must be explicitly authorized by the maintainer.
- Preserve downstream patches as small reviewable commits so an upstream sync
  can reapply or retire them independently.

## Releases

- Release tags have the form `rpg-runtime-0.8.1.1-rN`, with optional
  `-rc.N` only for integration candidates.
- `rN` increases for any source, build, asset, or adapter-contract change while
  the upstream baseline remains `0.8.1.1`. A new upstream baseline restarts at
  `r1` under its own tag name.
- Create annotated tags only from a clean commit already merged into `master`.
- Tags and published assets are immutable: never move a tag, overwrite an
  asset, or create aliases such as `latest`, `stable`, or `current`.
- The tag workflow is the only supported way to build and upload release
  assets. Observed hashes diagnose local/cache corruption; repository, tag,
  tag commit, asset filename, and adapter ABI define release identity.

Before publishing, run the checks relevant to the changed Player/build code and
verify that `.github/rpg-runtime/verify-release.py` accepts the produced pair.
Do not publish games, RTP, credentials, or host-specific code.
