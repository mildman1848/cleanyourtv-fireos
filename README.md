# CleanYourTV for Fire TV (Fire OS)

English · [Deutsch](README.de.md)

**A focused community fork for adapting CleanYourTV to Amazon Fire TV devices.** This repository is not the general Android TV / Google TV project and is not an official release of upstream CleanYourTV.

Upstream CleanYourTV remains the project for Android TV and Google TV: [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv). This fork keeps its launcher and selected tooling as a base, then adds Fire OS-specific installation safeguards and experiments. The goal is to make a Fire TV Stick or Cube usable with the CleanYourTV launcher without pretending that Fire OS behaves like ordinary Android TV. It does not.

> **Current status:** the launcher has a public, debug-signed test APK built from commit `ba3a493` in the [2026-11-08 Fire OS launcher test release](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-test-2026-11-08). The three add-ons have German resources and debug-signed test APKs in the [Fire OS add-on test release](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07). Unit tests, lint and release builds passed for those test artifacts. They are not production-signed. A user reports that the Home redirect appears to work, but the exact device/Fire OS version and test scenarios are unrecorded; boot after a full reboot remains unverified.

## What this fork changes

- **Fire OS-safe APK installation.** `tools/install_apk.py` installs an APK as an ordinary app. It does not switch the Home app, enable accessibility, or write secure settings.
- **Protected Amazon components.** Fire TV Home, Amazon Settings and Quick Settings packages are protected from the repository's package-disable and recovery paths. System packages are not uninstalled.
- **Optional Home redirect in the launcher.** `HomeRedirectService` is off by default. It is an experiment, not a supported Fire OS launcher replacement; its behavior depends on the exact Fire OS version and device.
- **Companion add-ons.** Separate test-build apps for TV Hub, Sources and Open on wake are available; see [add-on status](#add-ons).

This fork does **not** currently provide a verified Fire OS autostart solution, a Fire OS settings-cleanup app, or a validated list of "50+" Fire OS settings. The source used for platform detection and package protections does not establish such a list. No unsupported `settings put` commands are added.

## Download and test the launcher

The current test release is here:

**[Download CleanYourTV Fire OS test release](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-test-2026-11-08)**

It contains the existing CleanYourTV launcher as an ordinary APK. It is signed with a debug key for initial sideload testing, not a production signing key. Installing it does **not** make it the Fire TV Home screen and does **not** enable the redirect service.

For Fire OS, use the safe installer rather than the generic Android TV launcher handover script:

```bash
python3 -m venv tools/venv
tools/venv/bin/pip install -r tools/requirements.txt
TV_HOST=<fire-tv-ip> tools/venv/bin/python -I tools/install_apk.py \
  launcher/app/build/outputs/apk/release/app-release.apk
```

Or install the downloaded APK with a sideloading tool you trust. Open the launcher from the Fire TV app grid first. Keep Amazon Home and Settings available.

## Quick start for this fork

| Step | What to do |
|---|---|
| **1. On the Fire TV** | Enable ADB debugging in Developer options. Keep the device on and note its IP address. |
| **2. On your computer** | Clone this fork (`git clone https://github.com/mildman1848/cleanyourtv-fireos.git`), review [`PROMPT.md`](PROMPT.md), then follow [`docs/fireos.md`](docs/fireos.md). |
| **3. Install first** | Install the launcher as an ordinary app. Do not enable Home redirect or disable packages as part of the install. |

Cloning matters: this fork's `tools/disable.sh`, `tools/install_apk.py` and `tools/home_redirect.py` carry the Fire OS safeguards. **Do not run `launcher/build-and-install.sh` on Fire OS**; it changes Home/accessibility settings for other Android TV devices.

Read [the Fire OS guide](docs/fireos.md) and [the Fire OS test prompt](PROMPT.md) before changing device settings. **Do not enable Home redirection on a device you cannot recover.** A successful APK install proves only that the APK installed; it does not prove Home-key handling, reboot behavior or autostart.

## Fire OS support and safety

| Area | Status |
|---|---|
| Install launcher as an ordinary app | Public debug-signed test APK; installation was confirmed by a tester. |
| Disable/restore packages | Fire OS packages are guarded, but use only a model-specific, reviewed list. No new Amazon cleanup list is claimed here. |
| Amazon Home, Settings and Quick Settings | Protected; never disable or uninstall them as part of this fork's procedure. |
| Home-key redirect | Optional, off by default. One user reports that it appears to work; exact Fire TV model and Fire OS version are not recorded, so this is not a general compatibility claim. Keep a recovery path. |
| Start launcher at boot / wake | Not implemented or verified in this fork. |
| Fire OS 5 (2015 Fire TV Box) | `pm disable-user` is refused on the reported device; do not treat this as a supported debloat target. |
| Android TV / Google TV | Use upstream CleanYourTV instead. This fork's documentation and testing target Fire OS. |
| Samsung (Tizen), LG webOS, Roku, VIDAA | Not Android-based and not supported; see [`docs/devices/samsung-tizen.md`](docs/devices/samsung-tizen.md). |

Fire OS behavior differs between models and firmware versions. The project has not tested the Home redirect, the physical remote's Home button, or reboot recovery on every Fire TV model. Compatibility claims must name the exact model and Fire OS version tested.

### Autostart

There is no built-in, verified autostart in this fork. The launcher alone cannot guarantee that Fire OS starts it after reboot or wake. Do not treat the opt-in Home redirect as boot autostart. A separate third-party companion such as [Home on Fire](https://github.com/toolicious/home-on-fire) reports a boot-launch feature, but it is GPL-3.0 software and is **not included or supported by this repository**. Its compatibility and recovery behavior must be checked on the exact device before use.

## Add-ons

These are separate applications, not features built into the launcher:

| Add-on | German translation | APK status |
|---|---|---|
| [TV Hub](addons/tv-hub/) | German resources checked | [Debug-signed test APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |
| [Sources](addons/sources/) | German resources included | [Debug-signed test APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |
| [Open on wake](addons/wake-app/) | German resources included | [Debug-signed test APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |

The release notes list each APK, its version, build/signing status and SHA-256 checksum. Do not install an artifact from a branch build as though it were a published release.

## Build from source

Requirements: JDK 17 and Android SDK platform 34 with the matching build tools. Example for the launcher:

```bash
cd launcher
./gradlew --no-daemon testReleaseUnitTest lintRelease assembleRelease
```

The APK is written to `launcher/app/build/outputs/apk/release/app-release.apk`. Each add-on has its own Gradle project under `addons/` and must be built and checked independently. A successful launcher build says nothing about add-on builds or Fire TV runtime compatibility.

## Relationship to upstream

| Source | Role in this fork |
|---|---|
| [Gathin23/CleanYourTV](https://github.com/Gathin23/cleanyourtv), base commit `d451b175` | Launcher, core tools and project structure. |
| [Clean Your TV app](https://github.com/udhaykumarbala/cleanyourtv-app), commit `03ad20ebec68284a362b9d90690876c18e212286` | Reference for Fire OS detection and protected-package rules. The phone app itself is not part of this fork. |
| [fire-tv-cleanup](https://github.com/itsmeterrylin/fire-tv-cleanup), commit `ab4d9bfbc51e48316d0a19583d579de0b3f44215` | Reference for the opt-in Home redirect concept. |

Detailed source notes, limitations and recovery steps are in [`docs/fireos.md`](docs/fireos.md). This is an independent community fork; it is not affiliated with or endorsed by Amazon or the upstream CleanYourTV maintainer.

## Doing it by hand

On Fire OS use the Fire OS guide, [`docs/fireos.md`](docs/fireos.md), and the reviewed steps in [`PROMPT.md`](PROMPT.md). The generic tool list of upstream is not repeated here; each script's usage is in its first lines.

## The launcher

The launcher needs Android 8.0 (API 26) or newer (`minSdk` in [`launcher/app/build.gradle`](launcher/app/build.gradle)). Fire OS 5 devices are below that. See [`docs/launcher.md`](docs/launcher.md) and, for install errors, [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

## The microphone, and what can be said about it

`tools/privacy.py` reports what the TV says about voice, ACR and telemetry; see [`docs/privacy.md`](docs/privacy.md) for what the audit cannot prove.

## Restoring your TV

Every disabled package can be re-enabled: see [`docs/restore.md`](docs/restore.md).

## After a firmware update

Disabled packages can come back after an update: see [`docs/firmware-updates.md`](docs/firmware-updates.md).

## Questions people ask

See [`docs/faq.md`](docs/faq.md), including [whether this can brick the TV](docs/faq.md#is-this-safe-can-it-brick-the-tv).

## Contact

Questions and bug reports for this fork go to its [issue tracker](https://github.com/mildman1848/cleanyourtv-fireos/issues). Coding agents: read [`AGENTS.md`](AGENTS.md) first.

## Contributing

Contributions should improve the Fire OS-specific use case: model/firmware verification, safe installation, localization, add-on packaging, and reproducible recovery. Please include the exact Fire TV model and Fire OS version for device-dependent claims. Do not add commands that disable Amazon Home/Settings, write undocumented secure settings, or silently enable accessibility.

<details>
<summary><b>Isn't ADB access a security hole?</b></summary>

Network ADB provides powerful shell access. Keep debugging enabled only while you need it, and do not expose ADB to the public internet.

1. On the TV, switch off **USB debugging**, **Network/ADB debugging** and **Wireless debugging** (whichever are present), then revoke debugging authorisations. Wireless debugging may use a separate port; see [the full shutdown procedure](docs/faq.md#isnt-adb-access-a-security-hole).
2. Reboot the TV, then `python3 tools/adb-closed.py <tv ip>` must say the port is closed.

The full steps also explain how to check Wireless debugging's separate port: [docs/faq.md](docs/faq.md#isnt-adb-access-a-security-hole).

</details>

## License

MIT. See [`LICENSE`](LICENSE). The Outfit typeface remains under the SIL Open Font License; see [`launcher/FONT-LICENSE-OFL.txt`](launcher/FONT-LICENSE-OFL.txt).
