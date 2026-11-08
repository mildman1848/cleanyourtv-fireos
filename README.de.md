# CleanYourTV für Fire TV (Fire OS)

[English](README.md) · Deutsch

**Ein gezielter Community-Fork, der CleanYourTV für Amazon Fire TV anpasst.** Dieses Repository ist weder das allgemeine Android-TV-/Google-TV-Projekt noch eine offizielle Veröffentlichung des CleanYourTV-Upstreams.

Das ursprüngliche CleanYourTV bleibt das Projekt für Android TV und Google TV: [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv). Dieser Fork übernimmt den Launcher und ausgewählte Werkzeuge als Grundlage und ergänzt Fire-OS-spezifische Installationssicherungen und Experimente. Ziel ist, den CleanYourTV-Launcher auf einem Fire TV Stick oder Cube nutzbar zu machen, ohne so zu tun, als wäre Fire OS normales Android TV. Das wäre eine optimistische, aber falsche Annahme.

> **Aktueller Stand:** Der Launcher hat ein öffentliches, debug-signiertes Test-APK aus Commit `ba3a493` im [Fire-OS-Launcher-Test-Release vom 08.11.2026](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-test-2026-11-08). Die drei Add-ons haben deutsche Ressourcen und debug-signierte Test-APKs im [Fire-OS-Add-on-Test-Release](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07). Unit-Tests, Lint und Release-Builds liefen für diese Test-Artefakte erfolgreich. Es sind keine produktiv signierten APKs. Ein Nutzer berichtet, dass der Home-Redirect offenbar funktioniert; konkretes Gerät, Fire-OS-Version und Testszenarien sind nicht dokumentiert. Der Start nach einem vollständigen Neustart bleibt ungeprüft.

## Was dieser Fork ändert

