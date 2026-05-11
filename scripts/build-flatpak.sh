#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${1:-${PILIPLUS_TAG:-2.0.7}}"
APP_ID="com.example.piliplus"
APP_BRANCH="master"
REPO_NAME="${FLATPAK_REPO_NAME:-piliplus}"
REPO_TITLE="${FLATPAK_REPO_TITLE:-PiliPlus Flatpak}"
REPO_COMMENT="${FLATPAK_REPO_COMMENT:-Unofficial PiliPlus Flatpak builds}"
REPO_DESCRIPTION="${FLATPAK_REPO_DESCRIPTION:-Auto-built Flatpak repository for upstream PiliPlus releases.}"
BASE_URL="${FLATPAK_BASE_URL:-}"
REPO_URL="${FLATPAK_REPO_URL:-}"
GPG_KEY_ID="${FLATPAK_GPG_KEY_ID:-}"
GPG_HOMEDIR="${FLATPAK_GPG_HOMEDIR:-${GNUPGHOME:-}}"
GPG_PUBLIC_KEY="${FLATPAK_GPG_PUBLIC_KEY:-}"

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

builder_args=(--repo=.flatpak-repo --force-clean --disable-updates --user)
if [[ -n "$GPG_KEY_ID" ]]; then
  if [[ "${BUILDER[0]}" == "flatpak" ]]; then
    echo "error: signing requires the host flatpak-builder command, not org.flatpak.Builder." >&2
    exit 1
  fi
  builder_args+=(--gpg-sign="$GPG_KEY_ID")
  if [[ -n "$GPG_HOMEDIR" ]]; then
    builder_args+=(--gpg-homedir="$GPG_HOMEDIR")
  fi
fi
builder_args+=(.flatpak-build-dir com.example.piliplus.yml)

if [[ "${BUILDER[0]}" == "flatpak" ]]; then
  printf -v builder_command ' %q' "${builder_args[@]}"
  "${BUILDER[@]}" "cd '$ROOT' && XDG_DATA_HOME='${XDG_DATA_HOME:-$HOME/.local/share}' flatpak-builder$builder_command"
else
  "${BUILDER[@]}" "${builder_args[@]}"
fi

mkdir -p dist
# shellcheck disable=SC1091
. build/generated/release.env

update_repo_args=(
  --title="$REPO_TITLE"
  --comment="$REPO_COMMENT"
  --description="$REPO_DESCRIPTION"
  --default-branch="$APP_BRANCH"
  --generate-static-deltas
)
if [[ -n "$BASE_URL" ]]; then
  update_repo_args+=(--homepage="$BASE_URL" --icon="$BASE_URL/logo.png")
fi
if [[ -n "$GPG_KEY_ID" ]]; then
  update_repo_args+=(--gpg-sign="$GPG_KEY_ID")
  if [[ -n "$GPG_PUBLIC_KEY" ]]; then
    update_repo_args+=(--gpg-import="$GPG_PUBLIC_KEY")
  fi
  if [[ -n "$GPG_HOMEDIR" ]]; then
    update_repo_args+=(--gpg-homedir="$GPG_HOMEDIR")
  fi
fi

flatpak build-update-repo "${update_repo_args[@]}" .flatpak-repo

bundle_args=()
if [[ -n "$REPO_URL" ]]; then
  bundle_args+=(--repo-url="$REPO_URL")
fi
if [[ -n "$GPG_PUBLIC_KEY" ]]; then
  bundle_args+=(--gpg-keys="$GPG_PUBLIC_KEY")
fi

flatpak build-bundle "${bundle_args[@]}" .flatpak-repo "dist/$BUNDLE_NAME" "$APP_ID" "$APP_BRANCH"
sha256sum "dist/$BUNDLE_NAME" > "dist/$BUNDLE_NAME.sha256"

rm -rf dist/pages
pages_args=(
  --repo-dir .flatpak-repo
  --output-dir dist/pages
  --app-id "$APP_ID"
  --branch "$APP_BRANCH"
  --repo-name "$REPO_NAME"
  --repo-title "$REPO_TITLE"
  --repo-comment "$REPO_COMMENT"
  --repo-description "$REPO_DESCRIPTION"
)
if [[ -n "$BASE_URL" ]]; then
  pages_args+=(--base-url "$BASE_URL")
fi
if [[ -n "$REPO_URL" ]]; then
  pages_args+=(--repo-url "$REPO_URL")
fi
if [[ -n "$GPG_PUBLIC_KEY" ]]; then
  pages_args+=(--gpg-key "$GPG_PUBLIC_KEY")
fi

python3 scripts/prepare-pages.py "${pages_args[@]}"

echo "Built dist/$BUNDLE_NAME"
echo "Prepared Flatpak repository in dist/pages"
