# BingeTV

BingeTV is an Android media centre built from [Kodi](https://kodi.tv) 22 "Piers", with
[Stremio Bridge](https://github.com/shiggsy365/KodiStremioBridge) built in. It is for Fire TV,
Android TV and Android tablets.

> BingeTV is an unofficial build. It is not made, endorsed or supported by Team Kodi or the
> XBMC Foundation. Please don't ask them for help with it. Kodi® is a registered trademark of
> the XBMC Foundation.

## Status

Work in progress. Right now the repo builds **stock Kodi 22** for Android (phase 0).

| Phase | What | State |
|---|---|---|
| 0 | Reproducible CI build of Kodi 22 for armeabi-v7a and arm64-v8a | in progress |
| 1 | Rebrand as BingeTV (`com.shiggsy365.bingetv`), release signing | planned |
| 2 | Port Stremio Bridge and its add-ons to Kodi 22 | planned |
| 3 | New skin for Kodi 22 | planned |
| 4 | Built-in add-ons, first-run restore of a Kodi backup, update notices | planned |
| 5 | Remove what isn't needed, tune for speed (measured on a Fire TV Stick 4K) | planned |
| 6 | Signed releases | planned |

## How it's built

This isn't a fork of Kodi's whole repository. It holds only what BingeTV changes:

- `config/build.env`: the Kodi tag it's built from, the Android toolchain and the binary add-ons.
- `patches/`: changes to Kodi's code, applied in name order.
- `overlay/`: files added to or replacing files in Kodi's source tree, laid out like it.
- `scripts/build-android.sh`: fetches Kodi at the tag, applies the patches and overlay, and
  builds the APK, following Kodi's `docs/README.Android.md`.
- `.github/workflows/android.yml`: builds both APKs on GitHub Actions.

To build locally (Linux x86_64), install the packages and Android SDK/NDK listed in Kodi's
[README.Android.md](https://github.com/xbmc/xbmc/blob/22.0rc1-Piers/docs/README.Android.md),
then run:

```sh
ANDROID_SDK_ROOT=~/android-tools/android-sdk-linux scripts/build-android.sh arm      # 32-bit
ANDROID_SDK_ROOT=~/android-tools/android-sdk-linux scripts/build-android.sh aarch64  # 64-bit
```

The APK lands in `~/bingetv-work/out` (set `WORK_DIR` to build elsewhere). Expect tens of GB of
disk use and a long first build.

## Licence

BingeTV's build files are GPL-2.0-or-later, the same as Kodi. The source of every change made to
Kodi is in this repository.
