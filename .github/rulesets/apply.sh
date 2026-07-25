#!/usr/bin/env bash
# Apply the repo rulesets in this directory idempotently, via the GitHub API.
#
#   ./.github/rulesets/apply.sh
#
# Requires the `gh` CLI, authenticated with admin on the repo. Each <name>.json
# is matched to an existing ruleset by its ".name"; found -> PUT (update),
# else -> POST (create). Re-running is safe.
set -euo pipefail

dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Applying rulesets to $repo"

existing="$(gh api "repos/$repo/rulesets" --paginate)"

for f in "$dir"/*.json; do
  name="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['name'])" "$f")"
  id="$(echo "$existing" | python3 -c "import json,sys;name=sys.argv[1];print(next((r['id'] for r in json.load(sys.stdin) if r['name']==name),''))" "$name")"
  if [ -n "$id" ]; then
    echo "  update '$name' (id $id)"
    gh api -X PUT "repos/$repo/rulesets/$id" --input "$f" >/dev/null
  else
    echo "  create '$name'"
    gh api -X POST "repos/$repo/rulesets" --input "$f" >/dev/null
  fi
done
echo "Done."
