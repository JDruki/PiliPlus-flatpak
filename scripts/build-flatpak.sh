#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-${PILIPLUS_TAG:-2.0.7}}"

cd "$ROOT"

python3 scripts/prepare-release.py "$TAG"

if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate flatpak/com.example.piliplus.desktop
fi

if command -v appstreamcli >/dev/null 2>&1; then
  appstreamcli validate --no-net build/generated/com.example.piliplus.metainfo.xml
fi

if command -v flatpak-builder >/dev/null 2>&1; then
  BUILDER=(flatpak-builder)
elif flatpak info --user org.flatpak.Builder >/dev/null 2>&1 || flatpak info org.flatpak.Builder >/dev/null 2>&1; then
  BUILDER=(flatpak run --command=sh org.flatpak.Builder -c)
else
  echo "error: flatpak-builder is not installed." >&2
  echo "Install either the host flatpak-builder package or org.flatpak.Builder from Flathub." >&2
  exit 1
fi

rm -rf .flatpak-build-dir .flatpak-repo

if [[ "${BUILDER[0]}" == "flatpak" ]]; then
  "${BUILDER[@]}" "cd '$ROOT' && XDG_DATA_HOME='${XDG_DATA_HOME:-$HOME/.local/share}' flatpak-builder --repo='$ROOT/.flatpak-repo' --force-clean --disable-updates --user '$ROOT/.flatpak-build-dir' '$ROOT/com.example.piliplus.yml'"
else
  "${BUILDER[@]}" --repo=.flatpak-repo --force-clean --disable-updates --user .flatpak-build-dir com.example.piliplus.yml
fi

mkdir -p dist
# shellcheck disable=SC1091
. build/generated/release.env

flatpak build-bundle .flatpak-repo "dist/$BUNDLE_NAME" com.example.piliplus master
sha256sum "dist/$BUNDLE_NAME" > "dist/$BUNDLE_NAME.sha256"

echo "Built dist/$BUNDLE_NAME"
