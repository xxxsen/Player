# RPG runtime EasyRPG Web release

Tags matching `rpg-runtime-0.8.1.1-rN` build the tagged Player source with
Emscripten 3.1.74 and publish these GitHub Release assets:

- `easyrpg-player.js`
- `easyrpg-player.wasm`
- `rpg-runtime-release.json`

The workflow pins the liblcf and EasyRPG buildscripts commits used by host-independent RPG runtimes.
The JSON digest values describe the uploaded bytes for cache diagnostics; they
are not the remote admission identity. Consumers identify this runtime by the
repository, tag, tag commit, asset filenames and `easyrpg-save-v1` adapter ABI.
