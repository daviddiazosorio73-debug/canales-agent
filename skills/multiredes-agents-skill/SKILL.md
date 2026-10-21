---
name: "multiredes-agents-skill"
description: "Produce el programa semanal Top 10 Redes Sociales: conteo LATAM ES/PT con corte sábado 23:50 Lima, Top 10 general/por red/categoría, export a la app del conductor, guion, voz gratis, render y subida."
---

# Top 10 Redes Sociales — conteo semanal y episodio (ES/PT)

Clon adaptado de `youtube-agent-skill`: reutiliza su cadena **voz → render → miniatura → SEO → subida** y le agrega **extracción → snapshot → rankings → export a la app del conductor → tarjetas con cifras verificadas**. Claude redacta y decide; los scripts cuentan. **Ninguna cifra sale de la IA: todas salen de `ranking.json`.**

Úsala cuando el usuario pida el conteo, el ranking, el top 10 de la semana, de una red o de una categoría, el episodio, la miniatura, el SEO o el material del en vivo del canal @Top10RedesSociales, /multiredes-agents-skill, o hable del programa Top 10 Redes Sociales.

## Calendario (America/Lima)

| Momento | Paso |
|---|---|
| Dom 00:00 → Sáb 23:50 (semana N) | Ventana: solo cuenta lo **publicado** dentro de ella |
| **Sáb 23:50** | Corte: extracción + `snapshot.json` congelado (paso 1) |
| Dom–Lun | Rankings, revisión del usuario, enriquecimiento (pasos 2–3) |
| Mar–Mié | Guion/libreto ES y PT, aprobación, render de apoyo (pasos 4–5) |
| **Jue 23:59** | Entrega: `videos_app.json` para la app del conductor + libreto; video de apoyo subido en privado con `publicar_en` |
| **Dom 16:00** | Programa **en vivo** con la app ViralTop10 LATAM del conductor (video 3/4 + cámara 1/4, conteo 10→1) |

En UTC: inicio = domingo 05:00Z; corte = domingo 04:50Z (sábado 23:50 Lima); estreno = domingo 21:00Z.

## Preparación del espacio de trabajo (cada sesión)

1. Crea `top10/` con `scripts/`, `config/`, `assets/`, `semanas/`, `proyectos/`.
2. Copia de la skill `youtube-agent-skill/scripts/` (búscala con `ls -d ~/.claude/skills/**/youtube-agent-skill/scripts` o equivalente): `tts.py render.py thumbnail.py metadata.py upload.py`. Si no está instalada, avisa: esta skill depende de ella.
3. Escribe los scripts de la sección **Scripts** (incluye `common.py` mejorado: acepta fuentes OTF y prioriza Inter Display) y `config/config.json`.
4. `assets/logo.png`: logo del canal con fondo transparente (marca de agua). Fuentes: Inter Display si existe en el sistema, o `assets/fonts/*Bold*.otf|ttf` y `*Regular*`.
5. `pip install requests pillow playwright edge-tts google-api-python-client google-auth-oauthlib --break-system-packages` si falta algo; `python -m playwright install chromium` si no hay Chromium; FFmpeg con libass.
6. **Persistencia:** cada ejecución programada es una sesión nueva. Guarda `semanas/<AAAA-Www>/` (sobre todo `snapshot.json`), `config/config.json` y `proyectos/` en Google Drive (carpeta `Top10RedesSociales/`) al terminar cada paso y recupéralos al empezar el siguiente.
7. Red: la sesión debe permitir `www.googleapis.com` y `api.apify.com` (y `speech.platform.bing.com` para la voz gratis). Si una conexión es rechazada, dilo y no reintentes por otra vía; el render y la voz pueden correr en la PC del usuario.

### Variables de entorno
| Variable | Uso |
|---|---|
| `YOUTUBE_API_KEY` | Extracción con la API oficial (search/videos/channels) |
| `APIFY_TOKEN` | Actors de Apify (TikTok, Instagram, Kwai, X) |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID_ES`, `ELEVENLABS_VOICE_ID_PT` | Opcional. Sin ellas se usa `--voz-gratis` |
| OAuth en `~/.yt-agent/` | Subida: ver `references/setup.md` de youtube-agent-skill; aquí un solo canal: `--canal es`. Corrección: la documentación actual de `videos.insert` indica que los proyectos de API no verificados ya **no** quedan restringidos a privado; igual se sube en privado + `publicar_en`. |

Guarda claves en un archivo privado de la sesión (permisos 600), nunca en Drive, memoria ni en la skill. Si el usuario pega una clave en el chat, úsala y recuérdale rotarla. Si falta una clave en una ejecución desatendida: haz lo que se pueda sin ella, no inventes datos y avisa qué falta.

## Flujo

### 1. Corte y extracción (sábado 23:50)
```bash
S=semanas/2026-W42; INI=2026-10-11T05:00:00Z; FIN=2026-10-18T04:50:00Z
python scripts/extract_youtube.py $S $INI $FIN
python scripts/extract_apify.py $S            # todas las redes de config.apify (o una por proceso, en paralelo)
python scripts/normalize.py $S $FIN
```
**Entradas verificadas (octubre 2026)** ya están en `config.apify` y `config.mapeo`:
- TikTok ES y PT: `clockworks/tiktok-scraper` por **hashtags** (ES: humor, recetas, futbol, baile; PT: humorbrasil, receitasfaceis…). La búsqueda con proxy BR falló ("Could not get a working device id": TikTok bloquea esa vía); `apidojo/tiktok-scraper` con `location: BR` devolvió contenido en inglés. La búsqueda con filtros `MOST_LIKED`/`PAST_MONTH` funciona en ES pero cuesta ~US$1 por 150 videos: no usarla con presupuesto cero.
- Instagram: `apify/instagram-hashtag-scraper`, `resultsType: reels`. No trae idioma ni país: se detecta idioma por palabras (es/pt).
- Kwai: `natanielsantos/kwai-scraper` por `searchTerms`. Devuelve contenido viejo y viral: se usa como "en circulación" + `views_semana`.
- X: `apidojo/tweet-scraper` con búsqueda avanzada `filter:videos min_faves:2000 lang:es since:… until:…` (**actualiza `since`/`until` cada semana** a la ventana). Su línea natural es actualidad y política: va a su Top 10 y a la categoría Actualidad. País por `author.location` (texto libre); si no se deduce, revísalo (p. ej. políticos de España).

**Presupuesto cero:** plan Free de Apify (US$5/mes): hashtags y volúmenes bajos (≈US$1 por conteo semanal). Si el conector vidIQ está disponible, sus búsquedas de tendencias/outliers sirven de apoyo para descubrir creadores nuevos (revisa su saldo antes).

Si un Actor devuelve 0 ítems, lee su log (`/v2/actor-runs/<id>/log`), cambia de vía (búsqueda → hashtags → perfiles) y no repitas la misma entrada fallida más de una vez. Si se corta la conexión mientras un Actor corre, retómalo con `--run <plataforma>=<runId>` (no se paga dos veces).

**Descubrimiento + seguimiento:** el barrido semanal por búsquedas y hashtags trae a los nuevos; desde la semana 2, agrega también en `config` los creadores que entraron a algún Top 10 y consultálos por perfil (TikTok `profiles`, Instagram profile, Kwai URL de perfil) para medir su `views_semana`.

**Primera vez por red nueva (obligatorio):** obtén el esquema de entrada del Actor (API `/v2/acts/<id>` → build → `inputSchema`, o Apify MCP `fetch-actor-details`), arma `config.apify.<red>.input` solo con campos que existan, haz una corrida pequeña, mira un ítem real y escribe `config.mapeo.<red>` con las rutas exactas. Nunca adivines nombres de campos.

### 2. Rankings
```bash
python scripts/score.py $S $INI $FIN [semanas/<semana_anterior>/snapshot.json]
```
`ranking.json` trae:
- `top10`: **Top 10 general** (todas las redes; puntaje mixto; sin música ni actualidad; tope `max_por_red`; cupo PT).
- `por_red`: **Top 10 de cada red por vistas** (YouTube, TikTok, Instagram, Kwai, X). Siempre 10 si hay datos: sin mínimo de vistas. Si faltan publicaciones nuevas, se completa con contenido **en circulación** (`en_circulacion: true`), por `views_semana` cuando hay snapshot anterior o por vistas totales la primera semana. Dilo así en el programa.
- `categorias.revelacion` (cuentas con ≤ `revelacion_max_seguidores` y mayor vistas/seguidores) y `categorias.explosion` (más vistas por hora entre publicación y medición real; con historial, mayor % de crecimiento semanal): así entran los **nuevos** y los que **explotan**.
- `categorias.musica` (videoclips, YouTube categoría 10), `categorias.actualidad` (noticias y política por `palabras_actualidad`), `categorias.rescates` (lo llena la revisión: canales que resuben archivo, p. ej. humor clásico).

**Historial = conteo vivo:** guarda cada `snapshot.json`. Con el de la semana anterior se mide cuánto creció cada publicación en 7 días (`views_semana`).

Muestra al usuario el general y los de cada red con descartes por motivo. **Revisión humana**: puede mover un puesto a otra categoría, corregir país/idioma o vetar. Re-ejecuta tras cambios en `config`. La fórmula es pública y se explica en el programa.

Si las métricas no se tomaron en el corte exacto (p. ej. lanzamiento), dilo en el programa con la fecha real de medición (`medido_at`).

### 2b. Exportar a la app del conductor
```bash
python scripts/export_app.py $S     # -> $S/videos_app.json (formato VideoMetric de la app React ViralTop10 LATAM)
```
Cada video trae `listas` (p. ej. `general#1`, `tiktok#3`, `revelacion#2`). La app lo carga con el botón "Importar ranking de Claude" (`ImportClaudeRanking.tsx`). Pendiente de confirmar con el usuario: ids de `CATEGORIES` (data/countries.ts) y unidad de `engagementRate` (types.ts); hoy va en %.

