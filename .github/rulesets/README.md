# Repository rulesets (infrastructure-as-code)

Branch/tag protection for this repo, versioned as JSON so it is reviewable and
reproducible instead of hand-clicked in Settings.

## Apply

```bash
./.github/rulesets/apply.sh
```

Requires the `gh` CLI authenticated with **admin** on the repo. The script is
idempotent (create-or-update by ruleset `name`).

## What they do

- **`require-review-contributors.json`** — protects the default branch: blocks
  deletion and force-push (`non_fast_forward`), requires a PR with 1 approval
  (dismiss stale on push, require approval of the last push), and requires the
  CI status checks below to pass with an up-to-date branch
  (`strict_required_status_checks_policy`). Merge methods are limited to
  **merge** and **rebase** (no squash), matching the maintainer's preference.
- **`protect-release-tags.json`** — protects `refs/tags/v*` from deletion and
  force-moves (creating new release tags is unaffected).

## Two things to verify before/after applying

1. **Owner bypass.** `bypass_actors` grants the repository **admin** role
   (`actor_id: 5`) an *always* bypass, so the solo maintainer can still commit
   directly to `main` and cut tags without PR ceremony. Confirm the role id maps
   to admin in your account (`gh api repos/:owner/:repo/rulesets/:id` after
   applying) and adjust if your org uses different roles.
2. **Status-check contexts must match the CI check names exactly.** The contexts
   listed mirror the job `name:` fields in `.github/workflows/ci.yml`
   ("Unicode supply-chain guard", "Lint & type-check", "Test (Python 3.10)" …).
   If you rename a CI job, update the ruleset context here too, or the required
   check will never be satisfied.

## Export current state (drift check)

```bash
gh api repos/:owner/:repo/rulesets --jq '.[].name'
gh api repos/:owner/:repo/rulesets/<id> > /tmp/current.json   # compare to the file here
```