- **Fire-OS-sichere APK-Installation.** `tools/install_apk.py` installiert eine APK als normale App. Es ändert weder die Home-App noch aktiviert es Bedienungshilfen oder schreibt Secure Settings.
- **Geschützte Amazon-Komponenten.** Fire-TV-Home, Amazon-Einstellungen und Quick Settings sind in den Paket-Deaktivierungs- und Wiederherstellungspfaden geschützt. Systempakete werden nicht deinstalliert.
- **Optionaler Home-Redirect im Launcher.** `HomeRedirectService` ist nach der Installation ausgeschaltet. Er ist ein Experiment, kein unterstützter Ersatz für Fire TVs Home-Bildschirm; das Verhalten hängt vom konkreten Gerät und Fire OS ab.
- **Zusatz-Apps.** Separate Test-Builds für TV Hub, Sources und Open on wake sind verfügbar; siehe [Add-on-Status](#add-ons).

Dieser Fork enthält derzeit **keinen verifizierten Fire-OS-Autostart**, keine Fire-OS-Bereinigungs-App für Einstellungen und keine bestätigte Liste mit „50+“ Fire-OS-Einstellungen. Die als Referenz verwendete Quelle belegt Fire-OS-Erkennung und Paket-Schutz, nicht eine solche Liste. Unbelegte `settings put`-Befehle werden nicht ergänzt.

## Launcher herunterladen und testen

Das aktuelle Test-Release findest du hier:

**[CleanYourTV-Fire-OS-Test-Release herunterladen](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-test-2026-11-08)**

Es enthält den bestehenden CleanYourTV-Launcher als normale APK. Die Signatur stammt von einem Debug-Schlüssel und ist für erste Sideload-Tests gedacht, nicht für eine produktive Veröffentlichung. Die Installation macht den Launcher **nicht** zum Fire-TV-Home-Bildschirm und aktiviert **nicht** den Redirect-Dienst.

Verwende unter Fire OS den sicheren Installer statt des generischen Android-TV-Übergabe-Skripts:

```bash
python3 -m venv tools/venv
tools/venv/bin/pip install -r tools/requirements.txt
TV_HOST=<fire-tv-ip> tools/venv/bin/python -I tools/install_apk.py \
  launcher/app/build/outputs/apk/release/app-release.apk
```

Alternativ kannst du die heruntergeladene APK mit einem Sideload-Werkzeug deiner Wahl installieren. Öffne den Launcher zunächst über die App-Übersicht des Fire TV. Amazon Home und die Einstellungen müssen erreichbar bleiben.

## Schnellstart für diesen Fork

| Schritt | Was zu tun ist |
|---|---|
| **1. Am Fire TV** | ADB-Debugging in den Entwickleroptionen einschalten. Das Gerät eingeschaltet lassen und seine IP-Adresse notieren. |
| **2. Am Computer** | Diesen Fork klonen (`git clone https://github.com/mildman1848/cleanyourtv-fireos.git`), [`PROMPT.md`](PROMPT.md) lesen und anschließend [`docs/fireos.md`](docs/fireos.md) befolgen. |
| **3. Zuerst installieren** | Den Launcher als normale App installieren. Beim Installieren weder Home-Redirect aktivieren noch Pakete deaktivieren. |

Das Klonen ist wichtig: `tools/disable.sh`, `tools/install_apk.py` und `tools/home_redirect.py` aus diesem Fork enthalten die Fire-OS-Sicherungen. **`launcher/build-and-install.sh` nicht unter Fire OS ausführen** — das Skript ändert Home-/Bedienungshilfen-Einstellungen für andere Android-TV-Geräte.

Lies vor Änderungen an Geräteeinstellungen die [Fire-OS-Anleitung](docs/fireos.md) und den [Fire-OS-Testprompt](PROMPT.md). **Aktiviere den Home-Redirect nicht auf einem Gerät, das du nicht wiederherstellen kannst.** Eine erfolgreiche APK-Installation beweist nur, dass die APK installiert wurde — nicht, dass Home-Taste, Neustart oder Autostart funktionieren.

## Fire-OS-Unterstützung und Sicherheit

| Bereich | Stand |
|---|---|
| Launcher als normale App installieren | Öffentliches, mit Debug-Schlüssel signiertes Test-APK; die Installation wurde von einem Tester bestätigt. |
| Pakete deaktivieren/wiederherstellen | Fire-OS-Pakete sind geschützt. Nutze nur eine geprüfte Liste für genau dein Modell; eine neue Amazon-Bereinigungsliste wird hier nicht behauptet. |
| Amazon Home, Einstellungen und Quick Settings | Geschützt; im Rahmen dieses Forks niemals deaktivieren oder deinstallieren. |
| Home-Tasten-Redirect | Optional, standardmäßig aus. Ein Nutzer berichtet, dass er offenbar funktioniert; konkretes Fire-TV-Modell und Fire-OS-Version sind nicht dokumentiert. Das ist keine allgemeine Kompatibilitätszusage. Einen Rückweg bereithalten. |
| Launcher bei Boot/Wake starten | In diesem Fork weder implementiert noch verifiziert. |
| Fire OS 5 (Fire TV Box von 2015) | `pm disable-user` wird auf dem gemeldeten Gerät verweigert; keine unterstützte Debloat-Zielplattform. |
| Android TV / Google TV | Dafür den Upstream CleanYourTV verwenden. Dokumentation und Tests dieses Forks zielen auf Fire OS. |

Fire OS unterscheidet sich je nach Modell und Firmware. Der Home-Redirect, die physische Home-Taste der Fernbedienung und die Wiederherstellung nach einem Neustart wurden nicht auf jedem Fire-TV-Modell getestet. Kompatibilitätsaussagen müssen das konkret getestete Modell und die Fire-OS-Version nennen.

### Autostart

Dieser Fork hat keinen eingebauten, verifizierten Autostart. Der Launcher allein garantiert nicht, dass Fire OS ihn nach Neustart oder Aufwachen startet. Der optionale Home-Redirect ist kein Boot-Autostart. Ein separates Drittanbieter-Programm wie [Home on Fire](https://github.com/toolicious/home-on-fire) gibt an, eine Startfunktion beim Booten zu haben, steht aber unter GPL-3.0 und ist **nicht Teil oder Bestandteil des Supports dieses Repositories**. Kompatibilität und Wiederherstellung müssen auf dem konkreten Gerät geprüft werden.

## Add-ons

Die folgenden Zusatz-Apps sind getrennte Anwendungen und keine in den Launcher eingebauten Funktionen:

| Add-on | Deutsche Übersetzung | APK-Status |
|---|---|---|
| [TV Hub](addons/tv-hub/) | Deutsche Ressourcen geprüft | [Debug-signiertes Test-APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |
| [Sources](addons/sources/) | Deutsche Ressourcen enthalten | [Debug-signiertes Test-APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |
| [Open on wake](addons/wake-app/) | Deutsche Ressourcen enthalten | [Debug-signiertes Test-APK](https://github.com/mildman1848/cleanyourtv-fireos/releases/tag/fireos-addons-test-2026-11-07) |

Die Release-Notizen nennen jede APK, ihre Version, Build- und Signaturstatus sowie die SHA-256-Prüfsumme. Installiere keinen Branch-Build, als wäre er ein veröffentlichtes Release.

## Aus dem Quellcode bauen

Voraussetzungen: JDK 17 und Android-SDK-Plattform 34 mit passenden Build Tools. Beispiel für den Launcher:

```bash
cd launcher
./gradlew --no-daemon testReleaseUnitTest lintRelease assembleRelease
```

Die APK liegt danach unter `launcher/app/build/outputs/apk/release/app-release.apk`. Jedes Add-on hat ein eigenes Gradle-Projekt unter `addons/` und muss separat gebaut und geprüft werden. Ein erfolgreicher Launcher-Build sagt nichts über Add-on-Builds oder Laufzeit-Kompatibilität mit Fire TV aus.

## Verhältnis zum Upstream

| Quelle | Rolle in diesem Fork |
|---|---|
| [Gathin23/CleanYourTV](https://github.com/Gathin23/cleanyourtv), Basis-Commit `d451b175` | Launcher, Kernwerkzeuge und Projektstruktur. |
| [Clean Your TV app](https://github.com/udhaykumarbala/cleanyourtv-app), Commit `03ad20ebec68284a362b9d90690876c18e212286` | Referenz für Fire-OS-Erkennung und geschützte Pakete. Die Smartphone-App selbst ist nicht Teil dieses Forks. |
| [fire-tv-cleanup](https://github.com/itsmeterrylin/fire-tv-cleanup), Commit `ab4d9bfbc51e48316d0a19583d579de0b3f44215` | Referenz für das Konzept des optionalen Home-Redirects. |

Ausführliche Quellenhinweise, Einschränkungen und Wiederherstellungsschritte stehen in [`docs/fireos.md`](docs/fireos.md). Dies ist ein unabhängiger Community-Fork, weder mit Amazon noch mit dem CleanYourTV-Upstream-Maintainer verbunden oder von ihnen empfohlen.

## Mitwirken

Beiträge sollten den konkreten Fire-OS-Einsatz verbessern: Geräte- und Firmware-Prüfungen, sichere Installation, Übersetzungen, Add-on-Paketierung und reproduzierbare Wiederherstellung. Bitte nenne bei geräteabhängigen Aussagen das genaue Fire-TV-Modell und die Fire-OS-Version. Keine Befehle hinzufügen, die Amazon Home/Einstellungen deaktivieren, undokumentierte Secure Settings schreiben oder Bedienungshilfen unbemerkt aktivieren.

<details>
<summary><b>Ist ADB-Zugriff nicht ein Sicherheitsrisiko?</b></summary>

Netzwerk-ADB ermöglicht weitreichenden Shell-Zugriff. Lass Debugging nur eingeschaltet, solange du es brauchst, und mache ADB niemals aus dem öffentlichen Internet erreichbar.

1. Am Fernseher **USB-Debugging**, **Netzwerk-/ADB-Debugging** und **Wireless debugging** ausschalten (je nachdem, was vorhanden ist) und Debugging-Berechtigungen widerrufen. Wireless debugging kann einen eigenen Port verwenden; siehe [die vollständige Abschalt-Anleitung](docs/faq.md#isnt-adb-access-a-security-hole).
2. Den Fernseher neu starten und dann `python3 tools/adb-closed.py <tv ip>` ausführen. Das Werkzeug muss melden, dass Port 5555 geschlossen ist.

Die vollständigen Schritte erklären auch die Prüfung des separaten Wireless-Debugging-Ports: [docs/faq.md](docs/faq.md#isnt-adb-access-a-security-hole).

</details>

## Lizenz

MIT, siehe [`LICENSE`](LICENSE). Die Schrift Outfit bleibt unter der SIL Open Font License; siehe [`launcher/FONT-LICENSE-OFL.txt`](launcher/FONT-LICENSE-OFL.txt).