### 3. Enriquecimiento (Claude)
Para cada ganador, guarda en `ranking.json` → `top10[i].enriquecimiento`:
- `comentarios_destacados`: resumen de 2–3 comentarios reales. Sin datos personales.
- `historia`: 2–3 frases del creador (trayectoria, país) **con fuente**; sin fuente verificable, solo lo que muestra su perfil público.
- `por_que_gano`: lectura de los datos (velocidad, comentarios, engagement).

### 4. Libreto del en vivo y guion de apoyo
En vivo: por cada puesto, 3 datos para decir, historia con fuente, mejor comentario, transición y una pregunta para el chat (ES y PT). Estructura: Top 10 general como columna + Top 3 por red + categorías (Revelación, Explosión, Música, Actualidad, Rescates).

Video de apoyo (Shorts, repetición, versión PT): `proyectos/<AAAA-MM-DD domingo>-<lang>-top10/` con `guion.json` y una copia de `ranking.json`. Escaleta (12–18 min): `apertura` (capítulo) → `reglas` (capítulo) → `p10`…`p04` (`"puesto": N`, capítulo en p10) → `brasil` (opcional) → `p03`…`p01` (capítulos en p03 y p01) → `cierre` (capítulo).

Esquema:
```json
{"lang": "es", "tipo": "top10", "semana": "2026-W42", "color_marca": [255, 45, 120], "contenido_sintetico": true,
 "miniatura": {"linea1": "<creador #1>", "linea2": "es #1", "etiqueta": "SEMANA 42"},
 "seo": {"titulo": "...", "descripcion": "...", "tags": ["top 10 redes sociales", "..."], "hashtags": ["Top10RedesSociales"],
         "categoria_id": "24", "privacidad": "private", "publicar_en": "2026-10-25T21:00:00Z"},
 "escenas": [{"id": "apertura", "capitulo": "Apertura", "texto": "...", "tarjeta": {"titulo": "...", "sub": "..."}},
             {"id": "p10", "puesto": 10, "capitulo": "Puesto 10", "texto": "..."}]}
```
- Cifras en el `texto`: en palabras y redondeadas desde `ranking.json`; `validate_top10.py` avisa si ve cifras.
- No uses `texto_pantalla` en escenas con `puesto`: la ficha ya trae los datos.
- SEO: título 60–70 caracteres con "Top 10" al inicio y el nombre del #1; descripción con lista 10→1 (creador + enlace al original), Top 10 de cada red, fórmula, hashtag. PT: `Top 10 Redes Sociais`.

**Revisión humana** antes de sintetizar voz: resumen con título, gancho, Top 10 y miniatura.

### 5. Producir
```bash
python scripts/pipeline_top10.py proyectos/<proy> --voz-gratis        # voz gratis (edge-tts) + render local
python scripts/pipeline_top10.py proyectos/<proy> --mock --borrador   # prueba sin voz
python scripts/pipeline_top10.py proyectos/<proy>                     # con ElevenLabs
python scripts/pipeline_top10.py proyectos/<proy> --voz-gratis --subir  # + subida privada/programada
```
`cards.py` genera la ficha de cada puesto y las tarjetas con las cifras de `ranking.json`, y `miniatura_base.jpg`. Una imagen propia en `imagenes/<id>.jpg` (p. ej. captura **con permiso escrito** del creador) se respeta.

**Voz sin costo:** `tts_gratis.py` usa edge-tts (voces de Edge: es-PE-AlexNeural/CamilaNeural, es-MX-JorgeNeural/DaliaNeural, pt-BR-AntonioNeural/FranciscaNeural). Servicio no oficial: si falla, Piper (local, open source).

**Idioma PT:** un solo canal. Renderiza el proyecto PT, extrae su audio (`ffmpeg -i video.mp4 -vn -c:a aac pt.m4a`) y agrégalo como pista de audio PT al video ES desde la sección de idiomas del video en YouTube Studio.

### 6. Verificar antes de entregar
- 4 fotogramas: apertura, una ficha, el #1 y el cierre; mira la miniatura.
- Cada cifra en pantalla = `ranking.json`.
- Avisos de `metadata.py` (capítulos ≥10 s) y duración con `ffprobe`.

### 7. Entregar
`videos_app.json`, libreto, y si aplica video, miniatura, `metadata.json` (o el enlace de `publicado.json`). Una línea: título, duración, estado y fecha de estreno.

