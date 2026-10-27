"""Top 10 semanal por continente + Mundial, 100 % automático (sin Claude, sin IA que invente).

Corre en GitHub Actions el domingo 04:55 UTC (sábado 23:55 Lima). Para cada edición de top10_ediciones.json:
  1. Datos: videos en tendencia (videos.list chart=mostPopular, 1 unidad/página) de cada país del continente
     + búsqueda de los más vistos de la semana en sus países grandes. Solo videos publicados en los últimos 7 días.
     Fuera: música (cat. 10), noticias/política (25), transmisiones en vivo, videos de más de 150 min y top10_vetos.json.
  2. Ranking: más vistos, más comentados y más likes, un video por creador, del 10 al 1.
  3. Guion por plantilla en el idioma de la edición, con cifras reales y datos calculados (nada inventado), sin
     revelar el podio antes de tiempo. SEO, hashtags, títulos/descripciones traducidos y hora de publicación.
Escribe canales/top10-redes/proyectos/<fecha>-<lang>-top10-<edición>/{guion.json,categorias3.json}
y la lista de proyectos en top10_matriz.json (para el job en paralelo).
Uso: python top10_semana.py   (necesita ~/.yt-agent/token_top10-redes.json)
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from babel import Locale
from num2words import num2words

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
S = Path(__file__).parent
CFG = json.loads((S / "top10_ediciones.json").read_text())
VETOS = json.loads((S / "top10_vetos.json").read_text()) if (S / "top10_vetos.json").exists() else {}
FUERA_CAT = {"10", "25"}
EXTRA_CONT = {"CY": "europa", "MT": "europa", "IS": "europa", "BA": "europa", "MK": "europa", "AL": "europa", "MD": "europa",
              "BY": "europa", "ME": "europa", "AM": "asia", "MN": "asia", "KH": "asia", "LA": "asia", "MM": "asia",
              "UZ": "asia", "KG": "asia", "TJ": "asia", "AF": "asia", "IR": "asia", "SY": "asia", "PS": "asia",
              "CM": "africa", "CI": "africa", "ET": "africa", "SD": "africa", "AO": "africa", "MZ": "africa", "RW": "africa",
              "ZM": "africa", "BW": "africa", "NA": "africa", "ML": "africa", "BF": "africa", "BJ": "africa", "CD": "africa",
              "CU": "america", "HT": "america", "TT": "america", "BS": "america", "BB": "america", "BZ": "america",
              "GY": "america", "SR": "america", "FJ": "oceania", "WS": "oceania", "TO": "oceania"}


def continente_de(pais):
    for e in CFG["ediciones"]:
        if e["regiones"] != "todas" and pais in e["regiones"]:
            return e["id"]
    return EXTRA_CONT.get(pais)
CANAL = "top10-redes"

# ---------------------------------------------------------------- textos (es / en narración; pt / fr metadatos)
T = {
    "es": {
        "cat": {"views": "más vistos", "comments": "más comentados", "likes": "con más likes"},
        "met": {"views": "vistas", "comments": "comentarios", "likes": "likes"},
        "cap": {"apertura": "Apertura", "reglas": "Cómo contamos", "views": "Top 10 más vistos",
                "comments": "Top 10 más comentados", "likes": "Top 10 con más likes", "podio": "El podio", "cierre": "Cierre"},
        "puesto": ["En el puesto {w}", "Puesto {w}", "En la posición número {w}", "Llegamos al puesto {w}", "Ahora, el número {w}"],
        "bronce": "Medalla de bronce", "plata": "Medalla de plata",
        "uno_cat": {"views": "de los más vistos", "comments": "de los más comentados", "likes": "en likes"},
        "uno": ["Y llegó el momento. El número uno", "Redoble de tambores. El número uno", "Y ahora sí, el número uno"],
        "desde": "desde {p}", "con": "con «{t}»", "un_video": "con un video publicado hace {d}",
        "mas_de": "más de {x}", "mill": "millones", "un_mill": "un millón", "mil": "mil",
        "ins": {"rapido": "Fue el que más rápido creció de esta lista: cerca de {x} vistas por hora.",
                "inter": "Tiene la mejor tasa de interacción de esta lista: {x} de cada cien personas dieron like o comentaron.",
                "chico": "Y ojo: es un canal de unos {x} suscriptores que esta semana jugó en las grandes ligas.",
                "short": "Un Short de apenas {x} segundos.",
                "largo": "Un video de más de {x} minutos, y aun así la gente se quedó a verlo.",
                "nuevo": "Lo logró en apenas {x}."},
        "otros": "Además suma {x}.",
        "intro_cat": {"views": "Empezamos con los diez videos más vistos.",
                      "comments": "Pasamos a la conversación: los diez videos más comentados.",
                      "likes": "Y la última lista: los diez videos con más likes."},
        "apertura": "Esta semana, en {c}, millones de personas vieron, comentaron y compartieron sin parar. Entre los treinta videos de este conteo suman {x}. Pero solo uno se quedó con el número uno. Bienvenidos a Top 10 Redes Sociales, edición {c}. Hoy, los diez videos más vistos, los diez más comentados y los diez con más likes de la semana. Quédate hasta el final, porque el número uno no lo vas a adivinar.",
        "reglas": "Las reglas, rápido y claro. Solo entran videos publicados en los últimos siete días que fueron tendencia en {c}. Un solo video por creador en cada lista. La música y las noticias tienen su propio espacio. Todas las cifras salen de la API oficial de YouTube, medidas este domingo. Empecemos.",
        "cierre_sig": "Y aquí no termina la vuelta al mundo. La siguiente parada es {s}: el enlace está en la descripción y en la lista de reproducción.",
        "cierre_fin": "Así terminó la vuelta al mundo de esta semana.",
        "cierre": "Ahora te toca a ti: ¿qué video debió estar en este conteo? Escríbelo en los comentarios con el hashtag {h}. Todos los enlaces a los videos originales están en la descripción: ve y apoya a los creadores. Suscríbete y activa la campana. Cada domingo, un nuevo Top 10.",
        "mundial_ap": "Recorrimos Oceanía, Asia, África, Europa y América. Ahora, el ranking que lo reúne todo: el Top 10 mundial de la semana.",
    },
    "en": {
        "cat": {"views": "most viewed", "comments": "most commented", "likes": "most liked"},
        "met": {"views": "views", "comments": "comments", "likes": "likes"},
        "cap": {"apertura": "Intro", "reglas": "How we count", "views": "Top 10 most viewed",
                "comments": "Top 10 most commented", "likes": "Top 10 most liked", "podio": "The podium", "cierre": "Outro"},
        "puesto": ["At number {w}", "Number {w}", "Coming in at number {w}", "Next up, number {w}", "In position number {w}"],
        "bronce": "Bronze medal", "plata": "Silver medal",
        "uno_cat": {"views": "most viewed", "comments": "most commented", "likes": "most liked"},
        "uno": ["And here it is. Number one", "Drum roll, please. Number one", "And finally, number one"],
        "desde": "from {p}", "con": "with “{t}”", "un_video": "with a video posted {d} ago",
        "mas_de": "over {x}", "mill": "million", "un_mill": "one million", "mil": "thousand",
        "ins": {"rapido": "It was the fastest-growing video on this list: about {x} views per hour.",
                "inter": "It has the best engagement rate on this list: {x} out of every hundred viewers liked or commented.",
                "chico": "And get this: it's a channel with about {x} subscribers, playing in the big leagues this week.",
                "short": "A Short of just {x} seconds.",
                "largo": "A video over {x} minutes long, and people still stayed to watch.",
                "nuevo": "It got there in just {x}."},
        "otros": "It also has {x}.",
        "intro_cat": {"views": "Let's start with the ten most viewed videos.",
                      "comments": "Now for the conversation: the ten most commented videos.",
                      "likes": "And the last list: the ten most liked videos."},
        "apertura": "This week in {c}, millions of people watched, commented and shared non-stop. The thirty videos in this countdown add up to {x}. But only one took number one. Welcome to Top 10 Social Media, {c} edition. Today: the ten most viewed, the ten most commented and the ten most liked videos of the week. Stay until the end, because you won't guess number one.",
        "reglas": "The rules, quick and clear. Only videos posted in the last seven days that trended in {c}. One video per creator on each list. Music and news have their own space. Every number comes from the official YouTube API, measured this Sunday. Let's go.",
        "cierre_sig": "And the world tour isn't over. Next stop: {s}. The link is in the description and in the playlist.",
        "cierre_fin": "And that wraps up this week's world tour.",
        "cierre": "Now it's your turn: which video should have made this countdown? Tell us in the comments with the hashtag {h}. Links to every original video are in the description: go support the creators. Subscribe and hit the bell. A new Top 10 every Sunday.",
        "mundial_ap": "We toured Oceania, Asia, Africa, Europe and the Americas. Now, the ranking that brings it all together: this week's global Top 10.",
    },
}
# Metadatos (título y descripción) en cada idioma
M = {
    "es": {"titulo": "Top 10 {c}: lo más visto, comentado y con más likes | Semana {n}",
           "intro": "Los 10 videos más vistos, más comentados y con más likes de YouTube en {c} esta semana. Cifras reales, del 10 al 1.",
           "alfa": "Creadores de esta edición (en orden alfabético: el puesto de cada uno se revela en el video):",
           "cats": {"views": "👀 MÁS VISTOS", "comments": "💬 MÁS COMENTADOS", "likes": "❤️ MÁS LIKES"},
           "metodo": "📊 CÓMO CONTAMOS: videos publicados en los últimos 7 días que fueron tendencia en {c}. Un video por creador en cada lista. Sin música ni noticias. Cifras de la API oficial de YouTube, medidas el domingo.",
           "cta": "💬 ¿Quién faltó? Coméntalo con #{h}. Apoya a los creadores: mira sus videos originales.",
           "ia": "Narración con la voz del autor recreada con IA."},
    "en": {"titulo": "Top 10 {c}: Most Viewed, Commented & Liked on YouTube | Week {n}",
           "intro": "The 10 most viewed, most commented and most liked YouTube videos in {c} this week. Real numbers, from 10 to 1.",
           "alfa": "Creators in this edition (alphabetical order: each ranking is revealed in the video):",
           "cats": {"views": "👀 MOST VIEWED", "comments": "💬 MOST COMMENTED", "likes": "❤️ MOST LIKED"},
           "metodo": "📊 HOW WE COUNT: videos posted in the last 7 days that trended in {c}. One video per creator on each list. No music or news. Numbers from the official YouTube API, measured on Sunday.",
           "cta": "💬 Who was missing? Comment with #{h}. Support the creators: watch their original videos.",
           "ia": "Narrated with the author's voice recreated with AI."},
    "pt": {"titulo": "Top 10 {c}: os mais vistos, comentados e curtidos | Semana {n}",
           "intro": "Os 10 vídeos mais vistos, mais comentados e mais curtidos do YouTube em {c} nesta semana. Números reais, do 10 ao 1.",
           "alfa": "Criadores desta edição (em ordem alfabética: a posição de cada um é revelada no vídeo):",
           "cats": {"views": "👀 MAIS VISTOS", "comments": "💬 MAIS COMENTADOS", "likes": "❤️ MAIS CURTIDOS"},
           "metodo": "📊 COMO CONTAMOS: vídeos publicados nos últimos 7 dias que estiveram em alta em {c}. Um vídeo por criador em cada lista. Sem música nem notícias. Números da API oficial do YouTube, medidos no domingo.",
           "cta": "💬 Quem faltou? Comente com #{h}. Apoie os criadores: assista aos vídeos originais.",
           "ia": "Narração com a voz do autor recriada com IA."},
    "fr": {"titulo": "Top 10 {c} : les plus vues, commentées et aimées | Semaine {n}",
           "intro": "Les 10 vidéos YouTube les plus vues, les plus commentées et les plus aimées en {c} cette semaine. De vrais chiffres, du 10 au 1.",
           "alfa": "Créateurs de cette édition (ordre alphabétique : le classement est révélé dans la vidéo) :",
           "cats": {"views": "👀 LES PLUS VUES", "comments": "💬 LES PLUS COMMENTÉES", "likes": "❤️ LES PLUS AIMÉES"},
           "metodo": "📊 MÉTHODE : vidéos publiées ces 7 derniers jours et en tendance en {c}. Une vidéo par créateur et par liste. Ni musique ni actualités. Chiffres de l'API officielle de YouTube, mesurés le dimanche.",
           "cta": "💬 Qui manque ? Commente avec #{h}. Soutiens les créateurs : regarde leurs vidéos originales.",
           "ia": "Narration avec la voix de l'auteur recréée par IA."},
}


def elegir(opciones, semilla):
    return opciones[int(hashlib.md5(semilla.encode()).hexdigest(), 16) % len(opciones)]


def w(n, lang):
    return num2words(int(n), lang=lang)


def wn(n, lang):
    """Número delante de un sustantivo masculino: 'treinta y un segundos', 'veintiún días'."""
    x = w(n, lang)
    if lang == "es":
        x = re.sub(r"uno$", "ún" if x.endswith("veintiuno") else "un", x)
    return x


def aprox(n, lang, sustantivo=""):
    """'más de quince millones de vistas' / 'over fifteen million views' (redondeo hacia abajo: nunca exagera)."""
    t = T[lang]
    n = int(n or 0)
    mill = False
    if n >= 1_000_000:
        m = n / 1_000_000
        d = int(m * 10) / 10 if m < 10 else int(m)
        mill = True
        if d == int(d):
            x = num2words(int(d) * 1_000_000, lang=lang)
        else:
            sep = "coma" if lang == "es" else "point"
            x = f"{w(int(d), lang)} {sep} {w(round((d - int(d)) * 10), lang)} {t['mill']}"
        if lang == "es" and int(d) == 1 and d == 1:
            x = "un millón"
    elif n >= 1000:
        x = num2words((n // 1000) * 1000, lang=lang)
    else:
        x = w(n, lang)
    out = t["mas_de"].format(x=x) if n >= 1000 else x
    if sustantivo:
        out += (" de " if (lang == "es" and mill) else " ") + sustantivo
    return out


def redondo(n, lang):
    n = int(n)
    if n >= 1000:
        k = 10 ** (len(str(n)) - 2)
        n = n // k * k
    return num2words(n, lang=lang)


def dias_txt(d, lang):
    if d == 1:
        return "un día" if lang == "es" else "one day"
    return f"{wn(d, lang)} {'días' if lang == 'es' else 'days'}"


def dur_seg(iso):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def titulo_limpio(t):
    t = re.sub(r"[#@]\S+", "", t or "")
    t = re.sub(r"[^\w\s¿?¡!,.'’:\-áéíóúüñÁÉÍÓÚÜÑçÇãõâêôàèìòù]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -:|")
    letras = [c for c in t if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) / len(letras) > 0.5:
        t = t.capitalize()
    return t


# ---------------------------------------------------------------- datos
def recolectar(yt, ini, fin):
    todas = sorted({r for e in CFG["ediciones"] if e["regiones"] != "todas" for r in e["regiones"]})
    vids, regiones_de = {}, {}

    def guarda(items, reg):
        for v in items:
            vids[v["id"]] = v
            regiones_de.setdefault(v["id"], set()).add(reg)

    for reg in todas:
        tok = None
        for _ in range(4):
            try:
                r = yt.videos().list(part="snippet,statistics,contentDetails,status", chart="mostPopular", regionCode=reg,
                                     maxResults=50, pageToken=tok).execute()
            except Exception as e:
                print(f"  región {reg}: {str(e)[:80]}")
                break
            guarda(r.get("items", []), reg)
            tok = r.get("nextPageToken")
            if not tok:
                break
    extra = {}
    for e in CFG["ediciones"]:
        for reg in e["busqueda"]:
            try:
                r = yt.search().list(part="id", type="video", order="viewCount", regionCode=reg, maxResults=50,
                                     publishedAfter=ini.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     publishedBefore=fin.strftime("%Y-%m-%dT%H:%M:%SZ")).execute()
                for it in r.get("items", []):
                    extra.setdefault(it["id"]["videoId"], set()).add(reg)
            except Exception as ex:
                print(f"  búsqueda {reg}: {str(ex)[:80]}")
    faltan = [v for v in extra if v not in vids]
    for i in range(0, len(faltan), 50):
        for v in yt.videos().list(part="snippet,statistics,contentDetails,status", id=",".join(faltan[i:i + 50])).execute().get("items", []):
            vids[v["id"]] = v
    for v, regs in extra.items():
        regiones_de.setdefault(v, set()).update(regs)
    # canales: país, suscriptores, @handle
    chans = {}
    cl = list({v["snippet"]["channelId"] for v in vids.values()})
    for i in range(0, len(cl), 50):
        for c in yt.channels().list(part="snippet,statistics", id=",".join(cl[i:i + 50])).execute().get("items", []):
            chans[c["id"]] = c
    out = []
    vetados_c, vetados_v = set(VETOS.get("canales", [])), set(VETOS.get("videos", []))
    for vid, v in vids.items():
        s, st, cd = v["snippet"], v.get("statistics", {}), v.get("contentDetails", {})
        pub = datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00"))
        seg = dur_seg(cd.get("duration"))
        if not (ini <= pub <= fin) or s.get("categoryId") in FUERA_CAT or s.get("liveBroadcastContent", "none") != "none":
            continue
        if seg == 0 or seg > 150 * 60 or vid in vetados_v or s["channelId"] in vetados_c or "viewCount" not in st:
            continue
        if v.get("status", {}).get("madeForKids"):
            continue  # contenido infantil: fuera
        vw, lk, cm = int(st["viewCount"]), int(st.get("likeCount", 0) or 0), int(st.get("commentCount", 0) or 0)
        if vw >= 1_000_000 and lk / vw < 0.0005 and cm / vw < 0.00002:
            continue  # casi sin likes ni comentarios para tantas vistas: típico de anuncios pagados
        c = chans.get(s["channelId"], {})
        out.append({
            "post_id": vid, "url": f"https://youtu.be/{vid}", "title": s.get("title", ""),
            "creator_id": s["channelId"], "creator_name": s.get("channelTitle", ""),
            "handle": (c.get("snippet", {}).get("customUrl") or ""), "country": c.get("snippet", {}).get("country"),
            "followers": int(c.get("statistics", {}).get("subscriberCount", 0) or 0),
            "language": (s.get("defaultAudioLanguage") or s.get("defaultLanguage") or "")[:2],
            "published_at": s["publishedAt"], "segundos": seg, "category_id": s.get("categoryId"),
            "views": int(st["viewCount"]), "likes": int(st["likeCount"]) if "likeCount" in st else None,
            "comments": int(st["commentCount"]) if "commentCount" in st else None,
            "regiones": sorted(regiones_de.get(vid, [])),
        })
    return out


def ranking(videos, metrica):
    vistos, lista = set(), []
    for v in sorted((x for x in videos if x.get(metrica)), key=lambda x: -x[metrica]):
        if v["creator_id"] in vistos:
            continue
        vistos.add(v["creator_id"])
        lista.append(v)
        if len(lista) == 10:
            break
    return lista


# ---------------------------------------------------------------- guion
def pais(code, lang):
    try:
        return Locale.parse(lang).territories.get(code) if code else None
    except Exception:
        return None


def texto_puesto(v, rank, k, lista, lang, fin, semilla):
    t = T[lang]
    if rank == 1:
        cab = elegir(t["uno"], semilla) + " " + t["uno_cat"][k] + ","
    elif rank == 2:
        cab = t["plata"] + ","
    elif rank == 3:
        cab = t["bronce"] + ","
    else:
        cab = elegir(t["puesto"], semilla).format(w=w(rank, lang)) + ","
    p = pais(v.get("country"), lang)
    partes = [cab]
    if p:
        partes.append(t["desde"].format(p=p) + ",")
    partes.append(v["creator_name"] + ",")
    tl = titulo_limpio(v["title"])
    dias = max(1, (fin - datetime.fromisoformat(v["published_at"].replace("Z", "+00:00"))).days)
    if v.get("language") == lang and 4 <= len(tl) <= 70:
        partes.append(t["con"].format(t=tl) + ".")
    else:
        partes.append(t["un_video"].format(d=dias_txt(dias, lang)) + ".")
    frase = " ".join(partes)
    frase = frase[0].upper() + frase[1:]
    cifra = aprox(v[k], lang, t["met"][k])
    frase += f" {cifra[0].upper() + cifra[1:]}."
    # datos calculados (todos reales)
    horas = {x["post_id"]: max(1.0, (fin - datetime.fromisoformat(x["published_at"].replace("Z", "+00:00"))).total_seconds() / 3600) for x in lista}
    vph = {x["post_id"]: x["views"] / horas[x["post_id"]] for x in lista}
    inter = {x["post_id"]: ((x.get("likes") or 0) + (x.get("comments") or 0)) / max(1, x["views"]) for x in lista}
    ins = []
    if v["post_id"] == max(vph, key=vph.get):
        ins.append(t["ins"]["rapido"].format(x=redondo(vph[v["post_id"]], lang)))
    if v["post_id"] == max(inter, key=inter.get) and inter[v["post_id"]] >= 0.01:
        xi = w(round(inter[v["post_id"]] * 100), lang)
        ins.append(t["ins"]["inter"].format(x=re.sub(r"uno$", "una", xi) if lang == "es" else xi))
    if 0 < v.get("followers", 0) < 200_000:
        ins.append(t["ins"]["chico"].format(x=redondo(v["followers"], lang)))
    if v["segundos"] <= 60:
        ins.append(t["ins"]["short"].format(x=wn(v["segundos"], lang)))
    elif v["segundos"] >= 20 * 60:
        ins.append(t["ins"]["largo"].format(x=wn(v["segundos"] // 60, lang)))
    if dias <= 2:
        ins.append(t["ins"]["nuevo"].format(x=dias_txt(dias, lang)))
    frase += " " + " ".join(ins[:2])
    otro = [m for m in ("views", "comments", "likes") if m != k and v.get(m)]
    if otro and len(ins) < 2:
        m = otro[0]
        frase += " " + t["otros"].format(x=aprox(v[m], lang, t["met"][m]))
    return re.sub(r"\s+", " ", frase).strip()


def descripcion(lang, cont, cats, h_canal, h_ed, semana_n):
    m = M[lang]
    L = [m["intro"].format(c=cont), "", m["alfa"]]
    for k in ("views", "comments", "likes"):
        L.append("")
        L.append(m["cats"][k])
        for v in sorted(cats[k], key=lambda x: x["creator_name"].lower()):
            h = f" ({v['handle']})" if v.get("handle", "").startswith("@") else ""
            L.append(f"▶ {v['creator_name']}{h} — {v['url']}")
    an = CFG.get("anuncio") or {}
    if an and an.get("desc", {}).get(lang) and semana_n <= an.get("hasta_semana", "").split("W")[-1]:
        L[0:0] = [an["desc"][lang], ""]
    L += ["", m["metodo"].format(c=cont), "", m["cta"].format(h=h_canal), "", m["ia"]]
    return "\n".join(L)[:4600]


def guion_edicion(ed, cats, fin, semana_iso, siguiente):
    lang = ed["lang"]
    t = T[lang]
    cont = ed["nombre"][lang]
    n = semana_iso.split("W")[-1]
    h_canal, h_ed = CFG["hashtag_canal"], ed["hashtag"]
    total = sum(v["views"] for k in cats for v in cats[k] if k in ("views", "comments", "likes"))
    escenas = []
    ap = t["apertura"].format(c=cont, x=aprox(total, lang, t["met"]["views"]))
    if ed["id"] == "mundial":
        ap = t["mundial_ap"] + " " + ap
    escenas.append({"id": "apertura", "capitulo": t["cap"]["apertura"], "emocion": "gancho", "texto": ap,
                    "tarjeta": {"titulo": f"TOP 10 · {cont.upper()}", "sub": f"{'Semana' if lang == 'es' else 'Week'} {n}"}})
    escenas.append({"id": "reglas", "capitulo": t["cap"]["reglas"], "emocion": "agil", "texto": t["reglas"].format(c=cont),
                    "tarjeta": {"titulo": "LAS REGLAS" if lang == "es" else "THE RULES", "sub": "YouTube API · 7 días" if lang == "es" else "YouTube API · 7 days"}})
    for k, letra in (("views", "v"), ("comments", "c"), ("likes", "l")):
        lista = cats[k]
        for i, v in enumerate(reversed(lista)):
            rank = len(lista) - i
            e = {"id": f"{letra}{rank:02d}", "video_id": v["post_id"], "rank": rank,
                 "modo": "completo" if k == "views" else "rapido",
                 "emocion": "gancho" if rank == 1 else ("enfasis" if rank <= 3 else "agil"),
                 "texto": texto_puesto(v, rank, k, lista, lang, fin, f"{semana_iso}{ed['id']}{k}{rank}")}
            if i == 0:
                e["capitulo"] = t["cap"][k]
                e["texto"] = t["intro_cat"][k] + " " + e["texto"]
            elif rank == 3 and k == "views":
                e["capitulo"] = t["cap"]["podio"]
            escenas.append(e)
    cierre = (t["cierre_sig"].format(s=siguiente) if siguiente else t["cierre_fin"]) + " " + t["cierre"].format(h=h_canal)
    an = CFG.get("anuncio") or {}
    if an and semana_iso <= an.get("hasta_semana", "") and an.get(lang):
        cierre = an[lang] + " " + cierre
    escenas.append({"id": "cierre", "capitulo": t["cap"]["cierre"], "emocion": "calido", "texto": cierre,
                    "tarjeta": {"titulo": f"#{h_canal}", "sub": (f"→ {siguiente}" if siguiente else "")}})
    hh, mm = map(int, ed["publicar_utc"].split(":"))
    publicar = fin.replace(hour=hh, minute=mm, second=0, microsecond=0)
    locs = {}
    for l2 in ed["locs"]:
        c2 = ed["nombre"].get(l2, cont)
        locs[l2] = {"title": M[l2]["titulo"].format(c=ed.get("titulo", {}).get(l2, c2), n=n)[:100],
                    "description": descripcion(l2, c2, cats, h_canal, h_ed, n)}
    podio = [cats[k][0]["creator_name"].lower() for k in cats if cats[k]]
    tags = ([f"top 10 {cont.lower()}", "top 10", "top 10 youtube", "virales" if lang == "es" else "viral videos",
             "lo más visto" if lang == "es" else "most viewed", "tendencias" if lang == "es" else "trending",
             "top 10 redes sociales", h_canal.lower(), h_ed.lower()] + podio)
    return {
        "lang": lang, "tipo": "top10", "motor": "top10-semanal", "edicion": ed["id"], "continente": cont,
        "tema": f"Top 10 {cont} · {semana_iso}", "semana": semana_iso, "voz_fundador": True,
        "color_marca": [255, 45, 120], "contenido_sintetico": True,
        "reintento_desde": (fin + timedelta(hours=10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "libreto": "plantilla", "esperar_libreto_hasta": (fin + timedelta(minutes=100)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "miniatura": {"linea1": "TOP 10", "linea2": cont.upper(), "etiqueta": f"{'SEMANA' if lang == 'es' else 'WEEK'} {n}"},
        "seo": {"titulo": M[lang]["titulo"].format(c=ed.get("titulo", {}).get(lang, cont), n=n)[:100],
                "descripcion": descripcion(lang, cont, cats, h_canal, h_ed, n),
                "tags": list(dict.fromkeys(tags)), "hashtags": [h_canal, h_ed, "Virales" if lang == "es" else "Viral"],
                "localizaciones": locs, "categoria_id": "24", "privacidad": "public",
                "publicar_en": publicar.strftime("%Y-%m-%dT%H:%M:%SZ"), "lista_id": None},
        "escenas": escenas,
    }


def main():
    fin = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    ini = fin - timedelta(days=7)
    iso = fin - timedelta(days=1)  # la semana que termina (sábado)
    semana_iso = f"{iso.isocalendar()[0]}-W{iso.isocalendar()[1]:02d}"
    yt = service(CANAL)
    videos = recolectar(yt, ini, fin)
    print(f"Videos válidos de la semana: {len(videos)}")
    eds = sorted(CFG["ediciones"], key=lambda e: e["orden"])
    lanzar = json.loads((ROOT / ".github" / "top10_lanzar.json").read_text()) if (ROOT / ".github" / "top10_lanzar.json").exists() and "--lanzar" in sys.argv else {}
    acoplar = lanzar.get("acoplar", {})  # ediciones ya publicadas que entran a la vuelta al mundo
    proyectos = []
    for i, ed in enumerate(eds):
        if ed["id"] in acoplar:
            proyectos.append(acoplar[ed["id"]])
            continue
        if ed["regiones"] == "todas":
            pool = videos
        else:
            regs = set(ed["regiones"])
            # creadores DEL continente (país del canal); si el canal no declara país, se usa dónde fue tendencia
            def del_continente(v):
                if v.get("country"):
                    return continente_de(v["country"]) == ed["id"]
                return bool(regs & set(v["regiones"])) and len({continente_de(r) for r in v["regiones"]}) == 1
            pool = [v for v in videos if del_continente(v)]
        cats = {k: ranking(pool, k) for k in ("views", "comments", "likes")}
        if min(len(c) for c in cats.values()) < 10:
            print(f"! {ed['id']}: datos insuficientes ({[len(c) for c in cats.values()]}), se omite")
            continue
        sig = eds[i + 1]["nombre"][ed["lang"]] if i + 1 < len(eds) else None
        g = guion_edicion(ed, cats, fin, semana_iso, sig)
        base = Path("/tmp/top10_prueba") if "--prueba" in sys.argv else ROOT / "canales" / CANAL / "proyectos"
        d = base / f"{fin:%Y-%m-%d}-{ed['lang']}-top10-{ed['id']}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "categorias3.json").write_text(json.dumps({**cats, "vetados": []}, ensure_ascii=False, indent=1))
        (d / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
        proyectos.append(str(d.relative_to(ROOT)) if "--prueba" not in sys.argv else str(d))
        print(f"+ {ed['id']}: {d.name} ({sum(len(e['texto'].split()) for e in g['escenas'])} palabras)")
    if "--prueba" in sys.argv:
        for p in proyectos:
            g = json.loads((Path(p) / "guion.json").read_text())
            print(f"\n=== {g['edicion']} · {g['seo']['titulo']}")
            for e in g["escenas"][2:4] + g["escenas"][11:12]:
                print("  ", e["texto"][:300])
        return
    (ROOT / "top10_matriz.json").write_text(json.dumps([p for p in proyectos if p not in acoplar.values()]))
    (ROOT / "canales" / CANAL / f"semana_{semana_iso}.json").write_text(json.dumps(
        {"semana": semana_iso, "orden": proyectos}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
