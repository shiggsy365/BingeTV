#!/usr/bin/env bash
# Build a BingeTV APK for one Android ABI.
#
#   scripts/build-android.sh arm       # armeabi-v7a: Fire TV Stick 4K and other 32-bit devices
#   scripts/build-android.sh aarch64   # arm64-v8a: most Android TV boxes, tablets and phones
#
# Follows Kodi's docs/README.Android.md: Kodi's source at the tag in config/build.env,
# with our patches and overlay applied, then Kodi's depends, binary add-ons, the
# CMake build and `make apk`.
#
# Needs: the packages listed in Kodi's README.Android.md, JDK 17+, and an Android SDK
# with the NDK, platform and build tools in config/build.env (ANDROID_SDK_ROOT).
# Everything is built under WORK_DIR (default ~/bingetv-work); the APK ends up in
# WORK_DIR/out.
set -euo pipefail

ABI=${1:?usage: $0 arm|aarch64}
case "$ABI" in
  arm) HOST=arm-linux-androideabi ;;
  aarch64) HOST=aarch64-linux-android ;;
  *) echo "Unknown ABI '$ABI' (use arm or aarch64)" >&2; exit 2 ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=../config/build.env
source "$ROOT/config/build.env"

WORK_DIR=${WORK_DIR:-$HOME/bingetv-work}
SDK=${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/android-tools/android-sdk-linux}}
NDK=${ANDROID_NDK_PATH:-$SDK/ndk/$ANDROID_NDK_VERSION}
JOBS=${JOBS:-$(getconf _NPROCESSORS_ONLN)}
SRC=$WORK_DIR/kodi
BUILD=$WORK_DIR/build-$ABI
OUT=$WORK_DIR/out

step() { echo; echo "=== $* ($(date +%T))"; }

[ -d "$NDK" ] || { echo "NDK not found at $NDK" >&2; exit 1; }
mkdir -p "$WORK_DIR" "$WORK_DIR/tarballs" "$OUT"

step "Kodi $KODI_TAG source"
if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 --branch "$KODI_TAG" "$KODI_REPO" "$SRC"
else
  # A fresh tree each time, so patches apply to exactly the tagged source.
  git -C "$SRC" fetch --depth 1 origin "refs/tags/$KODI_TAG:refs/tags/$KODI_TAG"
  git -C "$SRC" checkout -q -f "$KODI_TAG"
  git -C "$SRC" clean -q -fdx -e tools/depends/target -e tools/depends/native
fi

