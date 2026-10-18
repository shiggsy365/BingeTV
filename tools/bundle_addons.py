#!/usr/bin/env python3
"""Put BingeTV's built-in add-ons into Kodi's source tree before it's built.

    python3 tools/bundle_addons.py <kodi source>

Reads config/build.env (passed in the environment by scripts/build-android.sh):

- OURS_REPO, OURS_REF, OURS_ADDONS: add-ons from the KodiStremioBridge repository,
  at a pinned commit (Stremio Bridge, the BingeTV skin, ...).
- KODI_REPO_ADDONS, KODI_ADDON_MIRROR: add-ons from Kodi's own repository for this
  release (Up Next, YouTube), with the Python modules they need. Anything Kodi
  already has, or that's built as a binary add-on (BINARY_ADDONS), is left out.
- BINGETV_VERSION: written to media/bingetv.json, which Stremio Bridge reads to
  tell you when a newer BingeTV is out.

Each add-on goes into <kodi source>/addons/<id>/ and is listed in
cmake/installdata/common/addons.txt, so it's packed into the APK. A skin isn't
listed: patches/0003 has Kodi pack its media/ into Textures.xbt, as for Estuary
(Android's packaging keeps nothing else from a skin's media/). Kodi turns them
on at the first start because patches/0002 lists them in system/addon-manifest.xml.
"""

import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

SKIP_NAMES = {"__pycache__", ".git", ".github", "tests", ".pytest_cache"}
SKIP_SUFFIXES = (".pyc", ".pyo")


def env_list(name):
    return os.environ.get(name, "").split()


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def copy_addon(source, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)

    def ignore(folder, names):
        return [n for n in names if n in SKIP_NAMES or n.endswith(SKIP_SUFFIXES)]

    shutil.copytree(source, dest, ignore=ignore)


def our_addons(kodi, wanted):
    repo, ref = os.environ["OURS_REPO"], os.environ["OURS_REF"]
    with tempfile.TemporaryDirectory() as work:
        subprocess.run(["git", "init", "-q", work], check=True)
        subprocess.run(["git", "-C", work, "fetch", "-q", "--depth", "1", repo, ref], check=True)
        subprocess.run(["git", "-C", work, "checkout", "-q", "FETCH_HEAD"], check=True)
        for addon in wanted:
            copy_addon(os.path.join(work, addon), os.path.join(kodi, "addons", addon))
            print(f"{addon}: from {repo} at {ref[:12]}")
    return list(wanted)


def kodi_repo_addons(kodi, wanted, skip):
    mirror = os.environ["KODI_ADDON_MIRROR"].rstrip("/")
    index = ET.fromstring(gzip.decompress(fetch(f"{mirror}/addons.xml.gz")))
    known = {a.get("id"): a for a in index.findall("addon")}
    have = set(os.listdir(os.path.join(kodi, "addons"))) | set(skip)
    todo, done = list(wanted), []
    while todo:
        addon_id = todo.pop(0)
        if addon_id in done or (addon_id in have and addon_id not in wanted):
            continue
        entry = known.get(addon_id)
        if entry is None:
            sys.exit(f"{addon_id} isn't in {mirror}")
        version = entry.get("version")
        data = fetch(f"{mirror}/{addon_id}/{addon_id}-{version}.zip")
        dest = os.path.join(kodi, "addons", addon_id)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            archive.extractall(os.path.join(kodi, "addons"))
        print(f"{addon_id}: {version} from {mirror}")
        done.append(addon_id)
        for need in entry.iter("import"):
            dep = need.get("addon")
            if dep.startswith(("xbmc.", "kodi.")) or need.get("optional") == "true":
                continue
            todo.append(dep)
    return done


def list_in_apk(kodi, addons):
    path = os.path.join(kodi, "cmake", "installdata", "common", "addons.txt")
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for addon in addons:
        if addon.startswith("skin."):
            continue  # skins are packed (Textures.xbt) and installed by Kodi's CMake: patches/0003
        line = f"addons/{addon}/*"
        if line not in lines:
            lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_version(kodi):
    info = {"version": os.environ["BINGETV_VERSION"], "releases": os.environ["BINGETV_RELEASES"]}
    with open(os.path.join(kodi, "media", "bingetv.json"), "w", encoding="utf-8") as f:
        json.dump(info, f)
    print(f"media/bingetv.json: {info}")


def main():
    kodi = sys.argv[1]
    bundled = our_addons(kodi, env_list("OURS_ADDONS"))
    bundled += kodi_repo_addons(kodi, env_list("KODI_REPO_ADDONS"), env_list("BINARY_ADDONS"))
    list_in_apk(kodi, bundled)
    write_version(kodi)


if __name__ == "__main__":
    main()
