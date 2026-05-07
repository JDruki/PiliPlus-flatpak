#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


UPSTREAM_REPO = "bggRGjQaUbCoE/PiliPlus"
API_ROOT = f"https://api.github.com/repos/{UPSTREAM_REPO}"
ASSET_RE = re.compile(r"^PiliPlus_linux_.*_amd64\.tar\.gz$")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def request(url: str) -> urllib.request.Request:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "piliplus-flatpak-release-script",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(request(url), timeout=60) as response:
            return json.load(response)
    except Exception as exc:
        fail(f"failed to fetch {url}: {exc}")


def download_sha256(url: str, output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(request(url), timeout=300) as response, output.open("wb") as fh:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                fh.write(chunk)
    except Exception as exc:
        fail(f"failed to download {url}: {exc}")
    return digest.hexdigest()


def sh_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def derive_version(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the Flatpak manifest from a PiliPlus GitHub Release."
    )
    parser.add_argument("tag", help="Upstream PiliPlus release tag, for example 2.0.7")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Packaging repository root.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    tag = args.tag
    release = fetch_json(f"{API_ROOT}/releases/tags/{tag}")
    assets = [asset for asset in release.get("assets", []) if ASSET_RE.match(asset.get("name", ""))]
    if not assets:
        names = ", ".join(asset.get("name", "<unnamed>") for asset in release.get("assets", []))
        fail(f"release {tag!r} has no Linux amd64 tarball asset. Assets: {names}")

    asset = sorted(assets, key=lambda item: item["name"])[0]
    asset_url = asset.get("browser_download_url")
    if not asset_url:
        fail(f"asset {asset.get('name')} has no browser_download_url")

    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        asset_sha256 = digest.removeprefix("sha256:")
    else:
        cache_path = repo_root / "build" / "downloads" / asset["name"]
        asset_sha256 = download_sha256(asset_url, cache_path)

    version = derive_version(tag)
    release_date = (release.get("published_at") or dt.date.today().isoformat())[:10]
    bundle_name = f"PiliPlus-{version}-x86_64.flatpak"

    manifest_template = (repo_root / "com.example.piliplus.yml.in").read_text(encoding="utf-8")
    manifest = (
        manifest_template.replace("@PILIPLUS_TARBALL_URL@", asset_url)
        .replace("@PILIPLUS_TARBALL_SHA256@", asset_sha256)
    )
    write_text(repo_root / "com.example.piliplus.yml", manifest)

    metainfo_template = (
        repo_root / "flatpak" / "com.example.piliplus.metainfo.xml.in"
    ).read_text(encoding="utf-8")
    metainfo = (
        metainfo_template.replace("@VERSION@", version)
        .replace("@RELEASE_DATE@", release_date)
    )
    write_text(repo_root / "build" / "generated" / "com.example.piliplus.metainfo.xml", metainfo)

    env = {
        "PILIPLUS_TAG": tag,
        "PILIPLUS_VERSION": version,
        "PILIPLUS_RELEASE_DATE": release_date,
        "PILIPLUS_ASSET_NAME": asset["name"],
        "PILIPLUS_ASSET_URL": asset_url,
        "PILIPLUS_ASSET_SHA256": asset_sha256,
        "BUNDLE_NAME": bundle_name,
    }
    env_text = "".join(f"{key}={sh_quote(value)}\n" for key, value in env.items())
    write_text(repo_root / "build" / "generated" / "release.env", env_text)

    print(f"Generated Flatpak inputs for PiliPlus {tag}")
    print(f"Asset: {asset['name']}")
    print(f"SHA256: {asset_sha256}")


if __name__ == "__main__":
    main()
