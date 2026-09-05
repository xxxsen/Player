# RPG runtime EasyRPG Web release

Tags matching `retrom-core-0.8.1.1-rN` build the tagged Player source with
Emscripten 3.1.74 and publish these GitHub Release assets:

- `easyrpg-player.js`
- `easyrpg-player.wasm`
- `rpg-runtime-release.json`

The workflow pins the liblcf and EasyRPG buildscripts commits used by host-independent RPG runtimes.
Hosts may pass `runtimeProjectRootUrl` to the modularized player factory to
load a project from an explicit URL. When omitted, the normal EasyRPG
`games/<game>/` lookup remains unchanged.
Hosts may also pass `runtimeRtpRemoteFiles` as an array of
`{lookupPath, path, url}` entries. `lookupPath` uses the same normalized lookup keys
as the project `index.json`. Project files always win; a missing project
resource is fetched from the matching RTP URL only when the game actually asks
for it. RTP archives are therefore not downloaded or unpacked before the first
frame.
The runtime status reports only the actual engine, map readiness, checkpoint
availability and frame count. It has no host review or fixture-state protocol;
development tests can inspect an ordinary saved LCF file for map and variable
assertions without changing the core's public status.
The JSON digest values describe the uploaded bytes for cache diagnostics; they
are not the remote admission identity. Consumers identify this runtime by the
repository, tag, tag commit, asset filenames and `easyrpg-save-v1` adapter ABI.