## Derechos y reglas del canal
- Proyectar videos de terceros en vivo puede activar Content ID o reclamos: fragmentos cortos con comentario encima, música silenciada, enlace al original; permiso escrito para el Top 3.
- Nombre y gráficos propios: nunca "Billboard", "Grammy" ni logos de las redes.
- Solo datos públicos del creador. Nada de contactos privados ni domicilio.
- Scraping de Instagram/TikTok/X puede chocar con sus términos: API oficial donde exista y volúmenes bajos.
- Videos con voz IA: `containsSyntheticMedia` = true (ya lo hace `upload.py`).

## Tareas programadas sugeridas (scheduled tasks, CRON_TZ=America/Lima)
| Cron | Tarea |
|---|---|
| `50 23 * * 6` | Paso 1 (+ guardar snapshot y config en Drive) |
| `47 8 * * 0` | Pasos 2, 2b y 3 con el snapshot anterior; deja los rankings en revisión |
| `47 8 * * 2` | Paso 4 (libreto y guiones ES/PT) en revisión |
| `47 19 * * 4` | Entrega del jueves; paso 5 con `--subir` solo si el guion fue aprobado |

En ejecución desatendida nunca publiques en público: privado + `publicar_en`.

## Scripts
`config/config.json` (verificado con datos reales; ajustable por el usuario; actualiza las fechas de X cada semana):
```json
{
  "zona_horaria": "America/Lima",
  "corte": {"dia": "sabado", "hora": "23:50"},
  "entrega": {"dia": "jueves", "hora": "23:59"},
  "estreno": {"dia": "domingo", "hora": "16:00", "formato": "en vivo con la app del conductor"},
  "pesos": {"views": 0.3, "comments": 0.25, "er": 0.25, "velocity": 0.1, "shares": 0.1},
  "min_views": {"youtube": 5000, "tiktok": 20000, "instagram": 5000, "kwai": 10000, "x": 5000},
  "er_max": 0.5,
  "max_por_creador": 1,
  "cupo_min": {"pt": 2},
  "youtube": {"regiones": ["PE", "MX", "CO", "AR", "CL", "BR"], "busquedas": {"es": ["viral", "humor", "receta", "fútbol", "música", "baile", "reto", "bromas"], "pt": ["viral", "humor", "receita", "futebol", "música", "dança", "desafio", "pegadinha"]}, "max_busquedas": 60},
  "apify": {"tiktok_es": {"actor": "clockworks/tiktok-scraper", "input": {"hashtags": ["humor", "recetas", "futbol", "baile"], "resultsPerPage": 25}}, "tiktok_pt": {"actor": "clockworks/tiktok-scraper", "input": {"hashtags": ["humorbrasil", "receitasfaceis", "futebolbrasileiro", "dancabrasil"], "resultsPerPage": 25}}, "instagram": {"actor": "apify/instagram-hashtag-scraper", "input": {"hashtags": ["humor", "recetas", "futbol", "humorbrasil", "receitas", "futebol"], "resultsType": "reels", "resultsLimit": 25}}, "kwai": {"actor": "natanielsantos/kwai-scraper", "input": {"searchTerms": ["viral", "humor", "receitas", "futebol", "novela"], "maxItems": 20, "maxCommentsPerVideo": 0}}, "x_es": {"actor": "apidojo/tweet-scraper", "input": {"searchTerms": ["filter:videos min_faves:2000 lang:es since:2026-10-04 until:2026-10-11"], "sort": "Top", "maxItems": 150}}, "x_pt": {"actor": "apidojo/tweet-scraper", "input": {"searchTerms": ["filter:videos min_faves:2000 lang:pt since:2026-10-04 until:2026-10-11"], "sort": "Top", "maxItems": 150}}},
  "mapeo": {"tiktok": {"post_id": "id", "url": "webVideoUrl", "thumbnail_url": "videoMeta.coverUrl", "title": "text", "description": "text", "published_at": "createTimeISO", "creator_id": "authorMeta.id", "creator_name": "authorMeta.nickName", "channel_name": "authorMeta.name", "followers": "authorMeta.fans", "country": "locationCreated", "language": "textLanguage", "views": "playCount", "likes": "diggCount", "comments": "commentCount", "shares": "shareCount"}, "instagram": {"post_id": "id", "url": "url", "thumbnail_url": "displayUrl", "title": "caption", "description": "caption", "published_at": "timestamp", "creator_id": "ownerId", "creator_name": "ownerFullName", "channel_name": "ownerUsername", "views": "videoPlayCount", "likes": "likesCount", "comments": "commentsCount", "shares": "sharesCount"}, "kwai": {"post_id": "id", "url": "url", "thumbnail_url": "thumb", "title": "caption", "description": "transcript", "published_at": "createTime", "creator_id": "authorMeta.id", "creator_name": "authorMeta.name", "channel_name": "authorMeta.username", "followers": "authorMeta.followersCount", "views": "viewCount", "likes": "likeCount", "comments": "commentCount", "shares": "shareCount"}, "x": {"post_id": "id", "url": "url", "title": "fullText", "description": "fullText", "published_at": "createdAt", "creator_id": "author.id", "creator_name": "author.name", "channel_name": "author.userName", "followers": "author.followers", "language": "lang", "views": "viewCount", "likes": "likeCount", "comments": "replyCount", "shares": "retweetCount", "ubicacion": "author.location"}},
  "idiomas": ["es", "pt"],
  "paises": ["AR", "BO", "BR", "CL", "CO", "CR", "CU", "DO", "EC", "SV", "GT", "HN", "MX", "NI", "PA", "PY", "PE", "PR", "UY", "VE"],
  "max_por_red": 6,
  "peso_alcance_global": 0.5,
  "palabras_actualidad": ["derecha", "izquierda", "presidente", "presidenta", "elección", "elecciones", "votar", "votando", "gobierno", "congreso", "partido", "eleição", "eleições", "governo", "lula", "bolsonaro", "petro", "milei", "sheinbaum", "política", "politica", "deputado", "senador", "noticia", "noticias", "notícia", "urgente", "directo", "ao vivo", "marcha", "protesta", "protesto"],
  "revelacion_max_seguidores": 100000,
  "revelacion_min_vistas": 50000
}
```

#### `scripts/common.py`
```python
"""Utilidades compartidas del pipeline."""
import json
import os
import subprocess
import sys
from pathlib import Path

W, H, FPS = 1920, 1080, 30

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
FONT_REG_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def font_path(bold=True, skill_dir=None):
    """Prefiere fuentes de assets/fonts; si no, del sistema."""
    if skill_dir:
        name = "Bold" if bold else "Regular"
        for ext in ("ttf", "otf"):
            for p in sorted((Path(skill_dir) / "assets" / "fonts").glob(f"*{name}*.{ext}")):
                return str(p)
    for p in (FONT_CANDIDATES if bold else FONT_REG_CANDIDATES):
        if os.path.exists(p):
            return p
    sys.exit("No se encontró una fuente TTF/OTF. Coloca una en assets/fonts/.")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit(f"Falló: {' '.join(map(str, cmd[:6]))} ...")
    return r.stdout


def duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def ts(sec, srt=False):
    ms = int(round(sec * 1000))
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if srt:
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
```

