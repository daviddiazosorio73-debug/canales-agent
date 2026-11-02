"""Comentario con pregunta en cada video largo, apenas se hace público (sin Claude).

Toma la línea «💬 …» de la descripción (o `comentario_fijado` del guion) y la publica como comentario del canal.
Fijarlo es manual: la API de YouTube no permite fijar comentarios (Studio → Comentarios → ⋮ → Fijar).
Guarda <proyecto>/comentario.json para no repetir. Cuota: 50 unidades por comentario; máximo MAX por corrida.
Uso: python scripts/comentario_pregunta.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MAX = 3


def pregunta(g):
    if g.get("comentario_fijado"):
        return g["comentario_fijado"]
    for linea in g.get("seo", {}).get("descripcion", "").splitlines():
        if linea.startswith("💬"):
            return linea
    return None


def main():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    hechos = 0
    for canal, cfg in canales.items():
        if canal.startswith("_") or canal == "top10-redes" or not cfg.get("activo"):
            continue  # el Top 10 tiene su propia comunidad (comunidad.py)
        yt = None
        for proj in sorted((ROOT / "canales" / canal / "proyectos").glob("*/publicado.json")):
            proj = proj.parent
            if hechos >= MAX or (proj / "comentario.json").exists():
                continue
            g = json.loads((proj / "guion.json").read_text())
            pub = g.get("seo", {}).get("publicar_en")
            if g.get("tipo") == "short" or not pub:
                continue
            t = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if t > ahora or (ahora - t).days > 3:
                continue  # aún privado, o demasiado antiguo para empezar ahora
            texto = pregunta(g)
            if not texto:
                continue
            if yt is None:
                if not token_file(canal, cfg):
                    break
                yt = service(canal)
            vid = json.loads((proj / "publicado.json").read_text())["video_id"]
            try:
                r = yt.commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid,
                        "topLevelComment": {"snippet": {"textOriginal": texto}}}}).execute()
            except Exception as e:
                print(f"AVISO {canal}/{proj.name}: {str(e)[:150]}")
                continue
            (proj / "comentario.json").write_text(json.dumps({
                "comentario_id": r["id"], "texto": texto, "fecha": ahora.strftime("%Y-%m-%dT%H:%MZ"),
                "fijar": f"https://studio.youtube.com/video/{vid}/comments"}, ensure_ascii=False, indent=2))
            hechos += 1
            print(f"OK {canal}/{proj.name}: comentario publicado (fíjalo en Studio)")
    print(f"{hechos} comentarios nuevos")


if __name__ == "__main__":
    main()
