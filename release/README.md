# WD Display release files

Everything needed to install the app, verify what you downloaded, and comply with the GPL.

| File | What it is |
|---|---|
| `WD-Display-0.1.5-dev.apk` | The installable app, 28 MB, arm64, Android 10+ |
| `WD-Display-0.1.5-dev-source.tar.gz` | Full corresponding source for this exact build (GPLv3 obligation), 18 MB |
| `SHA256SUMS` | Checksums for both files above |
| `LICENSE` | GPLv3 |
| `THIRD_PARTY_NOTICES.md` | Every bundled component and its license |
| `icon.png` | App icon, for store listings or READMEs |

## Install

Copy the APK to an Android phone (Android 10 or newer, arm64), open it, and allow installs from that source when Android asks. Or:

```bash
adb install -r WD-Display-0.1.5-dev.apk
```

More detail, including the notification prompt and Play Protect warning: [`../docs/INSTALL.md`](../docs/INSTALL.md).

## Verify the download

```bash
shasum -a 256 -c SHA256SUMS
```

```text
390869b1694593cf0fe2df57296a751997b20092504c3a4d5ce7d54d4ea35c1e  WD-Display-0.1.5-dev.apk
71b8cc59c7b11c06df8d8b85961ee6baf13868a5fa7937aca58ed7da34c43c77  WD-Display-0.1.5-dev-source.tar.gz
```

## Build facts

| | |
|---|---|
| Package | `org.pocketairdisplay.receiver` |
| Version | `0.1.5-dev`, versionCode 5 |
| ABIs | `arm64-v8a` |
| Min / target SDK | 29 / 34 |
| Signature | Android debug certificate |
| Native page alignment | 16 KiB (`zipalign -c -P 16` and all ELF `PT_LOAD` verified) |

## A note on hosting

If you publish this on GitHub, prefer a **Release** with the APK attached over committing it into the repository. Releases give a stable download URL, a version history, and keep the git history small. The copy in this folder is the same file, kept here so the repository is self-contained.
