# BingeTV

BingeTV is an Android media centre built from [Kodi](https://kodi.tv) 22 "Piers", with
[Stremio Bridge](https://github.com/shiggsy365/KodiStremioBridge) built in. It is for Fire TV,
Android TV and Android tablets.

> BingeTV is an unofficial build. It is not made, endorsed or supported by Team Kodi or the
> XBMC Foundation. Please don't ask them for help with it. Kodi® is a registered trademark of
> the XBMC Foundation.

## Install

Download the APK for your device from the [latest release](https://github.com/shiggsy365/BingeTV/releases/latest).
[docs/install.md](docs/install.md) has step-by-step instructions for Fire TV, Android TV and
tablets, and how to bring your Kodi setup across.

## Status

BingeTV is built from **Kodi 22.0 RC1**. It moves to the final Kodi 22 release once Team Kodi
publishes it. [implementation.md](implementation.md) has the details of each phase.

| Phase | What | State |
|---|---|---|
| 0 | Reproducible CI build of Kodi 22 for armeabi-v7a and arm64-v8a | done |
| 1 | Rebrand as BingeTV (`com.shiggsy365.bingetv`), release signing | done |
| 2 | Port Stremio Bridge and its add-ons to Kodi 22 ([results](docs/kodi22-compatibility.md)) | done: they work unchanged |
| 3 | A new skin for Kodi 22 (`skin.bingetv`, in KodiStremioBridge) | done |
| 4 | Built-in add-ons, first-run restore of a Kodi backup, update notices | done |
| 5 | A safe reusable Python interpreter, a slimmer Kodi, faster start (measured on a Fire TV Stick 4K) | done |
| 6 | Signed releases | done; the final Kodi 22 to come |

## How it's built

This isn't a fork of Kodi's whole repository. It holds only what BingeTV changes:

- `config/build.env`: the Kodi tag it's built from, the Android toolchain and the binary add-ons.
- `patches/`: changes to Kodi's code, applied in name order.
- `overlay/`: files added to or replacing files in Kodi's source tree, laid out like it.
- `scripts/build-android.sh`: fetches Kodi at the tag, applies the patches and overlay, and
  builds the APK, following Kodi's `docs/README.Android.md`.
- `.github/workflows/android.yml`: builds both APKs on GitHub Actions.
- `tools/bundle_addons.py`: puts the built-in add-ons into Kodi's source before it's built
  (Stremio Bridge, the BingeTV skin and the rest, from KodiStremioBridge at `OURS_REF`; Up Next
  and YouTube from Kodi's repository).
- `tools/publish_release.py`: publishes a CI build's two APKs as a GitHub release.
- `tools/make_branding.py`: draws BingeTV's icons, banners and splash screens into `overlay/`.
  Kodi's logo and name are the XBMC Foundation's trademarks, so none of Kodi's are shipped.
  Internally the program is still called Kodi (`APP_NAME`): that keeps binary add-ons and
  Kodi's paths working.

To build locally (Linux x86_64), install the packages and Android SDK/NDK listed in Kodi's
[README.Android.md](https://github.com/xbmc/xbmc/blob/22.0rc1-Piers/docs/README.Android.md),
then run:

```sh
ANDROID_SDK_ROOT=~/android-tools/android-sdk-linux scripts/build-android.sh arm      # 32-bit
ANDROID_SDK_ROOT=~/android-tools/android-sdk-linux scripts/build-android.sh aarch64  # 64-bit
```

The APK lands in `~/bingetv-work/out` (set `WORK_DIR` to build elsewhere). Expect tens of GB of
disk use and a long first build.

## Releasing

1. Set `BINGETV_VERSION` in `config/build.env` (and `OURS_REF` to the KodiStremioBridge commit to
   build in), then push. CI builds both APKs.
2. When the run has succeeded: `GITHUB_TOKEN=... python3 tools/publish_release.py <run id> notes.md`.
   BingeTV's update notices read the latest release, so the version must match the APKs'.

## Signing

Release APKs are signed with the BingeTV key. CI reads it from two repository secrets:
`BINGETV_KEYSTORE` (the `.jks` file, base64-encoded) and `BINGETV_KEY_PASSWORD`. Without them,
for example in a fork, CI signs with a throwaway debug key, and the artifact's name says so.
An APK signed with a debug key can't be installed over a release one.

## Licence

BingeTV's build files are GPL-2.0-or-later, the same as Kodi. The source of every change made to
Kodi is in this repository.
