import ollama
import chromadb
from pathlib import Path
from pypdf import PdfReader
import hashlib

# ausgewählte Modelle
MODEL_NAME = "llama3"
EMBED_MODEL = "mxbai-embed-large"

# RAG Einstellungen
MAX_LOGS = 20
TOP_K = 5
TEXTSTÜCKE_CHARS = 900
ÜBERSCHNEIDUNGEN = 150

# Pfade
WISSEN = Path("data/wissen")
CHROMA_PATH = Path("indexes/chroma")
COLLECTION_NAME = "wissen_docs"
STYLE_PROFILE_PATH = Path("style_profile.txt")
STYLE_PROFILE = STYLE_PROFILE_PATH.read_text(encoding="utf-8").strip()


# Kürzt den Chatverlauf, damit dieser nicht zu lang wird
def chatverlauf_kürzen(chathistorie):
        system = chathistorie[:1]
        rest = chathistorie[1:]
        keep = rest[-MAX_LOGS*2:]

        return system + keep

# Auslesen von Dateien
def auslesen_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    texte = []
    for page in reader.pages:
        texte.append(page.extract_text() or "")
    
    return "\n".join(texte)

def auslesen_txt(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return auslesen_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")

# Zerlegung von Texten in Stücke
def zerlegen_text(text: str):
    text = " ".join(text.split())
    textstücke = []
    i = 0
    while i < len(text):
        chunk = text[i:i+TEXTSTÜCKE_CHARS]
        if len(chunk.strip()) > 50:
            textstücke.append(chunk)
        i += TEXTSTÜCKE_CHARS - ÜBERSCHNEIDUNGEN
    return textstücke

# Erzeugt eine ID pro Textstück
def textstück_id(source: str, idx: int, chunk: str) -> str:
    h = hashlib.sha1(f"{source}#{idx}::{chunk}".encode("utf-8", errors="ignore")).hexdigest()
    return h

# ChromaDB Collection holen oder erstellen
def get_collection():
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    col = client.get_or_create_collection(name=COLLECTION_NAME)
    return client, col

# Index aufbauen oder aktualisieren
def build_or_update_index(collection):
    WISSEN.mkdir(parents=True, exist_ok=True)

    dateien = [p for p in WISSEN.rglob("*") if p.is_file() and p.suffix.lower() in {".pdf", ".txt"}]
    if not dateien:
        print("⚠️ Keine Dateien gefunden in data/wissen/.")
        return

    # Daten sammeln und einfügen (Stück für Stück)
    ids, embeddings, documents, metadatas = [], [], [], []

    for text in dateien:
        roh_text = auslesen_txt(text).strip()
        if not roh_text:
            continue

        textstücke = zerlegen_text(roh_text)
        for idx, ch in enumerate(textstücke):
            emb = ollama.embed(model=EMBED_MODEL, input=ch)["embeddings"][0]
            cid = textstück_id(str(text), idx, ch)

            ids.append(cid)
            embeddings.append(emb)
            documents.append(ch)
            metadatas.append({"source": str(text), "chunk_index": idx})

            # Batch-Flush
            if len(ids) >= 64:
                collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
                ids, embeddings, documents, metadatas = [], [], [], []

    if ids:
        collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    print("✅ Index up-to-date.\n")

# Kontext zu einer Anfrage abrufen
def abruf_context(collection, query: str):
    frage_emb = ollama.embed(model=EMBED_MODEL, input=query)["embeddings"][0]

    # sucht die besten Textstücke im Index, basierend auf der Anfrage
    res = collection.query(
        query_embeddings=[frage_emb],
        n_results=TOP_K,
        include=["documents", "metadatas"]
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    blocks = []
    sources = []

    # Zusammensetzen der Textstücke und Quellenangaben
    for d, m in zip(docs, metas):
        src = m.get("source", "unknown")
        ci = m.get("chunk_index", "?")
        tag = f"{src}#chunk{ci}"
        sources.append(tag)
        blocks.append(f"[{tag}]\n{d}")

    context = "\n\n---\n\n".join(blocks)
    return context, sources

def main():
    client, collection = get_collection()

    if collection.count() == 0:
        build_or_update_index(collection)
    
    chatverlauf = [
        {
            "role": "system",
            "content": (
                "Du bist ein hilfreicher, sachlicher Assistent. "
                "Du antwortest kurz, präzise und erfindest nichts."
            ),
        }
    ]

    while True:
        user_input = input("Du: ").strip()

        if not user_input:
            continue

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Bot: Okay, bis dann 👋")
            break

        if user_input == "/reset":
            chatverlauf = chatverlauf[:1]
            print("🧹 Chatverlauf zurückgesetzt.")
            continue

        if user_input == "/update":
            client.delete_collection(name=COLLECTION_NAME)
            collection = client.get_or_create_collection(name=COLLECTION_NAME)
            build_or_update_index(collection)
            print("✅ Reindex done.\n")
            continue

        # Abruf von Kontext aus dem Wissens-Index    
        context, quellen = abruf_context(collection, user_input)

        print("\n🔍 Gefundene Quellen:")
        for q in quellen:
            print("-", q)
        print()

        chatverlauf.append({"role": "user", "content": user_input})
        chatverlauf = chatverlauf_kürzen(chatverlauf)

        context_msg = {
            "role": "system",
            "content": (
                "Nutze ausschließlich die folgenden Quellen als Faktenbasis. "
                "Wenn die Quellen die Frage nicht beantworten: sag 'Ich weiß es nicht'.\n\n"
                f"QUELLEN-KONTEXT:\n{context}"
            ),
        }

        style_msg = {
            "role": "system",
            "content": (
                "Schreibe im folgenden Stilprofil. "
                "- Emojis sind OPTIONAL (max 1), und nicht in jeder Antwort.\n"
                " Nie nur mit einem Emoji antworten.\n"
                "Übernimm keine Fakten aus dem Stilprofil.\n\n"
                f"STYLE-PROFIL:\n{STYLE_PROFILE}"
    ),
}

        base = chatverlauf[:-1]  # alles außer der letzten User-Nachricht
        last_user = chatverlauf[-1]  # die letzte User-Nachricht
        msg_for_model = base + [style_msg] + [context_msg] + [last_user]

        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=msg_for_model,
            )
        except Exception as e:
            print("⚠️ Fehler beim Aufruf von Ollama:", e)
            continue

        bot_msg = response["message"]["content"]
        chatverlauf.append(response["message"])

        print("Bot:", bot_msg)
        print()  # Leerzeile für bessere Lesbarkeit

if __name__ == "__main__":
    main()