#### `scripts/extract_youtube.py`
```python
"""Extrae videos de YouTube publicados en la ventana (API oficial). Escribe <semana>/raw/youtube.json ya normalizado.
Uso: python extract_youtube.py <semana_dir> <inicio_iso_utc> <corte_iso_utc>
Requiere YOUTUBE_API_KEY. Respeta config.youtube.max_busquedas (search.list tiene cupo diario propio).
"""
import json, os, sys, requests
from pathlib import Path
API = "https://www.googleapis.com/youtube/v3/"
cfg = json.loads((Path(__file__).parent.parent / "config" / "config.json").read_text())

def get(ep, **p):
    p["key"] = os.environ.get("YOUTUBE_API_KEY") or sys.exit("Falta YOUTUBE_API_KEY.")
    r = requests.get(API + ep, params=p, timeout=60); r.raise_for_status(); return r.json()

def main():
    sem, ini, fin = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    yc = cfg["youtube"]; ids = {}; n = 0
    for lang, qs in yc["busquedas"].items():
        regs = [r for r in yc["regiones"] if (r == "BR") == (lang == "pt")]
        for reg in regs:
            for q in qs:
                if n >= yc["max_busquedas"]: break
                d = get("search", part="snippet", type="video", q=q, regionCode=reg, relevanceLanguage=lang,
                        publishedAfter=ini, publishedBefore=fin, order="viewCount", maxResults=50); n += 1
                for it in d.get("items", []): ids.setdefault(it["id"]["videoId"], (reg, lang))
    vids = list(ids); out = []; chans = {}
    for i in range(0, len(vids), 50):
        for v in get("videos", part="snippet,statistics", id=",".join(vids[i:i+50]))["items"]:
            s, st = v["snippet"], v.get("statistics", {})
            out.append({"platform": "youtube", "post_id": v["id"], "url": f"https://youtu.be/{v['id']}",
                "thumbnail_url": s.get("thumbnails", {}).get("high", {}).get("url"), "title": s.get("title"),
                "description": s.get("description", "")[:1000], "published_at": s["publishedAt"],
                "creator_id": s["channelId"], "creator_name": s["channelTitle"], "channel_name": s["channelTitle"],
                "language": (s.get("defaultAudioLanguage") or s.get("defaultLanguage") or "")[:2] or None, "country": None,
                "category_id": s.get("categoryId"),
                "region_busqueda": ids[v["id"]][0],
                "views": int(st["viewCount"]) if "viewCount" in st else None,
                "likes": int(st["likeCount"]) if "likeCount" in st else None,
                "comments": int(st["commentCount"]) if "commentCount" in st else None, "shares": None})
            chans[s["channelId"]] = None
    cl = list(chans)
    for i in range(0, len(cl), 50):
        for c in get("channels", part="snippet,statistics", id=",".join(cl[i:i+50]))["items"]:
            chans[c["id"]] = (c["snippet"].get("country"), c["statistics"].get("subscriberCount"))
    for o in out:
        ctry, subs = chans.get(o["creator_id"]) or (None, None)
        o["country"] = ctry; o["followers"] = int(subs) if subs else None
    (sem / "raw").mkdir(parents=True, exist_ok=True)
    (sem / "raw" / "youtube.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"OK youtube: {len(out)} videos, {n} búsquedas")

if __name__ == "__main__": main()
```

#### `scripts/extract_apify.py`
```python
"""Ejecuta los Actors de Apify configurados y guarda los ítems crudos. Escribe <semana>/raw/<plataforma>.raw.json
Uso: python extract_apify.py <semana_dir> [plataforma ...] [--run <plataforma>=<runId> ...]
Requiere APIFY_TOKEN. config.apify = {"tiktok_es": {"actor": "clockworks/tiktok-scraper", "input": {...}}, ...}
El input de cada Actor se copia de su esquema verificado (nunca se inventan campos).
"""
import json, os, sys, time, requests
from pathlib import Path
B = "https://api.apify.com/v2/"
cfg = json.loads((Path(__file__).parent.parent / "config" / "config.json").read_text())

def req(method, url, **kw):  # reintenta cortes de red sin duplicar corridas
    for i in range(6):
        try:
            r = requests.request(method, url, timeout=kw.pop("timeout", 60), **kw); r.raise_for_status(); return r
        except requests.exceptions.ConnectionError:
            if method == "POST" or i == 5: raise
            time.sleep(10 * (i + 1))

def main():
    sem = Path(sys.argv[1]); tok = os.environ.get("APIFY_TOKEN") or sys.exit("Falta APIFY_TOKEN.")
    H = {"Authorization": f"Bearer {tok}"}
    plats = [x for x in sys.argv[2:sys.argv.index("--run") if "--run" in sys.argv else None]] or list(cfg["apify"])
    (sem / "raw").mkdir(parents=True, exist_ok=True)
    for p in plats:
        a = cfg["apify"][p]
        if "--run" in sys.argv:  # retomar una corrida ya lanzada: --run <plataforma>=<runId>
            prev = dict(x.split("=") for x in sys.argv[sys.argv.index("--run") + 1:])
            if p in prev:
                run = req("GET", B + f"actor-runs/{prev[p]}", headers=H).json()["data"]
                while run["status"] in ("READY", "RUNNING"):
                    time.sleep(15); run = req("GET", B + f"actor-runs/{run['id']}", headers=H).json()["data"]
                items = req("GET", B + f"datasets/{run['defaultDatasetId']}/items", headers=H, params={"clean": "true"}, timeout=300).json()
                (sem / "raw" / f"{p}.raw.json").write_text(json.dumps(items, ensure_ascii=False)); print(f"OK {p}: {len(items)} ítems (retomado)"); continue
        run = requests.post(B + f"acts/{a['actor'].replace('/', '~')}/runs", headers=H, json=a["input"], timeout=60)
        run.raise_for_status(); run = run.json()["data"]
        while run["status"] in ("READY", "RUNNING"):
            time.sleep(15); run = req("GET", B + f"actor-runs/{run['id']}", headers=H).json()["data"]
        if run["status"] != "SUCCEEDED": sys.exit(f"{p}: run {run['id']} terminó en {run['status']}")
        items = req("GET", B + f"datasets/{run['defaultDatasetId']}/items", headers=H, params={"clean": "true"}, timeout=300).json()
        (sem / "raw" / f"{p}.raw.json").write_text(json.dumps(items, ensure_ascii=False))
        print(f"OK {p}: {len(items)} ítems (run {run['id']})")

if __name__ == "__main__": main()
```

