# Installing BingeTV

BingeTV installs as its own app, beside Kodi if you have it. Nothing in Kodi is touched.

## Which APK

Each [release](https://github.com/shiggsy365/BingeTV/releases/latest) has two APKs:

| Device | APK |
|---|---|
| Fire TV Sticks and Fire TV Cube | `bingetv-armeabi-v7a-release.apk` (32-bit) |
| Android TV boxes, Google TV, Android tablets and phones | `bingetv-arm64-v8a-release.apk` (64-bit) |

If you're not sure, use the 32-bit one: it runs on every device above, just a little slower than
the 64-bit one on devices that support 64-bit. BingeTV needs Android 7.0 or later.

## Fire TV

1. Install **Downloader** (by AFTVnews) from the Amazon Appstore.
2. Go to **Settings > My Fire TV > Developer options > Install unknown apps** and turn it on for
   Downloader. If you don't see Developer options, go to **Settings > My Fire TV > About** and
   press OK on the device name seven times.
3. Open Downloader and enter the address of the 32-bit APK from the
   [latest release](https://github.com/shiggsy365/BingeTV/releases/latest). The release page
   lists it under Assets.
4. Choose **Install**. When it's done, delete the downloaded file to free up space.

## Android TV and Google TV

The same as Fire TV, with Downloader from the Play Store and the 64-bit APK. On Google TV the
setting is under **Settings > System > Developer options > Install unknown apps**.

## Android tablets and phones

Open the [latest release](https://github.com/shiggsy365/BingeTV/releases/latest) in the browser
and download the 64-bit APK. Open it from the notification or your Downloads, and allow your
browser to install apps when Android asks.

## The first start

BingeTV asks whether to bring your Kodi setup across:

- **From Kodi (or another BingeTV):** on the old device, open Stremio Bridge's settings and choose
  **Expert > Back up this Kodi**. Save the backup somewhere this device can read, for example its
  Download folder or a network share. Then choose **Restore a backup** here and pick the file.
  Profiles, add-ons and settings come across. BingeTV closes when it's done; start it again.
- **Start afresh:** the setup wizard asks for your MDBList key and Stremio add-ons (stream and
  metadata add-ons, by their manifest links).

## Updates

About once a week BingeTV checks for a new version and offers to download it. You can also check
from **Settings > Expert > Check for BingeTV updates**. Install the new APK over the old one: your
settings stay. Stremio Bridge and the other built-in add-ons update themselves from the
shiggsy365 repository.

## Removing it

Uninstall BingeTV like any other app. That removes its settings too, so back up first if you might
want them again.
