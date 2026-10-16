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

step "Debug signing key"
# Phase 0 signs with Kodi's usual debug key; release signing comes with the rebrand.
if [ ! -f "$HOME/.android/debug.keystore" ]; then
  mkdir -p "$HOME/.android"
  keytool -genkey -keystore "$HOME/.android/debug.keystore" -v -alias androiddebugkey \
    -dname "CN=Android Debug,O=Android,C=US" -keypass android -storepass android \
    -keyalg RSA -keysize 2048 -validity 10000
fi

step "Depends for $HOST"
cd "$SRC/tools/depends"
./bootstrap
./configure --with-tarballs="$WORK_DIR/tarballs" --host="$HOST" \
  --with-sdk-path="$SDK" --with-ndk-path="$NDK" --prefix="$WORK_DIR/depends"
make -j"$JOBS"

step "Binary add-ons: $BINARY_ADDONS"
make -j"$JOBS" -C "$SRC/tools/depends/target/binary-addons" ADDONS="$BINARY_ADDONS"

step "Kodi"
make -C "$SRC/tools/depends/target/cmakebuildsys" BUILD_DIR="$BUILD"
make -C "$BUILD" -j"$JOBS"

step "APK"
make -C "$BUILD" apk
find "$SRC" -maxdepth 1 -name "*.apk" -newer "$BUILD/CMakeCache.txt" -exec cp -v {} "$OUT/" \;
ls -la "$OUT"
