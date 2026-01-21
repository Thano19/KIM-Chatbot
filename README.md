# Projekt: Lokaler Chatbot zur Imitation einer Person 

## Zum Projekt:
Dieses Projekt ist entstanden für den Kurs KI in Medienanwendungen an der Hochschule in Furtwangen.

Es wurde ein lokaler Chatbot auf Basis von **Ollama** und **Llama 3** entwickelt, der sein Wissen aus vorgegebenen Textdateien per **RAG (Retrieval-Augmented Generation)** nutzt und im **Schreibstil** einer Person antwortet. Dabei soll er keine Fakten erfinden.

## Leitfrage:
Wie einfach kann man eine Person von einem Chatbot imitieren lassen?

## Ziel:
Das Ziel des Projekts ist es , einen lokalen Chatbot zu entwickeln, der den Schreibstil einer Person nachahmt und gleichzeitig sich auf vorgegebenes Wissen zugreift, ohne Fakten zu erfinden. Im Fokus steht wie überzeugebend die Nachbildung im Dialog wirkt und sie trotzdem erkannt wird.

## Verwendete Technologien
- **Ollama**: Lokales Hosting/Inference von LLMs
- **Llama 3**: Chat-Modell für Antworten (Generation)
- **mxbai-embed-large** (oder anderes Embedding-Modell): für semantische Vektoren (Embeddings)
- **ChromaDB**: lokale Vektor-Datenbank für Retrieval (Similarity Search)
- **Python**: Implementierung der Pipeline
- **pypdf**: Extraktion von Text aus PDFs

---

## Funktionsübersicht
### 1) RAG (Wissensabruf aus Dateien)
Der Bot liest Dateien aus `data/wissen/` ein, zerlegt sie in Textstücke (Chunks), erstellt Embeddings und speichert diese in ChromaDB.

Bei einer Nutzerfrage passiert:
1. **Embedding der Frage**
2. **Similarity Search** in ChromaDB (Top-K passende Textstücke)
3. Übergabe des gefundenen Kontextes an Llama 3
4. Antwort wird generiert – **nur** mit den bereitgestellten Quellen als Faktenbasis

### 2) Style/Imitation
Der Bot verwendet zusätzlich einen definierten Schreibstil basierend auf Beispielen aus `data/style/`.
Dazu wird mit einem Builder-Script ein `style_profile.txt` erzeugt, das Stilregeln enthält (Ton, Satzlänge, typische Formulierungen, Emoji-Usage etc.).
Dieses Profil wird beim Chat als System-Regel eingesetzt.

---

## Projektstruktur
```txt
KIM-Chatbot/
├─ main.py
├─ imitation_builder.py            # erzeugt style_profile.txt aus data/style
├─ style_profile.txt               # generiert, optional
├─ data/
│  ├─ wissen/                      # PDFs/TXTs als Wissensbasis (nicht versionieren)
│  └─ style/                       # Stilbeispiele (nicht versionieren)
└─ indexes/
   └─ chroma/                      # ChromaDB Datenbank (nicht versionieren)
```

## Testen des Projekts
Zum Testen der Funktionalität und Beantwortung der Leitfrage wurde ein Experiment durchgeführt. Der Chatbot sollte meinen Schreibstil imitieren und in einem Chatkontext mit meinem Kommilitonen sowie dem Dozenten eingesetzt werden.

**Datenbasis** 
- 2 Textdateien mit insgesamt 10 Wissensfakten
- 5 Textdateien mit 3 Mailvorlagen in meinem Schreibstil
- 1 Textdatei mit >60 Privatnachrichten

**Beobachtungskriterien**
- Wurde der Chatbot erkannt bzw. wurde ein Verdacht geäußert?
- Falls ja: aufgrund  von Stil oder aufgrund von inhaltlichen Unstimmigkeiten

### Resultat
Der Chatbot wurde relativ schnell als nicht-menschlich erkannt. Der Schreibstil hat zwar Ähnlichkeiten mit meiner Artikulation jedoch wird inhaltlich schnell klar, dass nicht mir kommuniziert wird.

---

## Herausforderungen
- Die erste Herausforderung bestand in der generellen Nutzung eines lokalen Chatbots. Aufgrund Hardware basierter Probleme konnte zu Beginn des Projekts nicht Llama 3 genutzt werden sondern es wurde tinyllama verwendet. Dieser hat aber relativ schnell seine Grenzen gezeigt in dem nicht ordentlich in der Lage war in der deutschen Sprache zu kommunizieren sowie das Ignorieren der Textdateien zum embedden.
- Bei der Entwicklung des Chatbots war das hauptsächliche Problem die Verarbeitung der Textdateien, da diese am Anfang nicht wirklich embeddet wurden und somit auch nicht aufgenommen wurden.

---

## Fazit
Das Projekt zeigt, dass es nicht so schnell und einfach geht eine Person auf kommunikativer Basis zu imitieren. Gründe für das Fehlschlagen des Experiments sind sehr wahrscheinlich die verwendete Datenmenge sowie das ausgewählte Modell. Das Ergebnis des Experiments würde sehr wahrscheinlich sich nicht so schnell ergeben haben, wenn deutlich größere Datenmengen sowie ein größeres Modell verwendet worden wäre.