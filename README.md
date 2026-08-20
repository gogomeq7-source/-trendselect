# TrendSelect

Eine responsive, barrierearme Trend-Discovery-Website als statische Web-App. Sie läuft ohne Build-Schritt und kann direkt über GitHub Pages bereitgestellt werden.

## Lokal starten

`index.html` direkt öffnen oder im Projektordner einen lokalen Server starten, zum Beispiel:

```bash
python -m http.server 8000
```

Danach `http://localhost:8000` öffnen.

## GitHub Pages veröffentlichen

1. Alle Dateien in ein GitHub-Repository committen und pushen.
2. Unter **Settings → Pages** bei **Build and deployment** die Quelle **Deploy from a branch** wählen.
3. Branch `main`, Ordner `/ (root)` auswählen und speichern.

Die Seite benötigt keine Umgebungsvariablen und keine externen Build-Dienste.

## Automatische Trend-Aktualisierung

Die GitHub Action `.github/workflows/update-trends.yml` läuft täglich um 05:23 UTC und kann zusätzlich manuell gestartet werden. `scripts/update_trends.py` liest ausschließlich frei zugängliche RSS-/Atom-Feeds von heise online, tagesschau.de und dem Statistischen Bundesamt. Es benötigt nur die Python-Standardbibliothek und den automatisch vorhandenen `GITHUB_TOKEN`.

Der Generator kategorisiert, bewertet, kürzt und dedupliziert deutschsprachige Meldungen. Bei einem Feed-Ausfall bleiben die zuletzt gültigen Trends erhalten. Neue Daten werden nur bei inhaltlichen Änderungen nach `data/trends.json` geschrieben und dann automatisch committed. GitHub Pages liefert weiterhin ausschließlich statische Dateien aus.

## Affiliate- und Werbemonetarisierung konfigurieren

- Werbung und Affiliate: Platzhaltertexte, Kontaktadresse und `href` der gekennzeichneten Partnerlinks in `index.html` ersetzen. `rel="sponsored noopener"` beibehalten.
- Rechtliches: Sämtliche eckigen Platzhalter in `impressum.html` und `datenschutz.html` durch echte Betreiber- und Dienstangaben ersetzen und vor geschäftlicher Nutzung rechtlich prüfen lassen.
- Statistik: Der eingebundene Minimalzähler verwendet keine Cookies und ist in der Datenschutzvorlage offengelegt.

## Dateien

- `index.html` – semantische Seitenstruktur
- `styles.css` – responsives Layout und Design
- `app.js` – Filter, Suche, Merkliste, Detaildialog, mobiles Menü und Formular
- `.nojekyll` – verhindert unerwünschte Jekyll-Verarbeitung auf GitHub Pages
