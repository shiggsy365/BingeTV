#!/usr/bin/env python3
"""Publish a CI build's APKs as a GitHub release.

    GITHUB_TOKEN=... python3 tools/publish_release.py <CI run id> [notes.md]

Takes the run's two signed APK artifacts and makes the release v<BINGETV_VERSION> (from
config/build.env) at the run's commit, with the APKs attached. BingeTV's update notices
read GitHub's latest release, so the version must be the one the APKs were built with.
Refuses debug-signed artifacts, and a version that's already released.
"""

import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile

REPO = "shiggsy365/BingeTV"
API = f"https://api.github.com/repos/{REPO}"
HERE = os.path.dirname(os.path.abspath(__file__))


def build_version():
    with open(os.path.join(HERE, "..", "config", "build.env"), encoding="utf-8") as f:
        match = re.search(r"^BINGETV_VERSION=(\S+)", f.read(), re.M)
    return match.group(1)


def call(method, url, token, data=None, content_type="application/json", raw=False):
    body = data if isinstance(data, (bytes, type(None))) else json.dumps(data).encode()
    request = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
        "Content-Type": content_type, "User-Agent": "BingeTV release"})
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = response.read()
    return payload if raw else json.loads(payload or b"{}")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def download(url, token):
    """An artifact: GitHub answers with a redirect to its storage, which must be fetched
    without the token (it rejects requests that carry one)."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}",
                                                   "User-Agent": "BingeTV release"})
    try:
        with opener.open(request, timeout=600) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        location = exc.headers["Location"]
    with urllib.request.urlopen(urllib.request.Request(location, headers={"User-Agent": "BingeTV release"}),
                                timeout=600) as response:
        return response.read()


def main():
    token = os.environ["GITHUB_TOKEN"]
    run_id = sys.argv[1]
    notes = open(sys.argv[2], encoding="utf-8").read() if len(sys.argv) > 2 else ""
    version = build_version()
    tag = f"v{version}"
    try:
        call("GET", f"{API}/releases/tags/{tag}", token)
        sys.exit(f"{tag} is already released")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise

    run = call("GET", f"{API}/actions/runs/{run_id}", token)
    if run.get("conclusion") != "success":
        sys.exit(f"Run {run_id} didn't succeed ({run.get('conclusion')})")
    artifacts = call("GET", f"{API}/actions/runs/{run_id}/artifacts", token)["artifacts"]
    signed = [a for a in artifacts if a["name"].endswith("-release-signed")]
    if len(signed) != 2:
        sys.exit(f"Expected two release-signed APK artifacts, found {[a['name'] for a in artifacts]}")

    apks = {}
    for artifact in signed:
        data = download(artifact["archive_download_url"], token)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                if name.endswith(".apk"):
                    apks[name] = archive.read(name)
    print("APKs:", ", ".join(f"{n} ({len(b) // 1_000_000} MB)" for n, b in apks.items()))

    release = call("POST", f"{API}/releases", token, {
        "tag_name": tag, "target_commitish": run["head_sha"], "name": f"BingeTV {version}",
        "body": notes, "draft": False, "prerelease": False})
    upload = release["upload_url"].split("{")[0]
    for name, data in apks.items():
        call("POST", f"{upload}?name={name}", token, data, content_type="application/vnd.android.package-archive")
    print(f"Released {tag}: {release['html_url']}")


if __name__ == "__main__":
    main()
