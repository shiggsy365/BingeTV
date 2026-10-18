# BingeTV: remaining work

What's left to build, phase by phase. Phases 0–2 are done: the build, release signing, branding,
and the check that Stremio Bridge and its add-ons work on Kodi 22 unchanged (see
[docs/kodi22-compatibility.md](docs/kodi22-compatibility.md)).

The new skin, `skin.bingetv`, and Stremio Bridge live in the
[KodiStremioBridge](https://github.com/shiggsy365/KodiStremioBridge) repository. This repository
builds the APK.

## Phase 3: the BingeTV skin (done)

`skin.bingetv` rebuilds Arctic Zephyr Stremio's layout for Kodi 22 in BingeTV's theme: brand red
(`FFE31E2D`) for focus, white text on focus, and the same design throughout.

### Done

- **3.1–3.3:** Home with rows for each menu item, the menu bar, the hubs (Movies, TV), the
  information page, the "Finding streams" and "Preparing to play" pages, the stream picker and
  Search.
- **3.4, the player:**
  - The banner along the top and the bar along the bottom of the video.
  - The OSD's buttons, with a caption for the focused button. The OSD hides after a few seconds
    without a key press (7 by default).
  - A Streams button for choosing a different stream for what's playing.
  - The audio, subtitle and video settings as a panel down the right-hand side.
  - Up Next's cards.
- **Across the skin:**
  - "Watched" and "Paused" ribbons on posters and thumbnails.
  - The preparing page stays up through every step.
  - Dialogs, notifications, the context menu and add-on settings in BingeTV's style.
- **3.5: Home rows.** Choose, order, rename and remove the rows on Home, Movies and TV Shows:
  - Rows can come from your lists (Continue Watching, Next Up, Watchlist) or any catalog.
  - Each profile keeps its own rows.
  - Opened from BingeTV settings. It replaces Skin Shortcuts' "Customise Home".
- **3.6: BingeTV settings** (Settings > BingeTV):
  - Home rows.
  - Music, Live TV and the power button on the menu bar.
  - The ribbons.
  - How long the player's controls stay up (3–10 s).
  - Touch screen mode.
  - A link to Stremio Bridge's settings.
- **3.7: Other hubs and touch.**
  - Anime, More and your own hubs appear on the menu bar (up to four) when they have catalogs.
  - Touch screens: tapping and swiping work, and touch screen mode adds a Back button at the top
    left of every page but Home.

- **Stremio Bridge 0.17.0** (released 18 October 2026) carries everything the skin needs from
  the add-on: the Streams button, skipping placeholder clips, the steady preparing page, the Home
  rows editor and the menu bar's extra hubs.

The skin itself isn't in the add-on repository: it ships inside the APK (phase 4).

## Phase 4: BingeTV out of the box (done)

- **Built-in add-ons** (`tools/bundle_addons.py`, a build step):
  - From KodiStremioBridge, at the commit pinned in `config/build.env` (`OURS_REF`): Stremio
    Bridge, `skin.bingetv`, Dispatcharr Bridge, Tidy Cache and the shiggsy365 repository.
  - From Kodi's own repository for Piers: Up Next and YouTube, with the Python modules YouTube
    needs (requests, urllib3, certifi, chardet, idna).
  - `patches/0002-bingetv-defaults.patch` lists them in `system/addon-manifest.xml` as optional
    system add-ons. Kodi turns those on at the first start, and they can still be updated,
    disabled or removed. Anything bundled but not listed would start disabled.
- **Default settings** (`patches/0002`):
  - `skin.bingetv` is the default skin.
  - Subtitles default to English.
  - Remote control from other devices is on (`services.esallinterfaces`).
  - InputStream FFmpegDirect and InputStream RTMP are on from the start.
  - IPTV Simple stays off until a playlist is set in Settings > IPTV, which turns it on.
- **First run:** the setup wizard first offers to restore a Kodi backup. The backup is made on
  the old device under Settings > Expert > Back up this Kodi.
- **Updates:**
  - The build writes `media/bingetv.json` (`BINGETV_VERSION`, and where releases are).
  - About once a week Stremio Bridge checks GitHub's latest BingeTV release. If it's newer, it
    offers the download for the device's ABI, once per version.
  - Settings > Expert > Check for BingeTV updates checks straight away.
- **Old-format settings:** nothing to do. Our add-ons already use Kodi's new settings format.
  Kodi's "old format" messages came from Up Next's own settings definitions, which it converts
  itself.

Tested on 18 October 2026 with CI's release-signed armeabi-v7a APK, on a Fire TV Stick 4K with
BingeTV's data cleared:
- The first start used the BingeTV skin. All the built-in add-ons were on, and IPTV Simple stayed
  off as planned.
- Subtitles defaulted to English, and remote control from other devices was on.
- The restore offer appeared. Restoring the device's backup brought back the profile, rows,
  add-ons and IPTV channels.
- `patches/0003` was needed: Android's packaging keeps only a skin's `Textures.xbt`, so the first
  build's skin had no images.

## Phase 5: speed and slimming (in progress)

- **The reusable Python interpreter** (`patches/0004`):
  - **The crash:** with `reuselanguageinvoker` on, Kodi 22 crashed (SIGSEGV in
    `CPythonInvoker::execute`, in `GilSafeSingleLock`) when several Home rows loaded at once.
  - **The cause:** Kodi keeps one reusable interpreter. One plugin call could claim it, then
    another call released it before the first had started. The first then ran on a new thread
    while the old thread tore the interpreter down.
  - **The patch:**
    - The plugin handle and the interpreter are claimed together, by one call.
    - While the interpreter is claimed or running, other calls get a handle and a one-off
      interpreter of their own, which is how every call works with reuse off. Nothing releases it
      from under its claimant.
    - BingeTV's Kodi turns reuse on for Stremio Bridge itself. The add-on doesn't ask for it in its
      `addon.xml`, because on plain Kodi it can still crash.
  - Still to do: test on the Stick, with the old reproduction (fast Left/Right over Home's menu)
    and timings.
- **Home rows straight away:** this mostly comes from the reusable interpreter (pages measured at
  120–310 ms instead of 650–1,030 ms) plus Stremio Bridge's pre-warmed catalogs. Measure once the
  build is in; anything still slow gets its own fix.
- **"Preparing to play" page:** done (Stremio Bridge 0.17.0). It's taken down a minute after the
  hand-over if Kodi never starts the stream.
- **Kodi 21's settings files** (Stremio Bridge, next release): Kodi 22 converts a Kodi 21
  add-on settings file on every load until a setting is saved. Once per start, the service
  re-saves each such file. Tested on the Stick: Dispatcharr Bridge's file went from version 2 to 4.
- **Unused Kodi add-ons removed** (`patches/0005`):
  - Estuary, now that `skin.bingetv` is the built-in default.
  - The WMA encoder.
  - The four game controllers.
  - Chorus2, the browser remote. Phone remotes still work.
  - The weather icons.
  - Kodi's version check, which tells you to update Kodi and is no use in BingeTV.
  - The music album and artist scrapers and their `metadata.common.*` helpers. Music from add-ons
    still works, but Kodi's own music-library scanning no longer fetches album and artist details.
  - The settings that named them now have empty defaults.
  - Kept: the black screensaver, and the TMDb movie and TV scrapers (Stremio Bridge's "My
    Library" uses them).
- **Other tuning:** measure start-up and menu timings on the Stick before and after.

## Phase 6: releases

- Move from Kodi 22.0 RC1 to the final Kodi 22 release tag once it's out (`KODI_TAG` in
  `config/build.env`). Then repeat the phase 2 checks.
- Publish signed APKs (32-bit and 64-bit ARM) as GitHub releases. Point phase 4's update
  notification at them.
- Write install and update instructions for Fire TV, Android TV and Android tablets.

## Known limitations

- AIOMetadata gives no episode ratings, so episode cards show a rating only with other meta
  add-ons.
- Some stream sources serve a short "can't play this" clip instead of the video:
  - With autoplay, Stremio Bridge skips any video shorter than 2m31s and plays the next stream.
  - When you pick the stream yourself, the clip plays, but it isn't marked as watched. Pick another
    stream with the Streams button.
  - A real video shorter than 2m31s would also be skipped under autoplay, which only matters for
    very short clips.
