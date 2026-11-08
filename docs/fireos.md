# Fire OS (test release)

**Status: public test release; the current launcher APK is the [2026-11-08 build](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-test-2026-11-08) from commit `ba3a493`. A user reports that the Home redirect appears to work on their Fire TV.** The exact model, Fire OS version and test scenarios were not recorded, and the result has not been independently reproduced by a maintainer; do not treat it as a general compatibility claim. The tests without a TV cover fake devices and Java redirect logic only. **There is no separate boot autostart:** starting the launcher after a full reboot has not been reported or verified.

## Sources and exact commits

| Source | Commit | What was used |
|---|---|---|
| [CleanYourTV](https://github.com/Gathin23/cleanyourtv) | `d451b175` (this repo's base) | Everything not named below |
| [udhaykumarbala/cleanyourtv-app](https://github.com/udhaykumarbala/cleanyourtv-app) | `03ad20ebec68284a362b9d90690876c18e212286` | `core/planner/.../PlatformFacts.kt` (`FireOs`: the two protected homes `com.amazon.tv.launcher` and `com.amazon.firehomestarter`, and how a Fire OS set is recognised: maker or brand Amazon, an `AFT` model code, or one of those homes installed); `SwitchOffRule.kt` (Fire OS's homes are never switched off); `core/ops/.../HelperLines.kt` (the compare-and-set edit of the accessibility list that `tools/home_redirect.py` follows) |
| [itsmeterrylin/fire-tv-cleanup](https://github.com/itsmeterrylin/fire-tv-cleanup) | `ab4d9bfbc51e48316d0a19583d579de0b3f44215` | The `HomeRedirectService` concept (watch window changes, open the launcher over Amazon's Home), its manifest entry and accessibility XML |

What the app source proves is **package operations and platform detection**: which packages are never
disabled, and how to tell Fire OS. It contains no list of Fire OS `settings put` changes, so none were
ported, and this repo makes no claim of "50+ Fire OS settings". The donor's per-model lists were not merged
either (see "Deferred").

## What this adds

- **Protected packages.** `com.amazon.tv.launcher`, `com.amazon.firehomestarter`, `com.amazon.tv.settings`,
  `com.amazon.tv.settings.v2` and `com.amazon.tv.quicksettings` join the core-package block that
  `tools/disable.sh`, `disable.ps1` and `check.py --fix` refuse (`tools/recovery.py` `CORE_RE`, kept
  identical by `tests/test_core_packages.py`). Disabling stays `pm disable-user --user 0`; nothing is
  uninstalled.
- **`tools/install_apk.py`**: one safe way to put an APK on a TV as an ordinary app, for the launcher and
  for add-ons. It checks the file locally (a real zip with a manifest and dex, under 150 MB), copies it with
  `b64push.py` to a unique `/data/local/tmp/cytv-<random>-<name>.apk`, runs a quoted `pm install -r`, requires
  `Success`, and only then removes the staging file; after a failure the file stays and its path is in the
  message. It changes no Home, accessibility or secure setting. The only permission it can grant, and only on
  request, is `ACCESS_FINE_LOCATION` (`--grant` with `--package`); `WRITE_SECURE_SETTINGS` and anything
  accessibility-related are refused. `launcher/build-and-install.sh` and the add-on `install.sh` scripts keep
  their own side effects and are **not** routed through it; on Fire OS use the helper (below).
- **`HomeRedirectService`** in the existing launcher: an accessibility service with no screen of its own, so
  the APK stays under the CI size gate. You switch it on and off in Android's Accessibility settings or with
  the helper (below).
- **`tools/home_redirect.py`**: `status`, `enable --confirm`, `disable` for that service.

## Install the launcher as an ordinary app

```
cd launcher && ./gradlew --no-daemon assembleRelease     # JDK 17, Android SDK 34
cd ..
TV_HOST=192.168.1.50 tools/venv/bin/python -I tools/install_apk.py launcher/app/build/outputs/apk/release/app-release.apk
```

The launcher then appears in the apps row. It is not Home, and the redirect is off.
`launcher/build-and-install.sh` also writes accessibility and secure settings: do not run it on Fire OS.

## Home redirect: opt-in, and how to undo it

Fire OS does not hand Home to a third-party launcher by default. The redirect is an accessibility service
that opens the launcher when Amazon's Home comes up. Amazon's launcher stays enabled the whole time.

- **Off by default.** Install does not turn it on. Turning it on is your choice, one of:
  - Fire TV's own Settings > Accessibility > Home redirect (Fire OS) > on (the system asks you to confirm);
  - `TV_HOST=<tv ip> tools/home_redirect.py enable --confirm` (refuses on a TV that is not Fire OS or
    without the launcher installed); read the state with `status`.
- **Other services are kept.** Turning it on or off edits only this service's entry in
  `enabled_accessibility_services`, with a compare-and-set; every other service stays. Turning off never
  touches the global `accessibility_enabled` switch.
- **Amazon Settings fail closed.** Amazon's Home flashes up on the way into Settings. A window of Amazon's
  settings or quick settings stops all redirecting, with no timer; it resumes only when you open the launcher
  again from the apps row. After Settings, Home stays Amazon's until you do.
- **No autostart.** Nothing opens the launcher at boot. With the service on, the launcher opens when
  Amazon's Home next comes up, not before.

**Undo, in the order to try:**
1. `TV_HOST=<tv ip> tools/home_redirect.py disable` (read the state with `status`).
2. On the TV: Settings > Accessibility > Home redirect (Fire OS) > off.
3. No ADB and no usable screen: Settings > Applications > the launcher > Force stop, then Uninstall; the
   launcher is ours and removable, Amazon's packages are never touched.
4. Check afterwards that Amazon's Home opens and the real remote works.

Real-device checks to run, with the owner, before calling it working: Home opens the launcher; the real
remote's Home button works (an injected key proves nothing); Amazon Settings open and close normally; the TV
reboots and ADB comes back; the redirect is switched off by `disable`.

## Caveats

- Fire OS does not pass the Home key to accessibility services, so the redirect watches windows. Whether
  that holds on a given Fire OS version is unknown here; the donor measured it on one Fire OS 8 stick.
- The 2015 Fire TV Box (Fire OS 5) refuses `pm disable-user` altogether.
- Fire OS can refuse `pm disable-user` for some packages (a `SecurityException`); stop and say so.
- The service's name and description are English only in this release.

## Deferred

- The donor's per-model lists (`examples/*` in fire-tv-cleanup) were not merged: current lists here already
  cover Fire TV models and a Fire OS 8 refusal seen on one model is not a rule for the others.
- No Fire OS `settings put` cleanups: no source here proves any.
- Routing `launcher/build-and-install.sh` and add-on installers through `tools/install_apk.py`.
- An on/off screen inside the launcher and an opt-in open at boot: both were left out of this release to
  keep the APK under the size gate.

## Build and install the three add-ons

JDK 17 and Android SDK 34. `<tv ip>` is your TV; each command installs only the named APK.

| Add-on | Build (in its folder) | APK | Signed with |
|---|---|---|---|
| TV Hub | `./gradlew assembleDebug` | `addons/tv-hub/app/build/outputs/apk/debug/app-debug.apk` | debug key (release is unsigned unless `TVHUB_KEYSTORE*` are set) |
| Sources | `./gradlew assembleRelease` | `addons/sources/app/build/outputs/apk/release/app-release.apk` | debug key |
| Open on wake | `./gradlew assembleRelease` | `addons/wake-app/app/build/outputs/apk/release/app-release.apk` | debug key |

```
TV_HOST=<tv ip> tools/venv/bin/python -I tools/install_apk.py addons/sources/app/build/outputs/apk/release/app-release.apk
```

These are published test builds, not production-signed or reproducible releases; all three include German resources selected when the TV's language is German. Build TV Hub with `assembleDebug` for an installable test APK; `assembleRelease` produces an unsigned APK unless a release key is supplied.
Open on wake needs its `build-and-install.sh` for the overlay grant. **That script changes TV app permissions/settings** (`SYSTEM_ALERT_WINDOW`, possible vendor auto-start appops and a foreground service); review it before running. No signing key is kept in the repo.
