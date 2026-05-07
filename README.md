# Source Relevance Scoring Algorithm

> **FOM Hackathon – Algorithmen & Datenstrukturen 2026**

Dieses Tool bewertet automatisch die Relevanz von PDF-Quellen anhand einer gewichteten Keyword-Analyse. Jede PDF-Datei erhält einen numerischen Score – je häufiger und wichtiger die gesuchten Begriffe im Dokument vorkommen, desto höher der Score. Die Quellen werden anschließend nach Relevanz absteigend sortiert und als Tabelle ausgegeben.

---

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Projektstruktur](#projektstruktur)
- [Schnellstart](#schnellstart)
- [Flussdiagramm](#flussdiagramm)
- [Algorithmus – Detaillierte Erklärung](#algorithmus--detaillierte-erklärung)
- [Score-Formel](#score-formel)
- [Abweichungsanalyse](#abweichungsanalyse)
- [Beispiel](#beispiel)
- [Testdokumentation](#testdokumentation)
- [Annahmen & Einschränkungen](#annahmen--einschränkungen)
- [Reflexion](#reflexion)
- [Ausgabe](#ausgabe)

---

## Voraussetzungen

Python 3.10+ sowie folgende Pakete:

```bash
pip install pypdf pandas tabulate openpyxl
```

| Paket      | Verwendung                              |
|------------|-----------------------------------------|
| `pypdf`    | Text aus PDF-Dateien extrahieren        |
| `pandas`   | Ergebnistabelle erstellen & sortieren   |
| `tabulate` | Formatierte Konsolenausgabe der Tabelle |
| `openpyxl` | XLSX-Export mit Formatierung            |

---

## Projektstruktur

```
source_analyzer/
│
├── quellenbewertung.py           # Hauptskript (der Algorithmus)
│
├── stichpunkte.txt               # Keyword-Datei (eine Zeile = ein Keyword, wichtigstes zuerst)
├── simple_stichpunkte.txt        # Vereinfachte Keyword-Datei für Tests
│
├── sources/                      # Ordner mit den zu analysierenden PDFs (echte Quellen)
├── simple_sources/               # Ordner mit Test-PDFs
│   ├── test_A.pdf                # Normalfall: enthält mehrere Keywords
│   ├── test_B.pdf                # Normalfall: enthält wenige Keywords
│   ├── test_C.pdf                # Randfall: enthält nur 1 Keyword mit Treffer
│   ├── test_hyphenation.pdf      # Randfall: Keywords über Silbentrennung
│   ├── chinese.pdf               # Fehlerfall: fremdsprachige PDF (kein Treffer erwartet)
│   └── image_pdf.pdf             # Fehlerfall: bild-basierte PDF (Score = 0 erwartet)
│
├── result.csv                    # Ausgabe: Ergebnistabelle als CSV
├── result.xlsx                   # Ausgabe: Ergebnistabelle als Excel
├── erwartet.csv                  # Erwartete Testergebnisse (für simple_sources)
├── source_analyzer.drawio.jpg    # Flussdiagramm (vollständig, inkl. Fehlerpfade)
└── Abweichungsanalyse.docx       # Konzept der relativen Score-Bewertung
```

---

## Schnellstart

1. PDFs in den Ordner `sources/` legen
2. Keywords in `stichpunkte.txt` eintragen (eine Zeile pro Keyword, **wichtigstes zuerst**)
3. Skript ausführen:

```bash
python quellenbewertung.py
```

Das Skript gibt die Ergebnistabelle in der Konsole aus und exportiert `result.csv` sowie `result.xlsx`.

Für den Test mit einfachen Testdaten den Ordner-Pfad im Skript auf `simple_sources/` und die Keyword-Datei auf `simple_stichpunkte.txt` umstellen.

---

## Flussdiagramm

Das folgende Diagramm zeigt den vollständigen Ablauf des Algorithmus inkl. aller Fehler- und Sonderpfade:

![Flussdiagramm des Algorithmus](./source_analyzer.drawio.jpg)

**Erläuterung der wichtigsten Pfade:**
- **Fehlerfall 1 – Stichpunkt-Datei fehlt/leer:** Programm bricht sofort ab.
- **Fehlerfall 2 – Ordner nicht gefunden:** Programm bricht ab bevor nach PDFs gesucht wird.
- **Fehlerfall 3 – Keine PDFs im Ordner:** Programm bricht mit Fehlermeldung ab.
- **Sonderfall – PDF nicht lesbar:** Warnung wird ausgegeben, Score = 0, Programm läuft weiter zur nächsten PDF.
- **Hauptschleife:** Für jede PDF werden alle Keywords durchlaufen, Treffer gespeichert und der Score berechnet.
- **Abschluss:** Erst wenn alle PDFs und alle Keywords verarbeitet wurden, wird die Tabelle erstellt, sortiert und ausgegeben.

---

## Algorithmus – Detaillierte Erklärung

Der Algorithmus besteht aus **5 Hauptschritten**.

---

### Schritt 1: Keywords laden

**Funktion:** `load_keywords(file_path: Path) → list[str]`

Die Keyword-Datei (z. B. `stichpunkte.txt`) wird Zeile für Zeile eingelesen. Leere Zeilen werden ignoriert. Die Reihenfolge der Keywords ist **entscheidend**, da sie direkt die Gewichtung bestimmt.

**Beispiel `stichpunkte.txt`:**
```
neural network
deep learning
machine learning
training data
Python
schreibtisch
```

Wenn die Datei nicht existiert oder leer ist, bricht das Programm mit einem Fehler ab (`sys.exit(1)`).

---

### Schritt 1b: Gewichte berechnen

**Funktion:** `calculate_weights(keywords: list[str]) → dict[str, int]`

- Das **erste** Keyword (wichtigstes) bekommt das **höchste** Gewicht `n`
- Das **letzte** Keyword bekommt das **niedrigste** Gewicht `1`

**Formel:**

```
Gewicht(keyword_i) = n - i
```

`n` = Gesamtanzahl der Keywords, `i` = 0-basierter Index.

**Beispiel** (6 Keywords → n = 6):

| Index | Keyword          | Gewicht |
|-------|------------------|---------|
| 0     | neural network   | 6       |
| 1     | deep learning    | 5       |
| 2     | machine learning | 4       |
| 3     | training data    | 3       |
| 4     | Python           | 2       |
| 5     | schreibtisch     | 1       |

---

### Schritt 2: PDF-Ordner laden

**Funktion:** `load_pdfs(folder_path: Path) → list[Path]`

Alle `.pdf`-Dateien aus dem konfigurierten Ordner werden alphabetisch sortiert geladen. Wird der Ordner nicht gefunden oder enthält keine PDFs, bricht das Programm ab.

---

### Schritt 3: Text extrahieren

**Funktion:** `extract_text(pdf_path: Path) → str`

Der Text wird mit `pypdf.PdfReader` Seite für Seite extrahiert. Zwei Korrekturen werden angewendet:

#### Korrektur 1 – Silbentrennungs-Fix
```python
re.sub(r'-\n', '', raw_text)
```
Entfernt Bindestrich + Zeilenumbruch, sodass getrennte Wörter wieder zusammengefügt werden.

#### Korrektur 2 – Zeilenumbruch → Leerzeichen
```python
re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)
```
Verhindert, dass Wörter über Zeilengrenzen als separate Tokens gezählt werden.

**Fehlerfall:** Bei nicht lesbaren PDFs (z. B. Bild-PDFs) gibt die Funktion einen leeren String zurück → Score = 0.

---

### Schritt 3b: Keyword-Treffer zählen

**Funktion:** `count_occurrences(keyword: str, text: str) → int`

- **Case-insensitive** → `text.lower()`
- **Word-boundary-aware** → `\b`-Anker verhindern Teilstring-Treffer

```python
pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
```

Ergebnis: `hits[filename][keyword]` speichert die Trefferanzahl je PDF und Keyword.

---

### Schritt 4: Score berechnen

```python
score = sum(
    keyword_hits[keyword] * weights[keyword]
    for keyword in keywords
)
```

PDFs mit häufig vorkommenden, hochgewichteten Keywords erhalten einen höheren Score.

---

### Schritt 5: Tabelle bauen & sortieren

Ergebnisse werden in einem `pandas.DataFrame` zusammengeführt, **absteigend nach Score** sortiert. Der Index entspricht dem **Relevanz-Rang** (Rang 1 = relevanteste Quelle).

```python
table = table.sort_values(by="Score", ascending=False)
table.index += 1
```

---

## Score-Formel

Die vollständige mathematische Formel für den Score einer Quelle Q mit n Keywords:

$$Score(Q) = \sum_{i=0}^{n-1} count(keyword_i, Q) \times (n - i)$$

| Symbol | Bedeutung |
|--------|-----------|
| Q | Die zu bewertende Quelle (PDF-Datei) |
| n | Gesamtanzahl der Keywords |
| i | 0-basierter Index des Keywords |
| count(keyword_i, Q) | Anzahl der exakten Treffer von keyword_i in Quelle Q |
| n - i | Gewicht des Keywords |

---

## Abweichungsanalyse

### Wann ist eine Quelle gut?

Ein Score von z. B. **42** sagt alleine nichts aus. Bei 3 Keywords ist 42 hervorragend, bei 20 Keywords ist 42 schwach. Deshalb wird ein **relativer Vergleichswert** benötigt.

### Schritt 1: Maximalen Score berechnen

Stellt man sich vor, jedes Keyword kommt in der Quelle **genau einmal** vor (das absolute Minimum für Relevanz), ist der **theoretische Maximal-Score**:

$$Score_{max} = \frac{n \times (n + 1)}{2}$$

**Beispiel** mit 6 Keywords:

$$Score_{max} = \frac{6 \times 7}{2} = 21$$

### Schritt 2: Relativen Score berechnen

$$Score_{rel}(Q) = \frac{Score(Q)}{Score_{max}} \times 100$$

Ein relativer Score von **100%** bedeutet, dass jedes Keyword genau einmal vorkommt. Alles darüber zeigt, dass Keywords mehrfach vorkommen – die Quelle ist **überdurchschnittlich relevant**.

### Schritt 3: Klassifikation

| Stufe | Relativer Score | Interpretation |
|-------|-----------------|----------------|
| 🟢 **Sehr gut** | > 100% | Keywords kommen sehr häufig vor – Kernquelle |
| 🟡 **Gut** | 50 – 100% | Klar relevant, deckt das Thema gut ab |
| 🟠 **Ausreichend** | 20 – 50% | Randthema, nur bedingt nutzbar |
| 🔴 **Schwach** | < 20% | Kaum relevant, besser weglassen |

### Warum ist das fair?

Ohne Normalisierung würde ein **1000-seitiges Buch** immer gewinnen, weil jedes Keyword dort häufiger vorkommt als in einem 5-seitigen Paper. Der relative Score macht die Quellen **unabhängig von ihrer Länge und der Keyword-Anzahl** vergleichbar.

---

## Beispiel

**Keyword-Datei (`stichpunkte.txt`):**
```
neural network      → Gewicht 6
deep learning       → Gewicht 5
machine learning    → Gewicht 4
training data       → Gewicht 3
Python              → Gewicht 2
schreibtisch        → Gewicht 1
```

**Angenommene Treffer für eine PDF (`paper_A.pdf`):**

| Keyword          | Treffer | Gewicht | Produkt |
|------------------|---------|---------|---------|
| neural network   | 12      | 6       | 72      |
| deep learning    | 8       | 5       | 40      |
| machine learning | 5       | 4       | 20      |
| training data    | 3       | 3       | 9       |
| Python           | 1       | 2       | 2       |
| schreibtisch     | 0       | 1       | 0       |
| **Score**        |         |         | **143** |

---

## Testdokumentation

### Verwendete Test-Konfiguration

- **Keyword-Datei:** `simple_stichpunkte.txt`
- **Keyword-Reihenfolge und Gewichte:**

| Index | Keyword        | Gewicht |
|-------|----------------|---------|
| 0     | neural network | 4       |
| 1     | DEEP LEARNINg  | 3       |
| 2     | deep learning  | 2       |
| 3     | Python         | 1       |

> **Hinweis zu den Keywords:** `DEEP LEARNINg` und `deep learning` sind bewusst doppelt eingetragen (unterschiedliche Schreibweise), um das case-insensitive Verhalten zu testen. Beide werden intern zu `deep learning` normalisiert und zählen separat.

- **Test-PDFs:** `simple_sources/`
- **Erwartete Ergebnisse:** `erwartet.csv`

---

### Testkategorie 1 – Normalfall

**Ziel:** Prüfen ob der Algorithmus bekannte Keyword-Treffer korrekt zählt und den Score richtig berechnet.

#### Testfall N1 – Mehrere Keywords vorhanden (`test_A.pdf`)

| Feld | Wert |
|------|------|
| Input | `test_A.pdf` + `simple_stichpunkte.txt` |
| Erwartete Treffer | neural network: 4, DEEP LEARNINg: 1, deep learning: 1, Python: 1 |
| Erwarteter Score | 22 |
| Tatsächliche Treffer | neural network: 4, DEEP LEARNINg: 1, deep learning: 1, Python: 1 |
| Tatsächlicher Score | 22 |
| Ergebnis | ⬜ Bestanden |
| Abweichung | keine |

#### Testfall N2 – Wenige Keywords vorhanden (`test_B.pdf`)

| Feld | Wert |
|------|------|
| Input | `test_B.pdf` + `simple_stichpunkte.txt` |
| Erwartete Treffer | neural network: 0, DEEP LEARNINg: 3, deep learning: 3, Python: 2 |
| Erwarteter Score | 17 |
| Tatsächliche Treffer | neural network: 0, DEEP LEARNINg: 3, deep learning: 3, Python: 2 |
| Tatsächlicher Score | 17 |
| Ergebnis | ✅Bestanden |
| Abweichung | keine |

---

### Testkategorie 2 – Randfall

**Ziel:** Prüfen wie der Algorithmus mit Grenzfällen umgeht (Silbentrennung, fast keine Treffer).

#### Testfall R1 – Silbentrennung (`test_hyphenation.pdf`)

Testet ob der Silbentrennungs-Fix korrekt funktioniert. Wörter wie `neu-\nral network` sollen als `neural network` erkannt werden.

| Feld | Wert |
|------|------|
| Input | `test_hyphenation.pdf` + `simple_stichpunkte.txt` |
| Erwartete Treffer | neural network: 2, DEEP LEARNINg: 2, deep learning: 2, Python: 1 |
| Erwarteter Score | 19 |
| Tatsächliche Treffer | neural network: 2, DEEP LEARNINg: 2, deep learning: 2, Python: 1 |
| Tatsächlicher Score | 19 |
| Ergebnis | ✅Bestanden |
| Abweichung | keine |

#### Testfall R2 – Nur 1 Keyword trifft (`test_C.pdf`)

| Feld | Wert |
|------|------|
| Input | `test_C.pdf` + `simple_stichpunkte.txt` |
| Erwartete Treffer | neural network: 0, DEEP LEARNINg: 0, deep learning: 0, Python: 1 |
| Erwarteter Score | 1 |
| Tatsächliche Treffer | neural network: 0, DEEP LEARNINg: 0, deep learning: 0, Python: 1 |
| Tatsächlicher Score | 1 |
| Ergebnis | ✅Bestanden |
| Abweichung | keine |

---

### Testkategorie 3 – Fehlerfall

**Ziel:** Prüfen ob das Programm bei problematischen Eingaben robust reagiert (kein Absturz, Score = 0).

#### Testfall F1 – Bild-basierte PDF (`image_pdf.pdf`)

Bild-PDFs enthalten keinen Text-Layer → `extract_text()` gibt leeren String zurück → Score muss 0 sein.

| Feld | Wert |
|------|------|
| Input | `simple_sources/image_pdf.pdf` + `simple_stichpunkte.txt` |
| Erwartetes Verhalten | Kein Absturz, alle Treffer = 0, Score = 0 |
| Tatsächliches Verhalten | Kein Absturz, alle Treffer = 0, Score = 0 |
| Tatsächlicher Score | 0 |
| Ergebnis | ✅ Bestanden |
| Abweichung | keine |

#### Testfall F2 – Fremdsprachige PDF (`chinese.pdf`)

Eine PDF auf Chinesisch enthält keine englischen Keywords → alle Treffer = 0, Score = 0.

| Feld | Wert |
|------|------|
| Input | `simple_sources/chinese.pdf` + `simple_stichpunkte.txt` |
| Erwartetes Verhalten | Kein Absturz, alle Treffer = 0, Score = 0 |
| Tatsächliches Verhalten | Kein Absturz, alle Treffer = 0, Score = 0 |
| Tatsächlicher Score | 0 |
| Ergebnis | ✅ Bestanden |
| Abweichung | keine |

#### Testfall F3 – Leerer PDF-Ordner

| Feld | Wert |
|------|------|
| Input | Leerer Ordner (keine PDFs vorhanden) |
| Erwartetes Verhalten | Fehlermeldung: „FEHLER: Kein PDF gefunden", Programm bricht ab |
| Tatsächliches Verhalten | Fehlermeldung: „FEHLER: Kein PDF gefunden" |
| Ergebnis | ✅ Bestanden |
| Abweichung | keine |

---

### Gesamtergebnis Testdurchlauf

| Testfall | Kategorie | Ergebnis |
|----------|-----------|----------|
| N1 – test_A.pdf | Normalfall | ✅ |
| N2 – test_B.pdf | Normalfall | ✅ |
| R1 – test_hyphenation.pdf | Randfall | ✅ |
| R2 – test_C.pdf | Randfall | ✅ |
| F1 – image_pdf.pdf | Fehlerfall | ✅ |
| F2 – chinese.pdf | Fehlerfall | ✅ |
| F3 – Leerer Ordner | Fehlerfall | ✅ |

---

## Annahmen & Einschränkungen

| ID  | Typ           | Beschreibung                                                                                                                                                   |
|-----|---------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| A1  | Annahme       | Quellen sind auf Englisch verfasst                                                                                                                             |
| A2  | Annahme       | PDFs sind text-basiert (nicht gescannt / bild-basiert)                                                                                                         |
| A3  | Annahme       | PDFs sind einspaltig aufgebaut – mehrspaltige Layouts werden nicht unterstützt                                                                                 |
| L1  | Einschränkung | Keine Unterscheidung zwischen Groß-/Kleinschreibung (case-insensitive)                                                                                         |
| L2  | Einschränkung | Kein Stemming/Lemmatisierung – `"learning"` ≠ `"learn"`                                                                                                        |
| L3  | Einschränkung | Bild-basierte PDFs liefern leeren Text → Score = 0                                                                                                             |
| L4  | Einschränkung | Keyword-Reihenfolge bestimmt vollständig die Gewichtung                                                                                                        |
| L5  | Einschränkung | Häufigkeit ≠ Relevanz – der Kontext der Erwähnung wird nicht bewertet                                                                                          |
| L6  | Einschränkung | Mehrspaltige PDFs: `pypdf` extrahiert Text zeilenweise ohne Spaltenlogik – bei zweispaltigen Layouts können Wörter aus verschiedenen Spalten vermischt werden, was zu fehlerhaften Treffern oder verpassten Keywords führen kann |
| L7  | Einschränkung | Kopf- und Fußzeilen werden nicht herausgefiltert – Keywords die dort vorkommen (z. B. Titel, Seitenzahlen, Zeitschriftenname) werden mitgezählt und erhöhen den Score künstlich |

---

## Reflexion

### Wo ist der Algorithmus ineffizient?

Der Algorithmus verarbeitet jede PDF vollständig sequenziell: Für jede PDF wird der gesamte Text extrahiert und anschließend für jedes einzelne Keyword ein separater Regex-Suchlauf durchgeführt. Das bedeutet bei **P** PDFs und **K** Keywords werden **P × K** Regex-Operationen ausgeführt – jede davon durchläuft den gesamten Text der jeweiligen PDF.

Konkret ineffizient ist das in zwei Punkten:

- **Kein Caching des extrahierten Texts:** Wird das Skript mehrfach mit unterschiedlichen Keyword-Dateien auf denselben PDFs ausgeführt, wird der PDF-Text jedes Mal neu extrahiert, obwohl er sich nicht geändert hat. Eine einmalige Vorverarbeitung (Preprocessing) mit gespeichertem Text würde die Laufzeit bei Wiederholungen drastisch senken.
- **Einzelne Regex-Läufe pro Keyword:** Alle Keywords werden nacheinander als separate Regex-Muster auf denselben Text angewendet. Effizienter wäre ein einziger kombinierter Regex-Lauf mit einem `|`-verknüpften Muster, der den Text nur einmal durchläuft und alle Keywords gleichzeitig zählt.

### Wie skaliert die Lösung?

Der Algorithmus skaliert **linear** mit der Anzahl der PDFs und der Anzahl der Keywords. Verdoppelt man die Anzahl der PDFs, verdoppelt sich die Laufzeit – verdoppelt man gleichzeitig auch die Keywords, vervierfacht sie sich. Das ist für den studentischen Anwendungsfall (10–50 PDFs, 5–20 Keywords) problemlos handhabbar und läuft in Sekunden.

Bei größeren Datenmengen entstehen jedoch zwei Engpässe:

| Szenario | Problem |
|---|---|
| Sehr viele PDFs (z. B. 500+) | Text-Extraktion ist der Flaschenhals – `pypdf` liest sequenziell, keine Parallelverarbeitung |
| Sehr große PDFs (z. B. 500+ Seiten) | Der gesamte Text wird in den Arbeitsspeicher geladen – bei sehr großen Dokumenten kann das zu Speicherproblemen führen |
| Sehr viele Keywords (z. B. 100+) | Für jedes Keyword ein separater Regex-Lauf – Laufzeit steigt linear |

Für eine produktionsreife Version wären folgende Maßnahmen sinnvoll: parallele PDF-Verarbeitung mit `multiprocessing`, ein gecachter Text-Index nach der ersten Extraktion sowie ein kombinierter Regex-Ausdruck für alle Keywords.

---

## Ausgabe

Das Skript erzeugt drei Ausgaben:

1. **Konsole** – Formatierte Tabelle mit Rang, Dateiname, Keyword-Treffern und Score
2. **`result.csv`** – Ergebnistabelle als CSV-Datei (UTF-8)
3. **`result.xlsx`** – Ergebnistabelle als Excel-Datei (Sheet: `Results`)

**Beispiel-Konsolenausgabe (aus echten Quellen in `sources/`):**

```
╭───┬────────────────────┬────────────────┬───────────────┬──────────────────┬───────────────┬────────┬──────────────┬───────╮
│   │ Source             │ neural network │ deep learning │ machine learning │ training data │ Python │ schreibtisch │ Score │
├───┼────────────────────┼────────────────┼───────────────┼──────────────────┼───────────────┼────────┼──────────────┼───────┤
│ 1 │ 1912.09789v1.pdf   │             23 │            26 │              159 │            20 │      3 │            0 │   970 │
│ 2 │ 1908.00080v4.pdf   │             31 │            75 │               68 │             7 │      7 │            0 │   868 │
│ 3 │ 2108.00941v3.pdf   │             10 │            33 │               43 │             4 │      0 │            0 │   409 │
│ 4 │ 2308.11254v1.pdf   │              0 │            10 │               60 │             2 │      1 │            0 │   298 │
│ 5 │ 2402.06196v3.pdf   │              5 │             9 │               16 │             8 │      8 │            0 │   179 │
╰───┴────────────────────┴───────────────┴──────────────────┴───────────────┴────────┴──────────────┴───────╯
```

---

*Entwickelt für den FOM Hackathon – Algorithmen & Datenstrukturen 2026*