#### `scripts/normalize.py`
```python
"""Une todas las fuentes en <semana>/snapshot.json con el modelo unificado.
Uso: python normalize.py <semana_dir> <corte_iso_utc>
raw/youtube.json ya viene normalizado. raw/<p>[_sufijo].raw.json se mapea con config.mapeo[<p>].
Rutas con puntos; un campo sin ruta queda null. El mapeo se verifica con un ítem real antes de usarlo.
"""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
cfg = json.loads((Path(__file__).parent.parent / "config" / "config.json").read_text())
LUGARES = {"AR": ["argentina", "buenos aires"], "BO": ["bolivia"], "BR": ["brasil", "brazil", "são paulo", "sao paulo", "rio de janeiro"], "CL": ["chile", "santiago"],
           "CO": ["colombia", "bogotá", "bogota", "medellín", "medellin"], "MX": ["méxico", "mexico", "cdmx", "monterrey", "guadalajara"], "PE": ["perú", "peru", "lima"],
           "VE": ["venezuela", "caracas"], "EC": ["ecuador", "quito", "guayaquil"], "UY": ["uruguay", "montevideo"], "PY": ["paraguay"], "ES": ["españa", "spain", "madrid", "barcelona"],
           "US": ["usa", "estados unidos", "miami", "new york", "los angeles"], "PT": ["portugal", "lisboa"]}

def pais_de(texto):  # país a partir de la ubicación libre del perfil (X); None si no es claro
    t = (texto or "").lower()
    hits = [c for c, ws in LUGARES.items() if any(w in t for w in ws)]
    return hits[0] if len(hits) == 1 else None

CAMPOS = ["post_id", "url", "thumbnail_url", "title", "description", "published_at", "creator_id", "creator_name",
          "channel_name", "followers", "country", "language", "views", "likes", "comments", "shares"]
NUM = {"views", "likes", "comments", "shares", "followers"}

def pick(o, path):
    for k in path.split("."):
        if isinstance(o, list): o = o[int(k)] if k.isdigit() and int(k) < len(o) else None
        elif isinstance(o, dict): o = o.get(k)
        else: return None
    return o

PT = {"não", "você", "é", "isso", "muito", "uma", "também", "mais", "pra", "meu", "minha", "ele", "ela", "nós", "está", "são", "do", "da", "dos", "das", "no", "na", "com", "bom", "quando", "ainda", "até", "aqui", "agora", "gente", "receita", "futebol"}
ES = {"el", "los", "las", "del", "muy", "pero", "también", "una", "es", "está", "son", "yo", "tu", "mi", "con", "cuando", "aquí", "ahora", "hoy", "gente", "receta", "fútbol", "qué", "porque", "nada", "todo", "ya"}

def lang_of(t):  # idioma por palabras frecuentes cuando la red no lo da (solo es/pt; si no es claro, None)
    import re
    w = re.findall(r"[a-záéíóúâêôãõçñü]+", re.sub(r"[#@]\\w+|https?://\\S+", " ", (t or "").lower()))
    pt = sum(x in PT for x in w) + 2 * sum(("ã" in x or "õ" in x or "ç" in x) for x in w)
    es = sum(x in ES for x in w) + 2 * sum("ñ" in x for x in w)
    if max(pt, es) < 2 or pt == es: return None
    return "pt" if pt > es else "es"

def iso(v):
    if v is None: return None
    if isinstance(v, str) and v[:3].isalpha() and v[3] == " ":  # formato X: "Fri Oct 09 23:09:34 +0000 2026"
        return datetime.strptime(v, "%a %b %d %H:%M:%S %z %Y").astimezone(timezone.utc).isoformat()
    if isinstance(v, (int, float)): return datetime.fromtimestamp(v / 1000 if v > 1e12 else v, timezone.utc).isoformat()
    return datetime.fromisoformat(str(v).replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()

def main():
    sem, corte = Path(sys.argv[1]), sys.argv[2]; rows = []
    yt = sem / "raw" / "youtube.json"
    if yt.exists(): rows += json.loads(yt.read_text())
    for f in sorted((sem / "raw").glob("*.raw.json")):
        p = f.name.split(".")[0].split("_")[0]  # tiktok_es -> tiktok
        m = cfg["mapeo"].get(p) or sys.exit(f"Falta config.mapeo.{p}")
        for it in json.loads(f.read_text()):
            r = {"platform": p}
            for c in CAMPOS:
                v = pick(it, m[c]) if m.get(c) else None
                if c in NUM and v is not None:
                    try: v = int(float(v))
                    except (TypeError, ValueError): v = None
                r[c] = v
            r["published_at"] = iso(r["published_at"])
            if m.get("ubicacion") and not r.get("country"): r["country"] = pais_de(pick(it, m["ubicacion"]))
            if not r.get("language"): r["language"] = lang_of(f"{r.get('title') or ''} {r.get('description') or ''}"); r["language_detectado"] = True
            if r["post_id"] and r["published_at"]: rows.append(r)
    medido = datetime.fromtimestamp(min(f.stat().st_mtime for f in (sem / "raw").glob("*.json")), timezone.utc).isoformat()  # hora real de la medición
    for r in rows:
        r["published_at"] = iso(r["published_at"]); r["snapshot_at"] = corte; r["medido_at"] = medido
        if not r.get("language"): r["language"] = lang_of(f"{r.get('title') or ''} {r.get('description') or ''}"); r["language_detectado"] = True
        if r.get("country") in cfg.get("paises", []):  # país LATAM conocido manda: BR -> pt, resto -> es
            r["language"] = "pt" if r["country"] == "BR" else "es"
        r["key"] = f"{r['platform']}:{r['post_id']}"
    seen = {}; [seen.setdefault(r["key"], r) for r in rows]
    (sem / "snapshot.json").write_text(json.dumps(list(seen.values()), ensure_ascii=False, indent=1))
    print(f"OK snapshot: {len(seen)} publicaciones")

if __name__ == "__main__": main()
```

