# Source Relevance Scoring Algorithm

> **FOM Hackathon – Algorithms & Data Structures 2026**

Dieses Tool bewertet automatisch die Relevanz von PDF-Quellen anhand einer gewichteten Keyword-Analyse. Jede PDF-Datei erhält einen numerischen Score – je häufiger und wichtiger die gesuchten Begriffe im Dokument vorkommen, desto höher der Score. Die Quellen werden anschließend nach Relevanz absteigend sortiert und als Tabelle ausgegeben.

---

## Inhaltsverzeichnis

- [Voraussetzungen](#voraussetzungen)
- [Projektstruktur](#projektstruktur)
- [Schnellstart](#schnellstart)
- [Algorithmus – Detaillierte Erklärung](#algorithmus--detaillierte-erklärung)
  - [Schritt 1: Keywords laden](#schritt-1-keywords-laden)
  - [Schritt 1b: Gewichte berechnen](#schritt-1b-gewichte-berechnen)
  - [Schritt 2: PDF-Ordner laden](#schritt-2-pdf-ordner-laden)
  - [Schritt 3: Text extrahieren](#schritt-3-text-extrahieren)
  - [Schritt 3b: Keyword-Treffer zählen](#schritt-3b-keyword-treffer-zählen)
  - [Schritt 4: Score berechnen](#schritt-4-score-berechnen)
  - [Schritt 5: Tabelle bauen & sortieren](#schritt-5-tabelle-bauen--sortieren)
- [Score-Formel](#score-formel)
- [Beispiel](#beispiel)
- [Annahmen & Einschränkungen](#annahmen--einschränkungen)
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
├── quellenbewertung.py       # Hauptskript (der Algorithmus)
│
├── stichpunkte.txt           # Keyword-Datei (eine Zeile = ein Keyword)
├── simple_stichpunkte.txt    # Vereinfachte Keyword-Beispieldatei
│
├── sources/                  # Ordner mit den zu analysierenden PDFs
├── simple_sources/           # Ordner mit einfachen Beispiel-PDFs
│
├── result.csv                # Ausgabe: Ergebnistabelle als CSV
├── result.xlsx               # Ausgabe: Ergebnistabelle als Excel
└── erwartet.csv              # Erwartete Ergebnisse (für Tests)
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

---

## Algorithmus – Detaillierte Erklärung

Der Algorithmus besteht aus **5 Hauptschritten**. Nachfolgend wird jeder Schritt genau erklärt.

---

### Schritt 1: Keywords laden

**Funktion:** `load_keywords(file_path: Path) → list[str]`

Die Keyword-Datei (z. B. `stichpunkte.txt`) wird Zeile für Zeile eingelesen. Leere Zeilen werden ignoriert. Die Reihenfolge der Keywords in der Datei ist **entscheidend**, da sie direkt die Gewichtung bestimmt (siehe Schritt 1b).

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

Nach dem Laden der Keywords wird für jedes Keyword ein **Gewicht** (englisch: *weight*) berechnet. Das Prinzip ist einfach:

- Das **erste** Keyword (wichtigstes) bekommt das **höchste** Gewicht `n`
- Das **letzte** Keyword (unwichtigstes) bekommt das **niedrigste** Gewicht `1`

**Formel:**

```
Gewicht(keyword_i) = n - i
```

Dabei ist `n` die Gesamtanzahl der Keywords und `i` der 0-basierte Index des Keywords.

**Beispiel** (6 Keywords → n = 6):

| Index | Keyword          | Gewicht |
|-------|------------------|---------|
| 0     | neural network   | 6       |
| 1     | deep learning    | 5       |
| 2     | machine learning | 4       |
| 3     | training data    | 3       |
| 4     | Python           | 2       |
| 5     | schreibtisch     | 1       |

Das Gewicht spiegelt direkt die **thematische Priorität** wider, die der Nutzer durch die Reihenfolge in der Keyword-Datei festlegt.

---

### Schritt 2: PDF-Ordner laden

**Funktion:** `load_pdfs(folder_path: Path) → list[Path]`

Das Skript liest alle Dateien mit der Endung `.pdf` aus dem konfigurierten Ordner (Standard: `sources/`). Die Liste wird alphabetisch sortiert (`sorted()`), damit die Verarbeitungsreihenfolge deterministisch ist. Wird der Ordner nicht gefunden oder enthält keine PDFs, bricht das Programm ab.

---

### Schritt 3: Text extrahieren

**Funktion:** `extract_text(pdf_path: Path) → str`

Für jede PDF-Datei wird der enthaltene Text mit `pypdf.PdfReader` Seite für Seite extrahiert. Die Texte aller Seiten werden mit Zeilenumbrüchen verbunden.

**Wichtig: Zwei Textkorrekturen werden angewendet:**

#### Korrektur 1 – Silbentrennungs-Fix
PDFs enthalten häufig automatische Silbentrennung am Zeilenende, z. B.:

```
...the neu-
ral network was trained...
```

Der reguläre Ausdruck `re.sub(r'-\n', '', raw_text)` entfernt den Bindestrich samt Zeilenumbruch und fügt das Wort wieder zusammen:

```
...the neural network was trained...
```

#### Korrektur 2 – Einfacher Zeilenumbruch → Leerzeichen
Normale Zeilenumbrüche (kein Doppel-Newline, also kein Absatzende) werden durch Leerzeichen ersetzt:

```
re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)
```

Dadurch wird verhindert, dass Wörter, die über eine Zeilengrenze hinausgehen, als zwei separate Tokens gezählt werden.

**Fehlerfall:** Falls die PDF nicht lesbar ist (z. B. beschädigte Datei), gibt die Funktion einen leeren String zurück. Der Score dieser Datei wird dann automatisch `0`.

> **Einschränkung [L3]:** Bild-basierte PDFs (gescannte Dokumente ohne Text-Layer) liefern ebenfalls einen leeren String und erhalten einen Score von 0.

---

### Schritt 3b: Keyword-Treffer zählen

**Funktion:** `count_occurrences(keyword: str, text: str) → int`

Diese Funktion zählt, wie oft ein Keyword im extrahierten Text vorkommt. Die Suche ist:

- **Case-insensitive** (Groß-/Kleinschreibung wird ignoriert) → `text.lower()`
- **Word-boundary-aware** (es werden nur vollständige Wörter/Phrasen gefunden, keine Teilstrings)

Der reguläre Ausdruck lautet:

```python
pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
```

Die `\b`-Anker (Word Boundaries) stellen sicher, dass z. B. das Keyword `"learn"` **nicht** innerhalb von `"learning"` gefunden wird. `re.escape()` sorgt dafür, dass Sonderzeichen im Keyword (z. B. Punkte, Klammern) korrekt behandelt werden.

**Funktioniert für:**
- Einzelwörter: `"Python"` → findet `"python"`, `"Python"`, `"PYTHON"`
- Mehrwort-Phrasen: `"neural network"` → findet `"neural network"` als zusammenhängende Phrase

**Ergebnis:** Für jede PDF und jedes Keyword wird die Trefferanzahl in der Datenstruktur `hits[filename][keyword]` gespeichert.

---

### Schritt 4: Score berechnen

Nachdem alle Treffer gezählt wurden, wird für jede PDF-Datei ein **Gesamtscore** berechnet. Der Score ist die Summe aller gewichteten Keyword-Treffer.

**Formel:**

```
Score(Quelle) = Σ (Trefferanzahl(keyword_i) × Gewicht(keyword_i))
```

In Python:

```python
score = sum(
    keyword_hits[keyword] * weights[keyword]
    for keyword in keywords
)
```

**Interpretation:** Eine PDF, die das wichtigste Keyword (höchstes Gewicht) häufig enthält, erhält einen deutlich höheren Score als eine PDF, die nur unwichtige Keywords enthält. Keyword-Häufigkeit und Keyword-Priorität werden so kombiniert.

---

### Schritt 5: Tabelle bauen & sortieren

Die Ergebnisse werden in einem `pandas.DataFrame` zusammengeführt. Jede Zeile entspricht einer PDF-Datei, jede Spalte einem Keyword plus einer abschließenden Score-Spalte.

Die Tabelle wird **absteigend nach Score** sortiert:

```python
table = table.sort_values(by="Score", ascending=False)
table = table.reset_index(drop=True)
table.index += 1  # Rang beginnt bei 1
```

Der Index entspricht damit dem **Relevanz-Rang**: Rang 1 = relevanteste Quelle.

---

## Score-Formel

Die vollständige mathematische Formel für den Score einer Quelle `Q` mit `n` Keywords:

```
Score(Q) = Σ_{i=0}^{n-1}  count(keyword_i, Q) × (n - i)
```

| Symbol              | Bedeutung                                                      |
|---------------------|----------------------------------------------------------------|
| `n`                 | Gesamtanzahl der Keywords                                      |
| `i`                 | 0-basierter Index des Keywords in der Keyword-Datei            |
| `count(keyword, Q)` | Anzahl der exakten Vorkommen des Keywords in der PDF-Quelle `Q`|
| `(n - i)`           | Gewicht des Keywords (höchstes für das erste Keyword)          |

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

## Annahmen & Einschränkungen

| ID  | Typ           | Beschreibung                                                             |
|-----|---------------|--------------------------------------------------------------------------|
| A1  | Annahme       | Quellen sind auf Englisch verfasst                                       |
| A2  | Annahme       | PDFs sind text-basiert (nicht gescannt / bild-basiert)                   |
| L1  | Einschränkung | Keine Unterscheidung zwischen Groß-/Kleinschreibung (case-insensitive)   |
| L2  | Einschränkung | Kein Stemming/Lemmatisierung – `"learning"` ≠ `"learn"`                 |
| L3  | Einschränkung | Bild-basierte PDFs liefern leeren Text → Score = 0                       |
| L4  | Einschränkung | Keyword-Reihenfolge bestimmt vollständig die Gewichtung                  |
| L5  | Einschränkung | Häufigkeit ≠ Relevanz – der Kontext der Erwähnung wird nicht bewertet    |

---

## Ausgabe

Das Skript erzeugt drei Ausgaben:

1. **Konsole** – Formatierte Tabelle mit Rang, Dateiname, Keyword-Treffern und Score
2. **`result.csv`** – Ergebnistabelle als CSV-Datei (UTF-8)
3. **`result.xlsx`** – Ergebnistabelle als Excel-Datei (Sheet: `Results`)

**Beispiel-Konsolenausgabe:**

```
╭──────┬────────────────────┬────────────────┬───────────────┬───────┬────────┬──────────────┬───────╮
│      │ Source             │ neural network │ deep learning │  ...  │ Python │ schreibtisch │ Score │
├──────┼────────────────────┼────────────────┼───────────────┼───────┼────────┼──────────────┼───────┤
│    1 │ paper_A.pdf        │             12 │             8 │  ...  │      1 │            0 │   143 │
│    2 │ paper_B.pdf        │              3 │             2 │  ...  │      0 │            0 │    28 │
╰──────┴────────────────────┴────────────────┴───────────────┴───────┴────────┴──────────────┴───────╯
```

---

*Entwickelt für den FOM Hackathon – Algorithms & Data Structures 2026*
