# PiliPlus Flatpak Release Packaging

This repository packages the upstream PiliPlus Linux GitHub Release tarball as a
single-file Flatpak bundle and publishes it to this repository's GitHub Release.

Upstream project: <https://github.com/bggRGjQaUbCoE/PiliPlus>

## Local Build

Install Flatpak tooling and the GNOME runtime:

```bash
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.flatpak.Builder org.gnome.Platform//49 org.gnome.Sdk//49
```

Build a bundle from an upstream release tag:

```bash
./scripts/build-flatpak.sh 2.0.7
```

The output is written to `dist/`:

```bash
flatpak install --user -y dist/PiliPlus-2.0.7-x86_64.flatpak
flatpak run com.example.piliplus
```

## GitHub Release

Run the `Build Flatpak Release` workflow manually and pass the upstream PiliPlus
release tag, for example `2.0.7`.

The workflow:

1. Reads the upstream GitHub Release metadata.
2. Finds the `PiliPlus_linux_*_amd64.tar.gz` asset.
3. Generates the Flatpak manifest with the asset URL and SHA256.
4. Builds `PiliPlus-<version>-x86_64.flatpak`.
5. Publishes it to this repository under release tag `piliplus-<upstream-tag>`.

## Flatpak Permissions

The manifest keeps only the permissions needed for this desktop client:

- Network access for Bilibili and media requests.
- Wayland/X11 display access and IPC for the GUI.
- PulseAudio and DRI access for playback and hardware acceleration.
- Download, Pictures, and Videos folder access for user-selected output files.
- Notification and tray/appindicator D-Bus names for desktop integration.

Broad host filesystem access and unrestricted device access are intentionally not
enabled.