#### `scripts/score.py`
```python
"""Rankings semanales. Uso: python score.py <semana_dir> <inicio_iso_utc> <corte_iso_utc> [<snapshot_semana_anterior.json>]
Escribe ranking.json con:
  top10        -> Top 10 general (todas las redes)
  por_red      -> Top 10 de cada red por vistas (siempre 10 si hay datos; sin mínimo de vistas)
  categorias   -> musica, actualidad (noticias/política), rescates (lo marca la revisión),
                  revelacion (cuentas chicas con alcance enorme), explosion (crecimiento más rápido)
Puntaje = (1-G) x percentil dentro de su red + G x percentil de alcance global (vistas y comentarios).
Si hay snapshot anterior, 'views_semana' = vistas ganadas en la semana.
"""
import json, sys
from datetime import datetime
from pathlib import Path
cfg = json.loads((Path(__file__).parent.parent / "config" / "config.json").read_text())
T = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))

def pct(vals, v):
    lo = sum(x < v for x in vals); eq = sum(x == v for x in vals)
    return 100 * (lo + 0.5 * eq) / len(vals)

def norm(s): return "".join(ch for ch in (s or "").lower() if ch.isalnum())

def puntuar(rows, W, G):
    for p in {r["platform"] for r in rows}:
        g = [r for r in rows if r["platform"] == p]
        for m in W:
            vals = [r[m] for r in g if r.get(m) is not None]
            for r in g: r.setdefault("p", {})[m] = round(pct(vals, r[m]), 1) if vals and r.get(m) is not None else None
    gv = [r["views"] for r in rows if r.get("views") is not None]; gc = [r["comments"] for r in rows if r.get("comments") is not None]
    for r in rows:
        av = {m: w for m, w in W.items() if r["p"][m] is not None}; tot = sum(av.values())
        red = sum(w * r["p"][m] for m, w in av.items()) / tot if tot else 0
        glob = ([pct(gv, r["views"])] if r.get("views") is not None and gv else []) + ([pct(gc, r["comments"])] if r.get("comments") is not None and gc else [])
        r["score_red"] = round(red, 2)
        r["score"] = round((1 - G) * red + G * (sum(glob) / len(glob) if glob else red), 2)

def unicos(rows, key, n, cap=None):
    out, seen = [], set()
    for r in sorted(rows, key=key):
        c = norm(r.get("creator_name") or r.get("creator_id"))
        if c in seen: continue
        if cap and sum(x["platform"] == r["platform"] for x in out) >= cap: continue
        seen.add(c); out.append(dict(r))
        if len(out) == n: break
    for i, r in enumerate(out): r["rank"] = i + 1
    return out

def main():
    sem, ini, fin = Path(sys.argv[1]), T(sys.argv[2]), T(sys.argv[3])
    rows = json.loads((sem / "snapshot.json").read_text())
    prev = {r["key"]: r for r in json.loads(Path(sys.argv[4]).read_text())} if len(sys.argv) > 4 else {}
    base, motivos = [], {}
    for r in rows:
        f = []
        if (r.get("language") or "")[:2] not in cfg["idiomas"]: f.append("fuera_de_idioma")
        if r.get("country") and r["country"] not in cfg["paises"]: f.append("fuera_de_region")
        if (r.get("views") or 0) <= 0: f.append("sin_vistas")
        inter = sum(r.get(k) or 0 for k in ("likes", "comments", "shares"))
        r["er"] = round(inter / r["views"], 4) if r.get("views") else None
        if r["er"] is not None and r["er"] > cfg["er_max"]: f.append("er_anomalo")
        pub = T(r["published_at"]); r["en_ventana"] = ini <= pub <= fin
        med = T(r.get("medido_at") or sys.argv[3])  # vistas por hora entre publicación y medición real
        r["velocity"] = round(r["views"] / max(1, (med - pub).total_seconds() / 3600), 2) if r.get("views") else None
        if r["key"] in prev and r.get("views") is not None and prev[r["key"]].get("views") is not None:
            r["views_semana"] = max(0, r["views"] - prev[r["key"]]["views"])
        txt = f" {(r.get('title') or '')} {(r.get('description') or '')} ".lower()
        r["actualidad"] = any(f" {w} " in txt or f"#{w}" in txt for w in cfg.get("palabras_actualidad", []))
        r["musica"] = r["platform"] == "youtube" and r.get("category_id") == "10"
        for x in f: motivos[x] = motivos.get(x, 0) + 1
        if not f: base.append(r)
    W, G = cfg["pesos"], cfg.get("peso_alcance_global", 0.5)
    vent = [r for r in base if r["en_ventana"]]
    puntuar(vent, W, G)
    gen_pool = [r for r in vent if not r["musica"] and not r["actualidad"] and (r.get("views") or 0) >= cfg["min_views"].get(r["platform"], 0)]
    general = unicos(gen_pool, lambda r: -r["score"], 10, cfg.get("max_por_red"))
    for lang, n in cfg.get("cupo_min", {}).items():  # cupo por idioma en el general
        falta = n - sum(r.get("language") == lang for r in general)
        cand = [r for r in unicos(gen_pool, lambda r: -r["score"], 40) if r.get("language") == lang and norm(r["creator_name"]) not in {norm(x["creator_name"]) for x in general}]
        while falta > 0 and cand:
            out = next((r for r in reversed(general) if r.get("language") != lang), None)
            if not out: break
            general.remove(out); general.append(cand.pop(0)); general.sort(key=lambda r: -r["score"]); falta -= 1
        for i, r in enumerate(general): r["rank"] = i + 1
    por_red = {}
    for p in sorted({r["platform"] for r in base}):
        ven = [r for r in vent if r["platform"] == p]
        lista = unicos(ven, lambda r: (-(r.get("views") or 0), -(r.get("comments") or 0)), 10)  # por red: más vistas
        if len(lista) < 10:  # completar con contenido en circulación
            usados = {norm(x["creator_name"]) for x in lista}
            circ = [r for r in base if r["platform"] == p and not r["en_ventana"] and norm(r["creator_name"]) not in usados]
            k = (lambda r: -(r.get("views_semana") or 0)) if prev else (lambda r: -(r.get("views") or 0))
            extra = unicos(circ, k, 10 - len(lista))
            for r in extra: r["en_circulacion"] = True
            lista += extra
            for i, r in enumerate(lista): r["rank"] = i + 1
        por_red[p] = lista
    categorias = {"musica": unicos([r for r in vent if r["musica"]], lambda r: -r["score"], 10),
                  "actualidad": unicos([r for r in vent if r["actualidad"]], lambda r: -r["score"], 10),
                  "rescates": [],
                  "revelacion": unicos([r for r in vent if r.get("followers") and r["followers"] <= cfg.get("revelacion_max_seguidores", 100000)
                                        and (r.get("views") or 0) >= cfg.get("revelacion_min_vistas", 50000)],
                                       lambda r: -(r["views"] / max(r["followers"], 1)), 10),
                  "explosion": unicos([r for r in base if (r["en_ventana"] or r.get("views_semana")) and (r.get("views") or 0) >= cfg.get("revelacion_min_vistas", 50000)],
                                      (lambda r: -((r.get("views_semana") or 0) / max((r.get("views") or 1) - (r.get("views_semana") or 0), 1)) if r.get("views_semana") is not None else -(r.get("velocity") or 0)), 10)}
    json.dump({"semana": sem.name, "inicio": sys.argv[2], "corte": sys.argv[3], "pesos": W, "alcance_global": G,
               "con_historial": bool(prev), "top10": general, "por_red": por_red, "categorias": categorias,
               "descartes": motivos, "elegibles": {p: sum(r["platform"] == p for r in vent) for p in por_red}},
              open(sem / "ranking.json", "w"), ensure_ascii=False, indent=1)
    print("GENERAL"); [print(f" #{r['rank']:>2} {r['score']:5.1f} {r['platform']:<9} {r.get('language')} {r['creator_name'][:28]}") for r in general]
    for p, l in por_red.items():
        print(p.upper()); [print(f" #{r['rank']:>2} {r.get('views') or 0:>12,} {'(circ)' if r.get('en_circulacion') else '      '} {r['creator_name'][:28]}") for r in l]

if __name__ == "__main__": main()
```

