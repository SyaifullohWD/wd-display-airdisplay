# WD Display release files

Everything needed to install the app, verify what you downloaded, and comply with the GPL.

| File | What it is |
|---|---|
| `WD-Display-0.1.4-dev.apk` | The installable app, 28 MB, arm64, Android 10+ |
| `WD-Display-0.1.4-dev-source.tar.gz` | Full corresponding source for this exact build (GPLv3 obligation), 18 MB |
| `SHA256SUMS` | Checksums for both files above |
| `LICENSE` | GPLv3 |
| `THIRD_PARTY_NOTICES.md` | Every bundled component and its license |
| `icon.png` | App icon, for store listings or READMEs |

## Install

Copy the APK to an Android phone (Android 10 or newer, arm64), open it, and allow installs from that source when Android asks. Or:

```bash
adb install -r WD-Display-0.1.4-dev.apk
```

More detail, including the notification prompt and Play Protect warning: [`../docs/INSTALL.md`](../docs/INSTALL.md).

## Verify the download

```bash
shasum -a 256 -c SHA256SUMS
```

```text
cd671f0386087c7947807c6edcd14dc5b248e8c379fc5601e0a95d3840f9ab4c  WD-Display-0.1.4-dev.apk
221cae11387c0f4f806e3d0df3635bc8524d468666a5c9af849dabbc18ea7252  WD-Display-0.1.4-dev-source.tar.gz
```

## Build facts

| | |
|---|---|
| Package | `org.pocketairdisplay.receiver` |
| Version | `0.1.4-dev`, versionCode 5 |
| ABIs | `arm64-v8a` |
| Min / target SDK | 29 / 34 |
| Signature | Android debug certificate |
| Native page alignment | 16 KiB (`zipalign -c -P 16` and all ELF `PT_LOAD` verified) |

## A note on hosting

If you publish this on GitHub, prefer a **Release** with the APK attached over committing it into the repository. Releases give a stable download URL, a version history, and keep the git history small. The copy in this folder is the same file, kept here so the repository is self-contained.
