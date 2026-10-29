"""Shorts automáticos del Top 10: 3 por edición (vistas, comentarios y likes), DESPUÉS del estreno.

Para cada edición tipo "top10" ya subida (con publicado.json) cuyo estreno no tenga más de 24 h de antigüedad,
crea 3 proyectos tipo "short" en canales/top10-redes/proyectos/ con el podio (#3, #2, #1) de una categoría,
leído de categorias3.json (cifras redondeadas hacia abajo, nada inventado) y el enlace a la edición completa.
Horario: estreno + 7 h (vistas), + 14 h 30 (comentarios) y + 25 h (likes).
Las escenas llevan "video_id": top10_short_visual.py arma las fichas verticales en el runner.
Uso: python scripts/top10_shorts.py [--todas]   (--todas ignora el límite de 24 h)
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROY = ROOT / "canales" / "top10-redes" / "proyectos"
OFFSETS = {"views": timedelta(hours=7), "comments": timedelta(hours=14, minutes=30), "likes": timedelta(hours=25)}
TXT = {
    "es": {"cat": {"views": ("más visto", "vistas", "VISTAS"), "comments": ("más comentado", "comentarios", "COMENTARIOS"),
                   "likes": ("con más likes", "likes", "LIKES")},
           "gancho": "¿Cuál fue el video {c} de {r} esta semana? Este es el podio. Mira hasta el final.",
           "puesto": {3: "En el tercer lugar, {t}, de {n}, con {x} {u}.", 2: "En el segundo lugar, {t}, de {n}, con {x} {u}.",
                      1: "Y el número uno: {t}, de {n}, con {x} {u}."},
           "cierre": "El conteo completo, del diez al uno, ya está en el canal. Búscalo en la descripción. Hashtag Top 10 RS.",
           "titulo": "El #1 {c} de {r} esta semana 🏆 #shorts",
           "desc": "El podio de los videos {c} de {r} esta semana.\n\nConteo completo, del 10 al 1: {url}\n\nDatos de la API oficial de YouTube. Narración con voz sintética. #Top10RS #shorts",
           "tags": ["top 10", "videos virales", "tendencias youtube", "shorts", "top 10 redes sociales"]},
    "en": {"cat": {"views": ("most viewed", "views", "VIEWS"), "comments": ("most commented", "comments", "COMMENTS"),
                   "likes": ("most liked", "likes", "LIKES")},
           "gancho": "Which was the {c} video in {r} this week? Here is the podium. Watch until the end.",
           "puesto": {3: "In third place, {t}, by {n}, with {x} {u}.", 2: "In second place, {t}, by {n}, with {x} {u}.",
                      1: "And number one: {t}, by {n}, with {x} {u}."},
           "cierre": "The full countdown, from ten to one, is already on the channel. Find it in the description. Hashtag Top 10 RS.",
           "titulo": "The {c} video in {r} this week 🏆 #shorts",
           "desc": "The podium of the {c} videos in {r} this week.\n\nFull countdown, from 10 to 1: {url}\n\nData from the official YouTube API. Synthetic voice narration. #Top10RS #shorts",
           "tags": ["top 10", "viral videos", "youtube trends", "shorts", "top 10 social media"]},
}


def redondeo(n, lang):
    """Cifra hablada, redondeada hacia abajo: 30.484.875 -> 'más de 30 millones'."""
    n = int(n)
    mas = "más de " if lang == "es" else "over "
    if n >= 1_000_000:
        v = n // 1_000_000
        return f"{mas}{v} {'millones' if lang == 'es' else 'million'}" if v > 1 or lang == "en" else f"{mas}un millón"
    if n >= 1_000:
        return f"{mas}{n // 1000} {'mil' if lang == 'es' else 'thousand'}"
    return str(n)


def cifra(n, u, lang):
    x = redondeo(n, lang)
    return f"{x} de {u}" if lang == "es" and ("millón" in x or "millones" in x) else f"{x} {u}"


def titulo_corto(t, n=55):
    import re
    t = re.sub(r"\s*#\w+", "", t or "").strip(" -|·")
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(" ,.;:-") + "…"


def region(g):
    r = g.get("tema", "").split("·")[0].replace("Top 10", "").strip()
    return {"the World": "the world", "el Mundo": "el mundo"}.get(r, r) or g.get("edicion", "")


def main():
    ahora = datetime.now(timezone.utc)
    hechos = 0
    for gj in sorted(PROY.glob("*/guion.json")):
        ed = gj.parent
        g = json.loads(gj.read_text())
        if g.get("tipo") != "top10" or not (ed / "publicado.json").exists() or not (ed / "categorias3.json").exists():
            continue
        pub = g.get("seo", {}).get("publicar_en")
        if not pub:  # ya se publicó sin hora programada (edición vieja): no se rellena
            continue
        base = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        if "--todas" not in sys.argv and base < ahora - timedelta(hours=24):
            continue
        lang = g.get("lang") if g.get("lang") in TXT else "en"
        T, url = TXT[lang], json.loads((ed / "publicado.json").read_text())["url"]
        cats = json.loads((ed / "categorias3.json").read_text())
        r = region(g)
        for cat, off in OFFSETS.items():
            lista = cats.get(cat) or []
            if len(lista) < 3:
                continue
            cuando = base + off
            d = PROY / f"{cuando:%Y-%m-%d}-{lang}-short-top10-{g.get('edicion', ed.name)}-{cat}"
            if (d / "guion.json").exists():
                continue
            c, u, etq = T["cat"][cat]
            esc = [{"id": "gancho", "capitulo": "Inicio", "texto": T["gancho"].format(c=c, r=r), "emocion": "gancho",
                    "video_id": lista[0]["post_id"], "solo_fondo": True}]
            for p in (3, 2, 1):
                v = lista[p - 1]
                esc.append({"id": f"p{p}", "texto": T["puesto"][p].format(t=titulo_corto(v["title"]), n=(v["creator_name"] or "").strip(), x=cifra(v[cat], u, lang), u="").replace("  ", " ").replace(" .", "."),
                            "emocion": "agil" if p > 1 else "enfasis", "video_id": v["post_id"], "puesto": p,
                            "creador": (v["creator_name"] or "").strip(), "cifra": int(v[cat]), "categoria": etq})
            esc.append({"id": "cierre", "texto": T["cierre"], "emocion": "calido", "video_id": lista[0]["post_id"], "solo_fondo": True})
            short = {"lang": lang, "tipo": "short", "top10_short": True, "voz_fundador": bool(g.get("voz_fundador")),
                     "edicion": g.get("edicion"), "fecha": f"{cuando:%Y-%m-%d}", "tema": f"{g.get('tema')} · {etq}",
                     "color_marca": g.get("color_marca", [255, 45, 120]), "contenido_sintetico": True,
                     "miniatura": {"linea1": f"#1 {etq}", "linea2": r.upper(), "etiqueta": "TOP 10 RS", "imagen": "p1"},
                     "seo": {"titulo": T["titulo"].format(c=c, r=r)[:100], "descripcion": T["desc"].format(c=c, r=r, url=url),
                             "tags": T["tags"], "hashtags": ["Top10RS", "shorts"], "categoria_id": "24",
                             "privacidad": "private", "publicar_en": cuando.strftime("%Y-%m-%dT%H:%M:%SZ"), "lista_id": None},
                     "escenas": esc}
            d.mkdir(parents=True, exist_ok=True)
            (d / "guion.json").write_text(json.dumps(short, ensure_ascii=False, indent=2))
            hechos += 1
            print(f"+ {d.name}  ({short['seo']['publicar_en']})")
    print(f"Shorts nuevos del Top 10: {hechos}")


if __name__ == "__main__":
    main()
