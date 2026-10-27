"""Comunidad del Top 10: responde comentarios (saludo con @mención y FOMO), cuenta hashtags y mide las metas
de la premiación en vivo. Estado en canales/top10-redes/comunidad.json; resumen en canales/top10-redes/METAS.md.
Uso: python comunidad.py   (token de top10-redes)
Cuota: lectura 1 unidad por página; cada respuesta 50 unidades → tope RESPUESTAS_MAX por corrida.
"""
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANAL = "top10-redes"
ESTADO = ROOT / "canales" / CANAL / "comunidad.json"
RESUMEN = ROOT / "canales" / CANAL / "METAS.md"
MAX_RESP = int(os.environ.get("RESPUESTAS_MAX", "40"))
METAS = {"suscriptores": 1_000_000, "likes": 50_000, "comentarios": 500_000, "Top10RS": 50_000, "PremiosTop10RS": 50_000}

R = {  # variantes para que ninguna respuesta se repita igual (YouTube castiga el texto idéntico)
    "es": {
        "premios": ["¡Voto registrado, {u}! 🏆 Ya vamos {p} de 50 000 #PremiosTop10RS rumbo a la premiación EN VIVO. Comparte el video: cada voto cuenta.",
                    "{u}, ¡tu #PremiosTop10RS ya suma! 🏆 Llevamos {p}. Cuando lleguemos a 50 000, la premiación será en vivo… y no querrás perdértela.",
                    "¡Eso, {u}! 🙌 Voto número {p} para la premiación en vivo. Activa la campana: los ganadores se anuncian primero aquí."],
        "top10": ["¡Estás dentro, {u}! 🔥 Ya somos {t} con #Top10RS. El domingo sale la nueva vuelta al mundo: activa la campana y entérate primero.",
                  "{u}, ¡gracias por sumar tu #Top10RS! 🌎 Vamos {t}. ¿Quién crees que será el #1 la próxima semana? Te leemos.",
                  "¡Anotado, {u}! 👀 Llevamos {t} #Top10RS. Quien adivine el próximo #1 se gana un saludo en el video."],
        "general": ["¡Gracias por comentar, {u}! 👀 El próximo domingo hay un nuevo #1… ¿lo adivinas? Déjalo aquí con #Top10RS.",
                    "{u}, ¡qué bueno tenerte aquí! 🔥 ¿Quieres premiación en vivo para los ganadores? Comenta #PremiosTop10RS y suma tu voto.",
                    "¡Saludos, {u}! 🌎 Activa la campana: cada domingo, la vuelta al mundo en 10 videos. ¿Cuál fue tu favorito?"],
    },
    "en": {
        "premios": ["Vote counted, {u}! 🏆 We're at {p} of 50,000 #PremiosTop10RS on the road to a LIVE award show. Share the video: every vote counts.",
                    "{u}, your #PremiosTop10RS is in! 🏆 That's {p} so far. At 50,000 the awards go live… you won't want to miss it.",
                    "Yes, {u}! 🙌 Vote number {p} for the live awards. Hit the bell: winners are announced here first."],
        "top10": ["You're in, {u}! 🔥 {t} #Top10RS and counting. A new world tour drops Sunday: hit the bell and be the first to know.",
                  "{u}, thanks for adding your #Top10RS! 🌎 We're at {t}. Who do you think takes #1 next week? Tell us.",
                  "Noted, {u}! 👀 {t} #Top10RS so far. Guess next week's #1 and get a shout-out in the video."],
        "general": ["Thanks for commenting, {u}! 👀 There's a new #1 next Sunday… can you guess it? Drop it here with #Top10RS.",
                    "{u}, great to have you here! 🔥 Want a live award show for the winners? Comment #PremiosTop10RS to vote.",
                    "Hi {u}! 🌎 Hit the bell: every Sunday, the world tour in 10 videos. Which one was your favorite?"],
    },
}


def idiomas_por_video():
    m = {}
    for pub in (ROOT / "canales" / CANAL / "proyectos").glob("*/publicado.json"):
        g = json.loads((pub.parent / "guion.json").read_text())
        m[json.loads(pub.read_text())["video_id"]] = g.get("lang", "es")
    return m


def cuenta(texto, tag):
    return len(re.findall(rf"#{tag}\b", texto, flags=re.I))


