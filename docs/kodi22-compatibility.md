# Add-ons on Kodi 22 (phase 2)

Tested 16 October 2026 in BingeTV (Kodi 22.0 RC1, Python 3.14.6) on a Fire TV Stick 4K
(Android 7.1.2, armeabi-v7a). The add-ons are the released versions from
[KodiStremioBridge](https://github.com/shiggsy365/KodiStremioBridge), unchanged.

## Result

Every add-on works on Kodi 22 as it is. No code changes are needed.

Kodi 22 still accepts add-ons written for the Kodi 21 interfaces. Its Python API is 3.1.0 but
keeps compatibility back to 3.0.0; its skin API is 5.18.0, compatible back to 5.17.0. The add-ons
keep requiring `xbmc.python` 3.0.1, so the same releases run on Kodi 21 and 22.
`kodi-addon-checker --branch piers` reports no problems.

| Add-on | Version | What was tested | Result |
|---|---|---|---|
| Stremio Bridge | 0.16.3 | Menus, Next Up, Watchlist, hubs, catalogs, search, an info page; play with stream choice, subtitles and playback tracking; MDBList sync; Up Next hand-off and playing the next episode | Works. Lists answer in 0.5–1.5 s. From streams found to playing takes 1.2 s once warm (7 s on the very first play, while caches fill). |
| Dispatcharr Bridge | 1.0.1 | Its keymap installs; during live TV, the source picker lists the channel's sources from Dispatcharr | Works |
| Tidy Cache | 1.0.0 | Service starts; a manual tidy-up | Works |
| Podcasts | 1.0.5 | Main menu | Works |
| shiggsy365 repository | 1.0.2 | Enabled | Works |
| Up Next (official repo) | 1.1.9 | Pop-up near the end of an episode, then playing the next one | Works |
| YouTube (official repo) | 7.4.4 | Main menu | Works. Its first run logs harmless errors about settings files it hasn't created yet. |
| IPTV Simple (built in) | 22.6.5 | Your Kodi 21 settings: 214 channels, 6 groups, 5,300 guide entries; playing a channel | Works |

## For later phases

- **Build:** IPTV Simple requires `inputstream.rtmp`, which is now in `config/build.env`.
- **Defaults for phase 4:**
  - Stock Kodi 22 installs IPTV Simple and InputStream FFmpegDirect disabled; BingeTV should enable them.
  - Subtitles default to "forced only" (`locale.subtitlelanguage`). The Kodi 21 setup they replace had English.
  - Remote control from other devices (`services.esallinterfaces`) is off. It's needed for Dispatcharr tools and for testing.
- **Skin:** Stremio Bridge falls back to Kodi's own dialogs in Estuary, such as the progress dialog while streams are found. The new skin (phase 3) brings back its own windows.
