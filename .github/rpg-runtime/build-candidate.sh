#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
output=${1:?absolute empty output directory is required}
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" prepare "$output"
work=$(mktemp -d "${TMPDIR:-/tmp}/retrom-easyrpg-candidate.XXXXXX")
trap 'rm -rf "$work"' EXIT INT TERM
docker run --rm --platform linux/amd64 --hostname rpg-runtime-easyrpg \
  --volume "$root:/source:ro" --volume "$root/.github/rpg-runtime:/recipe:ro" \
  --volume "$work:/work" --volume "$output:/output" \
  emscripten/emsdk@sha256:af45409f3199d88db4b1b03af0098532c8fb33a375ac257463eeb0a622870d06 \
  /recipe/build-easyrpg.sh
commit=$(git -C "$root" rev-parse HEAD)
python3 "$root/.github/rpg-runtime/verify-release.py" --output "$output" \
  --repository "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["forkRepository"])' "$root/retrom-fork.json")" \
  --tag retrom-core-0.8.1.1-r999999 --commit "$commit"
rm "$output/rpg-runtime-release.json"
python3 "$root/.github/rpg-runtime/candidate_descriptor.py" finalize "$output" --core-id easyrpg
