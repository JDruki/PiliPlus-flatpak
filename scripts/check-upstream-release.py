#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
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
        "User-Agent": "piliplus-flatpak-release-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, headers=headers)


def fetch_json(url: str, allow_404: bool = False) -> dict | None:
    try:
        with urllib.request.urlopen(request(url), timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        fail(f"failed to fetch {url}: HTTP {exc.code}")
    except Exception as exc:
        fail(f"failed to fetch {url}: {exc}")


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def github_tag_url(repo: str, tag: str) -> str:
    quoted_tag = urllib.parse.quote(tag, safe="")
    return f"https://api.github.com/repos/{repo}/releases/tags/{quoted_tag}"


def write_outputs(outputs: dict[str, str]) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            for key, value in outputs.items():
                fh.write(f"{key}={value.replace(chr(10), ' ')}\n")

    generated = Path("build/generated")
    generated.mkdir(parents=True, exist_ok=True)
    with (generated / "check.env").open("w", encoding="utf-8") as fh:
        for key, value in outputs.items():
            fh.write(f"{key.upper()}='{value.replace(chr(39), chr(39) + chr(34) + chr(39) + chr(34) + chr(39))}'\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve whether a PiliPlus Flatpak release should be built.")
    parser.add_argument(
        "--tag",
        default="latest",
        help="Upstream PiliPlus tag to package, or 'latest'.",
    )
    parser.add_argument(
        "--packaging-repo",
        required=True,
        help="This GitHub repository in owner/name form, for example JDruki/PiliPlus-flatpak.",
    )
    parser.add_argument(
        "--force",
        default="false",
        help="Build even when the matching packaging release already exists.",
    )
    args = parser.parse_args()

    requested_tag = args.tag.strip() or "latest"
    if requested_tag == "latest":
        release = fetch_json(f"{API_ROOT}/releases/latest")
    else:
        release = fetch_json(github_tag_url(UPSTREAM_REPO, requested_tag))

    if not release:
        fail(f"could not resolve upstream release {requested_tag!r}")

    tag = release.get("tag_name")
    if not tag:
        fail("upstream release response has no tag_name")

    assets = [asset for asset in release.get("assets", []) if ASSET_RE.match(asset.get("name", ""))]
    if not assets:
        names = ", ".join(asset.get("name", "<unnamed>") for asset in release.get("assets", []))
        fail(f"release {tag!r} has no Linux amd64 tarball asset. Assets: {names}")

    force = parse_bool(args.force)
    release_tag = f"piliplus-{tag}"
    existing_release = fetch_json(github_tag_url(args.packaging_repo, release_tag), allow_404=True)
    exists = existing_release is not None
    should_build = force or not exists

    if should_build:
        reason = "forced rebuild" if force and exists else "new upstream release"
    else:
        reason = f"{release_tag} already exists"

    outputs = {
        "tag": tag,
        "release_tag": release_tag,
        "asset_name": sorted(assets, key=lambda item: item["name"])[0]["name"],
        "should_build": "true" if should_build else "false",
        "exists": "true" if exists else "false",
        "reason": reason,
    }
    write_outputs(outputs)

    print(f"Upstream tag: {tag}")
    print(f"Packaging release tag: {release_tag}")
    print(f"Asset: {outputs['asset_name']}")
    print(f"Existing packaging release: {outputs['exists']}")
    print(f"Should build: {outputs['should_build']} ({reason})")


if __name__ == "__main__":
    main()
