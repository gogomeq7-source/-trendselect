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

Die öffentliche Seite benötigt keine Umgebungsvariablen und keine externen Build-Dienste.

## Automatische Trend-Aktualisierung

Die GitHub Action `.github/workflows/update-trends.yml` läuft täglich um 05:23 UTC und kann zusätzlich manuell gestartet werden. `scripts/update_trends.py` liest ausschließlich frei zugängliche RSS-/Atom-Feeds von heise online, tagesschau.de und dem Statistischen Bundesamt. Es benötigt nur die Python-Standardbibliothek und den automatisch vorhandenen `GITHUB_TOKEN`.

Der Generator kategorisiert, bewertet, kürzt und dedupliziert deutschsprachige Meldungen. Bei einem Feed-Ausfall bleiben die zuletzt gültigen Trends erhalten. Neue Daten werden nur bei inhaltlichen Änderungen nach `data/trends.json` geschrieben und dann automatisch committed. GitHub Pages liefert weiterhin ausschließlich statische Dateien aus.

## Affiliate- und Werbemonetarisierung konfigurieren

- Affiliate-Produkte: `products.js` lädt den statischen Katalog aus `data/products.json`, erstellt Kategorien dynamisch und paginiert den Bestand. Dadurch bleibt die GitHub-Pages-Seite auch bei vielen Produkten schnell und benötigt keine Zugangsdaten im Browser.
- Automatisierung: `.github/workflows/update-products.yml` importiert alle sechs Stunden freigegebene Awin-Produktfeeds. Ohne hinterlegte Zugangsdaten bleibt der Katalog unverändert; es werden keine Beispielprodukte erzeugt.
- Awin einrichten: Publisher-Konto eröffnen, TrendSelect als Werbefläche bestätigen und passenden Advertiser-Programmen beitreten. Danach unter **Toolbox → Create-a-Feed** einen Produktfeed erstellen.
- In GitHub unter **Settings → Secrets and variables → Actions** das Repository-Secret `AWIN_PRODUCT_FEED_URLS` anlegen. Als Wert die vollständige Awin-Feed-Download-URL eintragen. Mehrere URLs werden zeilenweise hinterlegt. Diese URLs enthalten den Product-Feed-API-Key und dürfen niemals committed oder öffentlich geteilt werden.
- Optional kann unter **Variables** `PRODUCT_LIMIT` gesetzt werden (Standard: 5000, Maximum: 20000).
- Werbung: Platzhaltertexte und Kontaktadresse der gekennzeichneten Anzeigenflächen in `index.html` durch echte Angaben ersetzen.
- Rechtliches: Sämtliche eckigen Platzhalter in `impressum.html` und `datenschutz.html` durch echte Betreiber- und Dienstangaben ersetzen und vor geschäftlicher Nutzung rechtlich prüfen lassen.
- Statistik: Der eingebundene Minimalzähler verwendet keine Cookies und ist in der Datenschutzvorlage offengelegt.

## Dateien

- `index.html` – semantische Seitenstruktur
- `styles.css` – responsives Layout und Design
- `app.js` – Filter, Suche, Merkliste, Detaildialog, mobiles Menü und Formular
- `products.js` – Produktfilter, Suche, Pagination und sichere Affiliate-Karten
- `scripts/update_products.py` – Awin-Feed-Importer ohne zusätzliche Python-Pakete
- `.nojekyll` – verhindert unerwünschte Jekyll-Verarbeitung auf GitHub Pages