#### `scripts/export_app.py`
```python
"""Convierte ranking.json al formato VideoMetric de la app ViralTop10 LATAM (React).
Uso: python export_app.py <semana_dir>  -> <semana_dir>/videos_app.json
Campos confirmados en App.tsx: id, title, creator, category, categoryLabel, platform, country, views, likes,
comments, engagementRate, viralScore, url. El resto va como extra (la app los ignora si no los usa).
PENDIENTE: alinear 'category' con los ids de CATEGORIES (data/countries.ts) y la unidad de engagementRate (types.ts).
"""
import json, sys
from pathlib import Path
CAT = {"musica": "Música", "actualidad": "Actualidad", "rescates": "Rescates", "revelacion": "Revelación", "explosion": "Explosión"}

def main():
    sem = Path(sys.argv[1]); d = json.loads((sem / "ranking.json").read_text()); out = {}
    def add(r, lista, cat=None):
        k = r["key"]
        v = out.setdefault(k, {
            "id": f"claude-{r['platform']}-{r['post_id']}", "title": (r.get("title") or "").strip()[:200],
            "creator": r.get("creator_name") or r.get("channel_name") or "", "platform": r["platform"],
            "country": r.get("country") or "LATAM", "views": r.get("views") or 0, "likes": r.get("likes") or 0,
            "comments": r.get("comments") or 0, "shares": r.get("shares") or 0,
            "engagementRate": round((r.get("er") or 0) * 100, 2),  # en %
            "viralScore": round(r.get("score") or r.get("score_red") or 0, 1),
            "category": cat or "general", "categoryLabel": CAT.get(cat, "General"),
            "url": r["url"], "thumbnail": r.get("thumbnail_url"), "publishedAt": r.get("published_at"),
            "followers": r.get("followers"), "language": r.get("language"), "week": d["semana"],
            "enCirculacion": bool(r.get("en_circulacion")), "listas": [], "fuente": "claude"})
        v["listas"].append(lista)
    for r in d["top10"]: add(r, f"general#{r['rank']}")
    for p, l in d["por_red"].items():
        for r in l: add(r, f"{p}#{r['rank']}")
    for c, l in d["categorias"].items():
        for r in l: add(r, f"{c}#{r['rank']}", c)
    (sem / "videos_app.json").write_text(json.dumps(list(out.values()), ensure_ascii=False, indent=1))
    print(f"OK videos_app.json: {len(out)} videos")

if __name__ == "__main__": main()
```

#### `scripts/cards.py`
```python
"""Tarjetas visuales por escena (2880x1620) + miniatura_base.jpg, con cifras leídas de ranking.json (nunca del guion).
Uso: python cards.py <proyecto_dir>
Escena con "puesto": N -> ficha del ganador N. Sin puesto -> tarjeta con "tarjeta": {"titulo", "sub"}.
Respeta imagenes/<id>.jpg ya existentes (p. ej. una captura con permiso del creador).
"""
import html, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
SK = Path(__file__).resolve().parent.parent
RED = {"youtube": "YouTube", "tiktok": "TikTok", "instagram": "Instagram", "kwai": "Kwai", "x": "X"}
TXT = {"es": {"v": "vistas", "c": "comentarios", "e": "engagement", "s": "puntaje"},
       "pt": {"v": "visualizações", "c": "comentários", "e": "engajamento", "s": "pontuação"}}

def num(n, lang):
    if n is None: return "—"
    for d, s in ((1e9, " mil M" if lang == "es" else " bi"), (1e6, " M" if lang == "es" else " mi"), (1e3, " mil")):
        if n >= d: return f"{n / d:.1f}".rstrip("0").rstrip(".").replace(".", ",") + s
    return str(n)

CSS = """*{margin:0;box-sizing:border-box}body{width:2880px;height:1620px;overflow:hidden;font-family:'Inter Display',Inter,sans-serif;color:#fff;
background:radial-gradient(ellipse 1300px 800px at 25% 45%,rgba(255,45,120,.30),transparent 70%),radial-gradient(ellipse 1300px 800px at 78% 55%,rgba(34,211,255,.22),transparent 70%),
radial-gradient(ellipse 2000px 1100px at 50% 50%,#22103A,#0E0820 55%,#07050F)}
.g{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.05) 2px,transparent 2px),linear-gradient(90deg,rgba(255,255,255,.05) 2px,transparent 2px);background-size:90px 90px;-webkit-mask-image:radial-gradient(ellipse 1400px 700px at 50% 45%,#000 20%,transparent 75%)}
.hot{background:linear-gradient(90deg,#FF2D78,#FF6A2B 55%,#FFC21A);-webkit-background-clip:text;color:transparent}
.cool{background:linear-gradient(90deg,#7B5CFF,#22D3FF);-webkit-background-clip:text;color:transparent}
.w{position:absolute;left:330px;right:330px;top:260px;height:900px;display:flex;align-items:center;gap:110px}
.rk{font-weight:900;font-size:560px;line-height:1;letter-spacing:-10px;padding:0 30px}
.inf{display:flex;flex-direction:column;gap:34px;min-width:0}
.ch{display:flex;gap:20px}.c{font-weight:800;font-size:44px;padding:14px 34px;border-radius:999px;border:3px solid rgba(255,255,255,.2);background:rgba(255,255,255,.06)}
.n{font-weight:900;font-size:130px;line-height:1;letter-spacing:-2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.t{font-weight:600;font-size:52px;color:#C9C2EE;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.ms{display:flex;gap:30px;margin-top:10px}.m{padding:26px 40px;border-radius:30px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.14)}
.m b{display:block;font-size:80px;font-weight:900;white-space:nowrap}.m span{font-size:36px;color:#A79FD6;font-weight:600}
.ct{position:absolute;left:330px;right:330px;top:260px;height:900px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:40px}
.h{font-weight:900;font-size:190px;line-height:1;letter-spacing:-4px}.s{font-weight:600;font-size:70px;color:#C9C2EE}"""

def page(body): return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='g'></div>{body}</body></html>"
E = lambda s: html.escape(str(s or ""))

def ficha(r, lang):
    t = TXT[lang]; cl = "hot" if r["rank"] % 2 else "cool"
    chips = [RED.get(r["platform"], r["platform"]), r.get("country"), (r.get("language") or "").upper()]
    return page(f"""<div class='w'><div class='rk {cl}'>#{r['rank']}</div><div class='inf'>
<div class='ch'>{''.join(f"<div class='c'>{E(c)}</div>" for c in chips if c)}</div>
<div class='n'>{E(r.get('creator_name'))}</div><div class='t'>{E(r.get('title'))}</div>
<div class='ms'><div class='m'><b class='hot'>{num(r.get('views'), lang)}</b><span>{t['v']}</span></div>
<div class='m'><b class='cool'>{num(r.get('comments'), lang)}</b><span>{t['c']}</span></div>
<div class='m'><b class='hot'>{f"{(r.get('er') or 0) * 100:.1f}".replace('.', ',')}%</b><span>{t['e']}</span></div>
<div class='m'><b>{r['score']:.0f}</b><span>{t['s']}</span></div></div></div></div>""")

def tarjeta(tj): return page(f"<div class='ct'><div class='h'>{E(tj.get('titulo'))}</div><div class='s'>{E(tj.get('sub'))}</div></div>")

def main():
    proj = Path(sys.argv[1]); g = json.loads((proj / "guion.json").read_text())
    rk = {r["rank"]: r for r in json.loads((proj / "ranking.json").read_text())["top10"]}
    (proj / "imagenes").mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 2880, "height": 1620})
        for e in g["escenas"]:
            dst = proj / "imagenes" / f"{e['id']}.jpg"
            if dst.exists(): print(f"= {e['id']} (ya existe)"); continue
            pg.set_content(ficha(rk[e["puesto"]], g["lang"]) if e.get("puesto") else tarjeta(e.get("tarjeta") or {"titulo": e.get("capitulo", "")}))
            pg.wait_for_timeout(150); pg.screenshot(path=str(dst), type="jpeg", quality=92); print(f"+ {e['id']}")
        pg.set_viewport_size({"width": 1280, "height": 720})
        pg.set_content(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS} body{{width:1280px;height:720px}}</style></head><body>"
                       f"<div style='position:absolute;right:36px;top:170px;text-align:center;width:390px'><div class='hot' style='font-weight:900;font-size:150px;line-height:1;padding:0 10px'>TOP</div>"
                       f"<div class='cool' style='font-weight:900;font-size:260px;line-height:.9;padding:0 10px'>10</div></div></body></html>")
        pg.wait_for_timeout(150); pg.screenshot(path=str(proj / "miniatura_base.jpg"), type="jpeg", quality=92); b.close()
    print("OK tarjetas + miniatura_base.jpg")

if __name__ == "__main__": main()
```

