# PiliPlus Flatpak Release Packaging

This repository packages the upstream PiliPlus Linux GitHub Release tarball as a
Flatpak app. The GitHub workflow publishes both a single-file `.flatpak` bundle
to GitHub Releases and an updateable Flatpak repository to GitHub Pages.

Upstream project: <https://github.com/bggRGjQaUbCoE/PiliPlus>

## Local Build

Install Flatpak tooling and the GNOME runtime:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.flatpak.Builder org.gnome.Platform//49 org.gnome.Sdk//49
```

Build from an upstream release tag:

```bash
./scripts/build-flatpak.sh 2.0.7
```

The output is written to `dist/`:

```bash
flatpak install --user -y dist/PiliPlus-2.0.7-x86_64.flatpak
flatpak run com.example.piliplus
```

The script also prepares a static Flatpak repository under `dist/pages/`. For
local testing without GPG signing:

```bash
flatpak --user remote-add --if-not-exists --no-gpg-verify piliplus dist/pages/repo
flatpak --user install -y piliplus com.example.piliplus
flatpak --user update com.example.piliplus
```

## Updateable Flatpak Repository

After a successful workflow run, GitHub Pages serves:

- `https://<owner>.github.io/<repo>/piliplus.flatpakrepo`
- `https://<owner>.github.io/<repo>/com.example.piliplus.flatpakref`
- `https://<owner>.github.io/<repo>/repo/`

Enable GitHub Pages for this repository with source set to **GitHub Actions**.
Then users can add the remote and receive updates from future workflow runs:

```bash
flatpak remote-add --user --if-not-exists piliplus \
  https://<owner>.github.io/<repo>/piliplus.flatpakrepo
flatpak install --user piliplus com.example.piliplus
flatpak update --user com.example.piliplus
```

For a production remote, configure GPG signing before sharing the URL:

1. Create a passphrase-less GPG key dedicated to this Flatpak repository.
2. Add the private key export to the repository secret
   `FLATPAK_GPG_PRIVATE_KEY`.
3. Add the key ID to the repository variable `FLATPAK_GPG_KEY_ID`, or to the
   secret `FLATPAK_GPG_KEY_ID`.

If signing is not configured, the workflow still publishes an unsigned
repository. Users must add it with `--no-gpg-verify`, which is only appropriate
for personal testing.

## GitHub Release

Run the `Build Flatpak Release` workflow manually and pass the upstream PiliPlus
release tag, for example `2.0.7`. You can also pass `latest`.

The workflow also runs every 6 hours. Scheduled runs resolve the latest upstream
PiliPlus GitHub Release and only build when this packaging repository does not
already have the matching release tag.

The workflow:

1. Reads the upstream GitHub Release metadata.
2. Finds the `PiliPlus_linux_*_amd64.tar.gz` asset.
3. Checks whether `piliplus-<upstream-tag>` already exists in this repository.
4. Generates the Flatpak manifest with the asset URL and SHA256.
5. Builds `PiliPlus-<version>-x86_64.flatpak` and an OSTree Flatpak repository.
6. Deploys the Flatpak repository to GitHub Pages.
7. Publishes the bundle to this repository under release tag
   `piliplus-<upstream-tag>`.

Manual workflow runs enable `force` by default, so they can rebuild an existing
Flatpak release. Scheduled runs never force rebuilds.

## Flatpak Permissions

The manifest keeps only the permissions needed for this desktop client:

- Network access for Bilibili and media requests.
- Wayland/X11 display access and IPC for the GUI.
- PulseAudio and DRI access for playback and hardware acceleration.
- Download, Pictures, and Videos folder access for user-selected output files.
- Notification and tray/appindicator D-Bus names for desktop integration.

Broad host filesystem access and unrestricted device access are intentionally not
enabled.