step "Patches"
shopt -s nullglob
for patch in "$ROOT"/patches/*.patch; do
  echo "Applying $(basename "$patch")"
  git -C "$SRC" apply --whitespace=nowarn "$patch"
done

step "Overlay"
# overlay/ mirrors Kodi's source tree: its files replace or add to Kodi's.
(cd "$ROOT/overlay" && find . -type f ! -name README.md -print0 | while IFS= read -r -d '' f; do
  mkdir -p "$SRC/$(dirname "$f")"
  cp "$f" "$SRC/$f"
done)

step "Built-in add-ons"
# Stremio Bridge, the BingeTV skin and the rest, into Kodi's addons/ (tools/bundle_addons.py).
BINARY_ADDONS="$BINARY_ADDONS" BINGETV_VERSION="$BINGETV_VERSION" BINGETV_RELEASES="$BINGETV_RELEASES" \
  OURS_REPO="$OURS_REPO" OURS_REF="$OURS_REF" OURS_ADDONS="$OURS_ADDONS" \
  KODI_ADDON_MIRROR="$KODI_ADDON_MIRROR" KODI_REPO_ADDONS="$KODI_REPO_ADDONS" \
  python3 "$ROOT/tools/bundle_addons.py" "$SRC"

step "Signing key"
# Release builds pass the BingeTV key in KODI_ANDROID_STORE_FILE, KODI_ANDROID_KEY_ALIAS,
# KODI_ANDROID_STORE_PASSWORD and KODI_ANDROID_KEY_PASSWORD (read by Kodi's packaging).
# Without them Kodi signs with ~/.android/debug.keystore, made here if it's missing.
if [ -n "${KODI_ANDROID_STORE_FILE:-}" ]; then
  echo "Signing with $KODI_ANDROID_STORE_FILE"
elif [ ! -f "$HOME/.android/debug.keystore" ]; then
  mkdir -p "$HOME/.android"
  keytool -genkey -keystore "$HOME/.android/debug.keystore" -v -alias androiddebugkey \
    -dname "CN=Android Debug,O=Android,C=US" -keypass android -storepass android \
    -keyalg RSA -keysize 2048 -validity 10000
fi

step "Depends for $HOST"
cd "$SRC/tools/depends"
./bootstrap
# Kodi's depends default to a debug build (--enable-debug): debug flags and a debuggable
# APK. Release builds, like Kodi's own, use --disable-debug; DEBUG_BUILD=1 for a debug one.
if [ "${DEBUG_BUILD:-0}" = 1 ]; then debug=--enable-debug; else debug=--disable-debug; fi
./configure --with-tarballs="$WORK_DIR/tarballs" --host="$HOST" \
  --with-sdk-path="$SDK" --with-ndk-path="$NDK" --prefix="$WORK_DIR/depends" "$debug"
make -j"$JOBS"

# Binary add-ons with patches of ours (patches/addons/<id>/*.patch) are built from a local
# copy of their source: the branch Kodi's add-on list pins, with the patches applied. The
# rest are fetched and built by Kodi's own add-on build as usual.
PATCHED_ADDONS=""
for dir in "$ROOT"/patches/addons/*/; do
  id=$(basename "$dir")
  case " $BINARY_ADDONS " in *" $id "*) PATCHED_ADDONS="$PATCHED_ADDONS $id" ;; esac
done
PLAIN_ADDONS=$(for id in $BINARY_ADDONS; do case " $PATCHED_ADDONS " in *" $id "*) ;; *) echo "$id" ;; esac; done | xargs)
ADDON_SRC="$WORK_DIR/addon-src"
read -r _ _ KODI_ADDONS_BRANCH < "$SRC/cmake/addons/bootstrap/repositories/binary-addons.txt"  # e.g. Piers

step "Binary add-ons: $PLAIN_ADDONS"
make -j"$JOBS" -C "$SRC/tools/depends/target/binary-addons" ADDONS="$PLAIN_ADDONS"

for id in $PATCHED_ADDONS; do
  step "Binary add-on $id, patched"
  # e.g. "pvr.iptvsimple https://github.com/kodi-pvr/pvr.iptvsimple Piers"
  read -r _ url ref < <(curl -fsSL "https://raw.githubusercontent.com/xbmc/repo-binary-addons/$KODI_ADDONS_BRANCH/$id/$id.txt")
  rm -rf "$ADDON_SRC/$id"
  git clone -q --depth 1 --branch "$ref" "$url" "$ADDON_SRC/$id"
  echo "$id at $(git -C "$ADDON_SRC/$id" rev-parse --short HEAD)"
  for patch in "$ROOT"/patches/addons/"$id"/*.patch; do
    echo "Applying $(basename "$patch")"
    git -C "$ADDON_SRC/$id" apply --whitespace=nowarn "$patch"
  done
  rm -f "$SRC"/tools/depends/target/binary-addons/.installed-*  # it only builds once otherwise
  make -j"$JOBS" -C "$SRC/tools/depends/target/binary-addons" ADDONS="$id" ADDON_SRC_PREFIX="$ADDON_SRC"
done

step "Kodi"
make -C "$SRC/tools/depends/target/cmakebuildsys" BUILD_DIR="$BUILD"
make -C "$BUILD" -j"$JOBS"

step "APK"
make -C "$BUILD" apk
# Kodi names it kodiapp-<abi>-<release|debug>.apk.
for apk in $(find "$SRC" -maxdepth 1 -name "*.apk" -newer "$BUILD/CMakeCache.txt"); do
  cp -v "$apk" "$OUT/$(basename "$apk" | sed 's/^kodiapp-/bingetv-/')"
done
ls -la "$OUT"
