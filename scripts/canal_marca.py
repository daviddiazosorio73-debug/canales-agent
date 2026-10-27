"""Aplica canales/<canal>/marca.json al canal de YouTube (descripción, palabras clave, idioma, país, tráiler,
traducciones, no dirigido a niños) y guarda lo que quedó en canales/<canal>/marca_actual.json.
Uso: python canal_marca.py <canal>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    canal = sys.argv[1]
    M = json.loads((ROOT / "canales" / canal / "marca.json").read_text())
    yt = service(canal)
    ch = yt.channels().list(part="id,brandingSettings,localizations,status", mine=True).execute()["items"][0]
    b = ch["brandingSettings"]
    c = b.setdefault("channel", {})
    for k in ("description", "keywords", "defaultLanguage", "country", "unsubscribedTrailer"):
        if M.get(k):
            c[k] = M[k]
    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": {"channel": c}}).execute()
    if M.get("localizations"):
        yt.channels().update(part="localizations", body={"id": ch["id"], "localizations": M["localizations"]}).execute()
    try:
        yt.channels().update(part="status", body={"id": ch["id"], "status": {"selfDeclaredMadeForKids": False}}).execute()
    except Exception as e:
        print("marca: aviso (estado niños):", str(e)[:150])
    fin = yt.channels().list(part="brandingSettings,localizations,statistics", mine=True).execute()["items"][0]
    (ROOT / "canales" / canal / "marca_actual.json").write_text(json.dumps(fin, ensure_ascii=False, indent=1))
    print("marca aplicada:", canal, fin["statistics"])


if __name__ == "__main__":
    main()
