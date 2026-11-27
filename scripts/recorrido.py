"""Recorrido completo de MayorDom (propuesta del Fundador, 27-nov-2026).

Lista «MayorDom · Recorrido completo» = todos los videos largos (sermones y análisis) en orden ascendente desde
«¿Miembro o discípulo? … Noche 1», y como ÚLTIMO elemento un video largo del canal hermano (Escuela Sabática ES):
al terminar nuestro material, la reproducción automática lleva a otro canal nuestro, no a uno ajeno.
Cada video (largos y Shorts) lleva en su descripción el enlace «empieza desde la Noche 1» con la lista.

Idempotente; corre a diario después del reinicio de cuota. Presupuesto por corrida (unidades de la API):
inserciones de lista 50 c/u y edición de descripciones 50 c/u, máx. RECORRIDO_MAX_EDITAR por día.
Estado en canales/mayordom/recorrido.json. Uso: python scripts/recorrido.py
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANAL = "mayordom"
HERMANO = "escuela-sabatica-es"
EST = ROOT / "canales" / CANAL / "recorrido.json"
TITULO = "MayorDom · Recorrido completo (desde la Noche 1)"
DESC = ("Todo MayorDom en orden, desde la Semana de Mayordomía 2026 · Noche 1 «¿Miembro o discípulo?» hasta el "
        "último sermón y análisis. Al final te espera la Escuela Sabática para maestros y alumnos. #MayordomíaBíblica")
MAX_EDITAR = int(os.environ.get("RECORRIDO_MAX_EDITAR", "40"))
MARCA = "▶ Recorre todo MayorDom desde la Noche 1:"


def largos():
    out = []
    for g in sorted((ROOT / "canales" / CANAL / "proyectos").glob("*/guion.json")):
        d = json.loads(g.read_text())
        pub = g.parent / "publicado.json"
        if d.get("tipo") in ("sermon", "analisis") and pub.exists():
            out.append((g.parent.name[:10], json.loads(pub.read_text())["video_id"]))
    return [v for _, v in sorted(out)]


def todos_los_videos():
    out = []
    for pub in sorted((ROOT / "canales" / CANAL / "proyectos").glob("*/publicado.json")):
        out.append(json.loads(pub.read_text())["video_id"])
    return out


def final_hermano(yt):
    """Último video largo (más de 3 min) del canal hermano."""
    cid = json.loads((ROOT / "canales.json").read_text())[HERMANO]["youtube_id"]
    up = yt.channels().list(part="contentDetails", id=cid).execute()["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50).execute().get("items", [])]
    if not ids:
        return None
    for v in yt.videos().list(part="contentDetails,status", id=",".join(ids)).execute().get("items", []):
        m = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:\d+S)?", v["contentDetails"]["duration"])
        if m and (int(m.group(1) or 0) * 60 + int(m.group(2) or 0)) >= 3 and v["status"].get("privacyStatus") == "public":
            return v["id"]
    return None


def main():
    yt = service(CANAL)
    est = json.loads(EST.read_text()) if EST.exists() else {}
    gasto = 0
    if not est.get("lista"):
        r = yt.playlists().insert(part="snippet,status", body={"snippet": {"title": TITULO, "description": DESC, "defaultLanguage": "es"},
                                                              "status": {"privacyStatus": "public"}}).execute()
        est["lista"] = r["id"]
        gasto += 50
        print("+ lista", r["id"])
    lista = est["lista"]
    orden = largos()
    est["inicio"] = orden[0] if orden else None
    # estado actual de la lista
    items, tok = [], None
    while True:
        r = yt.playlistItems().list(part="snippet", playlistId=lista, maxResults=50, pageToken=tok).execute()
        items += [(it["id"], it["snippet"]["resourceId"]["videoId"], it["snippet"]["position"]) for it in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    en_lista = [v for _, v, _ in sorted(items, key=lambda x: x[2])]
    fin = est.get("final") or final_hermano(yt)
    est["final"] = fin
    # insertar los que faltan en su posición (orden ascendente), siempre antes del video del canal hermano
    for i, v in enumerate(orden):
        if v in en_lista or gasto > 9000:
            continue
        pos = sum(1 for x in orden[:i] if x in en_lista)
        yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": lista, "position": pos,
                                                                     "resourceId": {"kind": "youtube#video", "videoId": v}}}).execute()
        en_lista.insert(pos, v)
        gasto += 50
        print(f"+ {v} en la posición {pos}")
    if fin and fin not in en_lista:
        yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": lista, "resourceId": {"kind": "youtube#video", "videoId": fin}}}).execute()
        gasto += 50
        print("+ final del canal hermano", fin)
    # enlace «desde la Noche 1» en las descripciones de los videos ya subidos (por tandas)
    enlace = f"https://www.youtube.com/watch?v={est['inicio']}&list={lista}"
    hechos = set(est.get("descripciones", []))
    editados = 0
    for v in todos_los_videos():
        if v in hechos or editados >= MAX_EDITAR or gasto > 9000:
            continue
        it = yt.videos().list(part="snippet", id=v).execute().get("items", [])
        if not it:
            hechos.add(v)
            continue
        sn = it[0]["snippet"]
        if MARCA not in sn.get("description", ""):
            desc = f"{MARCA} {enlace}\n\n" + sn.get("description", "")
            body = {"id": v, "snippet": {"title": sn["title"], "description": desc[:4900], "categoryId": sn["categoryId"],
                                         "tags": sn.get("tags", []), "defaultLanguage": sn.get("defaultLanguage", "es")}}
            yt.videos().update(part="snippet", body=body).execute()
            editados += 1
            gasto += 51
        hechos.add(v)
    est["descripciones"] = sorted(hechos)
    est["enlace"] = enlace
    EST.write_text(json.dumps(est, ensure_ascii=False, indent=1))
    print(f"OK recorrido: {len(orden)} largos, final {fin}, {editados} descripciones editadas hoy, ~{gasto} unidades")


if __name__ == "__main__":
    main()
