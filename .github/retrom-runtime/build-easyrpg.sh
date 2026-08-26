#!/bin/bash
set -euo pipefail

readonly PLAYER_SOURCE=/source
readonly WORK_ROOT=/work
readonly OUTPUT_ROOT=/output
readonly BUILDSCRIPTS_COMMIT=57e4736179f65e910a399267f4ce4ea68d382667
readonly LIBLCF_COMMIT=92c4450a1bc1acb58bd02bbb99b57e5036919cdf
readonly BUILDSCRIPTS="$WORK_ROOT/buildscripts"
readonly PREFIX="$WORK_ROOT/easyrpg-prefix"
readonly PLAYER_BUILD="$WORK_ROOT/player-build"

export DEBIAN_FRONTEND=noninteractive
export LANG=C
export LC_ALL=C
export SOURCE_DATE_EPOCH=0
export TZ=UTC
export USE_WASM_SIMD=0
export BUILD_LIBLCF=1
export NO_CCACHE=1

apt-get update
apt-get install -y --no-install-recommends \
  autoconf automake build-essential bzip2 ca-certificates cmake curl gettext git \
  libtool ninja-build patch perl pkg-config python3 python3-pip unzip xz-utils
PIP_DISABLE_PIP_VERSION_CHECK=1 python3 -m pip install meson==1.7.0
git config --global --add safe.directory "$PLAYER_SOURCE"

git clone https://github.com/EasyRPG/buildscripts.git "$BUILDSCRIPTS"
git -C "$BUILDSCRIPTS" checkout --detach "$BUILDSCRIPTS_COMMIT"
patch -d "$BUILDSCRIPTS" -p1 < /recipe/easyrpg-fixed-parallel.patch

mkdir -p "$PREFIX" "$OUTPUT_ROOT"
cd "$PREFIX"
"$BUILDSCRIPTS/emscripten/1_download_library.sh"
git -C "$PREFIX/liblcf" checkout --detach "$LIBLCF_COMMIT"
"$BUILDSCRIPTS/emscripten/2_build_toolchain.sh"

emcmake cmake -S "$PLAYER_SOURCE" -B "$PLAYER_BUILD" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$PREFIX" \
  -DCMAKE_FIND_ROOT_PATH="$PREFIX" \
  -DSDL2_DIR="$PREFIX/lib/cmake/SDL2" \
  -DPLAYER_FIND_ROOT_PATH_APPEND=ON \
  -DPLAYER_ENABLE_TESTS=OFF \
  -DPLAYER_JS_GAME_URL=/runtime/rpg-project/ \
  -DPLAYER_JS_BUILD_SHELL=OFF
cmake --build "$PLAYER_BUILD" --parallel 1

install -m 0644 "$PLAYER_BUILD/easyrpg-player.js" "$OUTPUT_ROOT/easyrpg-player.js"
install -m 0644 "$PLAYER_BUILD/easyrpg-player.wasm" "$OUTPUT_ROOT/easyrpg-player.wasm"