def main():
    S = json.loads(ESTADO.read_text()) if ESTADO.exists() else {
        "hasta": "1970-01-01T00:00:00Z", "Top10RS": 0, "PremiosTop10RS": 0, "respondidos": []}
    yt = service(CANAL)
    ch = yt.channels().list(part="id,statistics,contentDetails", mine=True).execute()["items"][0]
    cid = ch["id"]
    langs = idiomas_por_video()
    nuevos, tope, token = [], S["hasta"], None
    while True:  # hilos más recientes primero; se detiene en lo ya contado
        r = yt.commentThreads().list(part="snippet", allThreadsRelatedToChannelId=cid, order="time", maxResults=100,
                                     textFormat="plainText", pageToken=token).execute()
        fin = False
        for it in r.get("items", []):
            top = it["snippet"]["topLevelComment"]["snippet"]
            if top["publishedAt"] <= S["hasta"]:
                fin = True
                break
            nuevos.append(it)
            tope = max(tope, top["publishedAt"])
        token = r.get("nextPageToken")
        if fin or not token or len(nuevos) > 5000:
            break
    for it in nuevos:
        txt = it["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        S["Top10RS"] += cuenta(txt, "Top10RS")
        S["PremiosTop10RS"] += cuenta(txt, "PremiosTop10RS")
    S["hasta"] = tope
    # respuestas: primero quien vota o usa el hashtag; nunca a nosotros mismos, ni a enlaces/spam
    hechas = 0
    orden = sorted(nuevos, key=lambda it: -(2 * cuenta(it["snippet"]["topLevelComment"]["snippet"]["textDisplay"], "PremiosTop10RS")
                                             + cuenta(it["snippet"]["topLevelComment"]["snippet"]["textDisplay"], "Top10RS")))
    for it in orden:
        if hechas >= MAX_RESP:
            break
        top = it["snippet"]["topLevelComment"]["snippet"]
        tid = it["id"]
        if top["publishedAt"] < (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"):
            continue  # solo conversaciones frescas
        if tid in S["respondidos"] or top.get("authorChannelId", {}).get("value") == cid or "http" in top["textDisplay"]:
            continue
        lang = "es" if langs.get(it["snippet"].get("videoId"), "es") == "es" else "en"
        txt = top["textDisplay"]
        tipo = "premios" if cuenta(txt, "PremiosTop10RS") else ("top10" if cuenta(txt, "Top10RS") else "general")
        opciones = R[lang][tipo]
        k = int(hashlib.md5(tid.encode()).hexdigest(), 16) % len(opciones)
        u = top.get("authorDisplayName", "")
        u = u if u.startswith("@") else u.split()[0] if u else ""
        resp = opciones[k].format(u=u, p=f"{S['PremiosTop10RS']:,}".replace(",", " "), t=f"{S['Top10RS']:,}".replace(",", " "))
        try:
            yt.comments().insert(part="snippet", body={"snippet": {"parentId": tid, "textOriginal": resp}}).execute()
            hechas += 1
            S["respondidos"] = (S["respondidos"] + [tid])[-5000:]
        except Exception as e:  # comentario borrado o cerrado: se sigue
            print("comunidad: aviso al responder:", str(e)[:160])
    # métricas de las metas
    likes = comentarios = 0
    ids, tok = [], None
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
        ids += [x["contentDetails"]["videoId"] for x in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute().get("items", []):
            likes += int(v["statistics"].get("likeCount", 0))
            comentarios += int(v["statistics"].get("commentCount", 0))
    actual = {"suscriptores": int(ch["statistics"].get("subscriberCount", 0)), "likes": likes, "comentarios": comentarios,
              "Top10RS": S["Top10RS"], "PremiosTop10RS": S["PremiosTop10RS"]}
    S["metas"] = actual
    S["actualizado"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ESTADO.write_text(json.dumps(S, ensure_ascii=False, indent=1))
    nombres = {"suscriptores": "Suscriptores (YouTube)", "likes": "Likes", "comentarios": "Comentarios",
               "Top10RS": "#Top10RS en comentarios", "PremiosTop10RS": "#PremiosTop10RS en comentarios"}
    filas = [f"| {nombres[k]} | {actual[k]:,} | {METAS[k]:,} | {min(100, actual[k] * 100 // METAS[k])}% |" for k in METAS]
    RESUMEN.write_text("# Metas de la premiación en vivo · Top 10 Redes Sociales\n\n"
                       f"Actualizado: {S['actualizado']} (UTC)\n\n| Meta | Hoy | Objetivo | Avance |\n|---|---|---|---|\n"
                       + "\n".join(filas).replace(",", " ") + "\n\nLa premiación en vivo se activa al cumplir TODAS las metas.\n")
    print(f"comunidad: {len(nuevos)} comentarios nuevos, {hechas} respuestas · {actual}")


if __name__ == "__main__":
    main()
