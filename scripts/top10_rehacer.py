"""Rehace con el formato nuevo (noticiero, voz noticiero, saludos, GEO) ediciones del Top 10 YA subidas
(orden del Fundador, 27-nov-2026). No toca las carpetas viejas ni su publicado.json: crea carpetas nuevas
<fecha>-<lang>-top10-<id>-v2 con el mismo libreto, datos y hora de estreno, y anota el reemplazo.
Uso: python top10_rehacer.py <semana_json>   (en Actions, con token de top10-redes) → escribe top10_matriz.json
"""
import json
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import top10_semana as T  # noqa: E402
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GENERADOS = ("secuencia", "ficha_anim", "tabla")
CORTE = {"es": "Corte: miércoles 00:00, hora de Lima", "en": "Cut: Wednesday 00:00, Lima time"}


def main():
    sp = ROOT / sys.argv[1]
    S = json.loads(sp.read_text())
    try:
        yt = service(T.CANAL)
    except (Exception, SystemExit) as ex:
        print("sin token (no habrá saludos):", ex)
        yt = None
    eds = {e["id"]: e for e in T.CFG["ediciones"]}
    nuevos, orden = [], []
    america_nuevo = None
    for rel in S["orden"]:
        vieja = ROOT / rel
        g = json.loads((vieja / "guion.json").read_text())
        nueva = vieja.parent / (vieja.name + "-v2")
        orden.append(str(nueva.relative_to(ROOT)))
        if (nueva / "guion.json").exists():
            print("= ya existe", nueva.name)
            if g.get("edicion") == "america":
                america_nuevo = str(nueva.relative_to(ROOT))
            continue
        ed = eds[g["edicion"]]
        lang = g["lang"]
        pub = json.loads((vieja / "publicado.json").read_text())
        objetivo = pub["estado"].get("publishAt") or g["seo"].get("publicar_en")
        for e in g["escenas"]:
            for k in GENERADOS:
                e.pop(k, None)
        # saludos: 3 primeros comentarios de la edición ANTERIOR a la vieja (no de la que se reemplaza)
        sal = []
        if yt is not None:
            base = vieja.parent
            previas = sorted(d for d in base.glob(f"*-top10-{ed['id']}") if (d / "publicado.json").exists() and d.name < vieja.name)
            if previas:
                sal = _saludos(yt, previas[-1])
        if sal:
            frase = ((f"Antes de empezar, un saludo especial para {T._nombres(sal, lang)}: los primeros en comentar la edición "
                      "anterior. ¡Gracias! Comenta hoy y el próximo saludo puede ser para ti.") if lang == "es" else
                     (f"Before we start, a special shout-out to {T._nombres(sal, lang)}: the first to comment on last week's "
                      "edition. Thank you! Comment today and next week's shout-out could be yours."))
            g["escenas"][0]["texto"] = g["escenas"][0]["texto"].rstrip() + " " + frase
            g["seo"]["descripcion"] = (("👋 Saludos a " if lang == "es" else "👋 Shout-out to ") + T._nombres(sal, lang)
                                      + (", los primeros en comentar la edición anterior.\n\n" if lang == "es"
                                         else ", the first to comment on last week's edition.\n\n") + g["seo"]["descripcion"])
            for e in g["escenas"][:1]:  # las pistas en otros idiomas se regeneran desde el texto nuevo
                for k in [k for k in e if k.startswith("texto_")]:
                    e.pop(k)
        fin = datetime.fromisoformat("2026-11-25T05:00:00+00:00") if g.get("semana") == "2026-W48" else None
        if fin:
            geo = T.geo(lang, g.get("continente", ""), fin, g["edicion"] == "mundial")
            geo["resumen"] = geo["resumen"].replace("(corte: sábado 23:59, hora local)", "(corte: miércoles 00:00, hora de Lima)") \
                                           .replace("(cut: Saturday 23:59 local time)", "(cut: Wednesday 00:00 Lima time)")
            g["seo"].update(geo)
        if g["edicion"] == "mundial" and america_nuevo:
            g["publicar_despues_de"] = america_nuevo
            objetivo = (datetime.fromisoformat(objetivo.replace("Z", "+00:00")) + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        idx = S["orden"].index(rel)
        sig = None
        if idx + 1 < len(S["orden"]):
            gs = json.loads((ROOT / S["orden"][idx + 1] / "guion.json").read_text())
            sig = eds[gs["edicion"]]["nombre"].get(lang)
        g.update({"estilo": "noticiero", "saludos": sal, "siguiente_parada": sig or "", "corte_txt": CORTE.get(lang, CORTE["en"]),
                  "publicar_al_terminar": True, "publicar_objetivo": objetivo, "reemplaza": rel, "libreto": "claude",
                  "reintento_desde": (datetime.now(timezone.utc) + timedelta(hours=20)).strftime("%Y-%m-%dT%H:%M:%SZ")})
        g["seo"]["publicar_en"] = objetivo
        g.pop("audios_extra", None)
        nueva.mkdir(parents=True, exist_ok=True)
        shutil.copy(vieja / "categorias3.json", nueva / "categorias3.json")
        (nueva / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
        nuevos.append(str(nueva.relative_to(ROOT)))
        if g["edicion"] == "america":
            america_nuevo = str(nueva.relative_to(ROOT))
        print(f"+ {nueva.name} · estreno {objetivo} · saludos {sal}")
    (ROOT / "top10_matriz.json").write_text(json.dumps(nuevos))
    S["orden_v2"] = orden
    sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))


def _saludos(yt, previa):
    vid = json.loads((previa / "publicado.json").read_text())["video_id"]
    propio = json.loads((ROOT / "canales.json").read_text())[T.CANAL].get("youtube_id")
    from top10_noticiero import latino
    coms, tok = [], None
    try:
        for _ in range(10):
            r = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=100, order="time",
                                         textFormat="plainText", pageToken=tok).execute()
            for it in r.get("items", []):
                c = it["snippet"]["topLevelComment"]["snippet"]
                cid = (c.get("authorChannelId") or {}).get("value")
                if cid and cid != propio:
                    coms.append((c["publishedAt"], cid, c.get("authorDisplayName", "")))
            tok = r.get("nextPageToken")
            if not tok:
                break
    except Exception as ex:
        print("  saludos:", str(ex)[:100])
        return []
    out, vistos = [], set()
    for _, cid, nom in sorted(coms):
        n = latino(nom.lstrip("@").replace("-", " ").replace("_", " "))
        if cid in vistos or not n:
            continue
        vistos.add(cid)
        out.append(n)
        if len(out) == 3:
            break
    return out


if __name__ == "__main__":
    main()
