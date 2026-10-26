"""SEO del Top 10 a partir de los videos del conteo (API oficial, corre en Actions antes de metadata.py).

1. Lee títulos, etiquetas y descripciones de los videos listados (videos.list) y el @handle de cada creador
   (channels.list → snippet.customUrl).
2. Etiquetas: añade a seo.tags las etiquetas que más se repiten entre los videos del conteo (≥2 videos)
   y los nombres de los 3 primeros de cada categoría. metadata.py recorta a 500 caracteres.
3. Menciones: en la descripción, cada línea "N. Creador — https://youtu.be/ID" pasa a
   "N. Creador (@handle) — https://youtu.be/ID". YouTube notifica al canal mencionado en algunos casos.
4. Hashtags extra al final: los más usados por los videos del conteo (sin #shorts), máx. 5.
5. Si existe canales/<canal>/listas.json con la lista del tipo, añade el enlace a todas las ediciones.
Uso: python top10_seo.py <proyecto_dir> --canal <canal>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GENERICAS = {"shorts", "short", "youtube", "viral", "video", "videos", "funny", "humor", "tiktok", "fyp",
             "parati", "foryou", "trending", "reels", "youtubeshorts", "subscribe", "like"}


def lotes(xs, n=50):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def main():
    proj = Path(sys.argv[1])
    canal = sys.argv[sys.argv.index("--canal") + 1]
    g = json.loads((proj / "guion.json").read_text())
    seo = g["seo"]
    ids = list(dict.fromkeys(e["video_id"] for e in g["escenas"] if e.get("video_id")))
    if not ids:
        return
    yt = service(canal)
    vids = []
    for b in lotes(ids):
        vids += yt.videos().list(part="snippet", id=",".join(b)).execute().get("items", [])
    canales = list(dict.fromkeys(v["snippet"]["channelId"] for v in vids))
    handle = {}
    for b in lotes(canales):
        for c in yt.channels().list(part="snippet", id=",".join(b)).execute().get("items", []):
            cu = c["snippet"].get("customUrl") or ""
            if cu.startswith("@"):
                handle[c["id"]] = cu
    vid_handle = {v["id"]: handle.get(v["snippet"]["channelId"]) for v in vids}

    # Etiquetas frecuentes del conteo
    cuenta = Counter()
    hashtags = Counter()
    for v in vids:
        s = v["snippet"]
        cuenta.update({t.strip().lower() for t in s.get("tags", []) if 2 < len(t.strip()) <= 30})
        hashtags.update({h.lower() for h in re.findall(r"#(\w{3,30})", s.get("title", "") + " " + s.get("description", ""))})
    frecuentes = [t for t, n in cuenta.most_common(40) if n >= 2 and t.replace(" ", "") not in GENERICAS]
    cats = proj / "categorias3.json"
    nombres = []
    if cats.exists():
        D = json.loads(cats.read_text())
        for k in ("views", "comments", "likes"):
            nombres += [(r.get("creator_name") or "").lower() for r in D.get(k, [])[:3]]
    base = seo.get("tags", [])
    seo["tags"] = list(dict.fromkeys(base + [n for n in nombres if n] + frecuentes))

    # Menciones @handle en la descripción
    def mencion(m):
        h = vid_handle.get(m.group(3))
        return f"{m.group(1)} ({h}){m.group(2)}" if h and h not in m.group(1) else m.group(0)
    desc = re.sub(r"^(\d+\. [^\n—]+?)( — https://youtu\.be/([\w-]{11}))", mencion, seo["descripcion"], flags=re.M)

    extra = [h for h, _ in hashtags.most_common(15) if h not in GENERICAS][:5]
    base_h = seo.get("hashtags", [])
    seo["hashtags"] = list(dict.fromkeys(base_h + extra))[:8]  # los 3 nuestros van primero (son los visibles)
    listas = ROOT / "canales" / canal / "listas.json"
    if listas.exists():
        L = json.loads(listas.read_text())
        lid = L.get("ids", {}).get(seo.get("lista_nombre") or "")
        if lid and "playlist?list=" not in desc:
            desc += f"\n\n📺 Todas las ediciones: https://www.youtube.com/playlist?list={lid}"
    seo["descripcion"] = desc
    (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
    print(f"SEO: {len(handle)} menciones, {len(frecuentes)} etiquetas del conteo, hashtags extra: {extra}")


if __name__ == "__main__":
    main()