#### `scripts/tts_gratis.py`
```python
"""Narración GRATIS con edge-tts (voces neuronales de Microsoft Edge). Mismo formato que tts.py:
audio/<id>.mp3 + audio/<id>.align.json (tiempos por carácter para subtítulos).
Uso: python tts_gratis.py <proyecto_dir> [--voz es-PE-AlexNeural]
Requiere internet (servicio de lectura en voz alta de Edge) y: pip install edge-tts
Servicio no oficial y sin garantía: si deja de funcionar, usar Piper (local, open source).
"""
import asyncio, json, sys
from pathlib import Path
import edge_tts

VOZ = {"es": "es-PE-AlexNeural", "pt": "pt-BR-AntonioNeural"}

async def una(texto, voz, mp3, align):
    com = edge_tts.Communicate(texto, voz, rate="+5%", boundary="WordBoundary")
    palabras = []
    with open(mp3, "wb") as f:
        async for ch in com.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                palabras.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    chars, st, en = [], [], []
    for i, (w, a, b) in enumerate(palabras):  # reparte el tiempo de cada palabra entre sus letras
        paso = (b - a) / max(len(w), 1)
        for k, c in enumerate(w): chars.append(c); st.append(a + k * paso); en.append(a + (k + 1) * paso)
        if i + 1 < len(palabras): chars.append(" "); st.append(b); en.append(palabras[i + 1][1])
    json.dump({"characters": chars, "character_start_times_seconds": st, "character_end_times_seconds": en},
              open(align, "w", encoding="utf-8"), ensure_ascii=False)

def main():
    proj = Path(sys.argv[1]); g = json.loads((proj / "guion.json").read_text())
    voz = sys.argv[sys.argv.index("--voz") + 1] if "--voz" in sys.argv else VOZ[g["lang"]]
    (proj / "audio").mkdir(exist_ok=True)
    for e in g["escenas"]:
        mp3, al = proj / "audio" / f"{e['id']}.mp3", proj / "audio" / f"{e['id']}.align.json"
        if mp3.exists() and al.exists(): print(f"= {e['id']}"); continue
        asyncio.run(una(e["texto"], voz, mp3, al)); print(f"+ {e['id']} ({voz})")

if __name__ == "__main__": main()
```

#### `scripts/validate_top10.py`
```python
"""Valida guion.json del programa antes de gastar voz. Uso: python validate_top10.py <proyecto_dir>"""
import json, re, sys
from pathlib import Path
RANGO = {"top10": (1800, 2700), "short": (40, 120)}  # ~150 palabras/min: 12-18 min / 15-50 s

def main():
    p = Path(sys.argv[1]); g = json.loads((p / "guion.json").read_text()); err, warn = [], []
    for k in ["lang", "tipo", "semana", "escenas", "seo", "miniatura"]:
        if k not in g: err.append(f"Falta '{k}'.")
    if err: sys.exit("\n".join(err))
    if g["tipo"] not in RANGO: err.append(f"tipo: {', '.join(RANGO)}")
    if g["lang"] not in ("es", "pt"): err.append("lang: es | pt")
    ids = [e.get("id") for e in g["escenas"]]
    if len(set(ids)) != len(ids) or not all(re.fullmatch(r"[a-z0-9_-]+", i or "") for i in ids): err.append("ids únicos a-z0-9_-")
    if g["tipo"] == "top10":
        rk = json.loads((p / "ranking.json").read_text())["top10"]
        puestos = [e["puesto"] for e in g["escenas"] if e.get("puesto")]
        if sorted(puestos) != list(range(1, len(rk) + 1)): err.append(f"Faltan puestos: {sorted(set(range(1, len(rk) + 1)) - set(puestos))}")
        if puestos != sorted(puestos, reverse=True): err.append("Los puestos van en cuenta regresiva (10 → 1).")
        caps = [e for e in g["escenas"] if e.get("capitulo")]
        if not g["escenas"][0].get("capitulo") or len(caps) < 3: err.append("≥3 capítulos y la primera escena con capítulo.")
        for e in g["escenas"]:
            if re.search(r"\d{1,3}([.,]\d{3})+|\d+\s?(mil|millones|milhões|%)", e["texto"]):
                warn.append(f"{e['id']}: el texto tiene cifras; verifica que coincidan con ranking.json o usa palabras.")
    n = sum(len(e["texto"].split()) for e in g["escenas"]); lo, hi = RANGO.get(g["tipo"], (0, 1e9))
    if not lo <= n <= hi: warn.append(f"{n} palabras; esperado {lo}-{hi}.")
    if len(g["seo"].get("titulo", "")) > 100: err.append("seo.titulo > 100")
    if not g["miniatura"].get("linea1"): err.append("miniatura.linea1 vacío")
    for w in warn: print("AVISO:", w)
    if err: sys.exit("ERRORES:\n - " + "\n - ".join(err))
    print(f"OK guion: {len(ids)} escenas, {n} palabras (~{n / 150:.1f} min)")

if __name__ == "__main__": main()
```

#### `scripts/pipeline_top10.py`
```python
"""Uso: python pipeline_top10.py <proyecto_dir> [--voz-gratis | --mock] [--borrador] [--subir]"""
import subprocess, sys
from pathlib import Path
H = Path(__file__).resolve().parent
def step(s, *a):
    print(f"\n== {s} =="); r = subprocess.run([sys.executable, str(H / s), *a])
    if r.returncode: sys.exit(f"Paso {s} falló.")
p, a = sys.argv[1], sys.argv[2:]
step("validate_top10.py", p)
if "--voz-gratis" in a: step("tts_gratis.py", p)  # edge-tts, sin costo
else: step("tts.py", p, *(["--mock"] if "--mock" in a else []))
step("cards.py", p); step("render.py", p, *(["borrador"] if "--borrador" in a else []))
step("thumbnail.py", p); step("metadata.py", p)
if "--subir" in a:
    if "--mock" in a: sys.exit("No se sube un video con audio de prueba.")
    step("upload.py", p)
print(f"\nListo: {Path(p) / 'salida'}")
```