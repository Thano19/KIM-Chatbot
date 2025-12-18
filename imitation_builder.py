from pathlib import Path
from pypdf import PdfReader
import ollama

STYLE = Path("data/style")
OUT = Path("style_profile.txt")
MODEL_NAME = "llama3"

def auslesen_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def auslesen_txt(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return auslesen_pdf(path)
    return path.read_text(encoding="utf-8", errors="ignore")

def main():
    texte = []
    for datei in STYLE.rglob("*"):
        if datei.is_file() and datei.suffix.lower() in [".txt", ".pdf"]:
            text = auslesen_txt(datei).strip()
            if text:
                texte.append(text)

    if not texte:
        raise SystemExit("Keine Stil-Beispieldateien gefunden in 'data/style'.")

    sample = "\n\n---\n\n".join("\n".join(text.splitlines()[:100]) for text in texte[:6])

    prompt = f"""
Erstelle ein STYLE-PROFIL aus den Beispielen.

Gib zurück:
1) Tonalität + Satzlänge + Struktur + typische Phrasen + Emoji-Usage
2) Dos & Don'ts (max 10)
3) 3 Beispielantworten im Stil: Begrüßung, kurze Erklärung, höfliche Absage

Regeln:
- Nur Stil ableiten, keine privaten Fakten übernehmen.
Beispiele:
{sample}
"""
    response = ollama.chat(model=MODEL_NAME, messages=[{"role": "user", "content": prompt}])
    OUT.write_text(response["message"]["content"], encoding="utf-8")
    print(f"✅ Stil-Profil erstellt in '{OUT}'")

if __name__ == "__main__":
    main()