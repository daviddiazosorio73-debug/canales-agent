---
name: "mayordom-youtube"
description: "Produce y publica en el canal YouTube @MayorDom (Mayordomía Bíblica): sermones, análisis martes/jueves, shorts, podcast; voz IA gratis, render, miniatura, SEO y subida."
---

# MayorDom YouTube — producción y publicación de punta a punta

Clon adaptado de `youtube-agent-skill`. Canal: **MayorDom** (@MayorDom, ID `UCxGgMCMbyiCvRo_T-haI_Ug`, Perú). Idioma: español neutro latinoamericano. Todo gratis.

## Fuentes de contenido
- Biblia: la versión de mayor impacto para el tema (RVR1960, NVI, NTV, LBLA, etc.) o combinadas. Cada cita lleva su versión. Texto literal solo si está verificado en una fuente (bibliaparalela.com, biblegateway, o el texto impreso del material oficial); si no, se cita la referencia y se parafrasea.
- Elena G. de White, en especial *Consejos sobre mayordomía cristiana* (edición en español: 15 secciones, 68 capítulos; egwwritings.org es_CMC(CS)). Citas breves, con libro y página, verificadas.
- Material del Fundador en Drive: carpeta `1nSUHFNb5wjCPDuzfHilRuSwZ2M4GiiO1` (Sermonario de la Semana de Mayordomía 2026 «Todo por amor a Él» y libro).
- Material oficial (sermonarios, lecciones): se adapta con redacción original, se acredita en la descripción y no se copia párrafo a párrafo.

## Formatos y calendario (hora de Lima, UTC−5)
| Formato | `tipo` | Cuándo | Duración |
|---|---|---|---|
| Sermón del capítulo de la semana (3 por capítulo) | `sermon` | Lunes, miércoles y viernes | 10–24 min |
| Análisis de otros autores (enriquecer, o corregir y desmentir con fuentes) | `analisis` | Martes y jueves | 10–20 min |
| Shorts / Reels (3 diarios) | `short` | 07:00 · 13:00 · 20:30 | 40–75 s, 9:16 |
| Podcast (audio más portada) | podcast | Según el plan | Libre |
| Eventos (p. ej. Semana de Mayordomía: 1 sermón por noche) | `sermon` | 18:00 | 10–24 min |

Serie principal: un capítulo de *Consejos sobre mayordomía cristiana* por semana (68 semanas). Por capítulo: extracción de conocimiento, análisis, aplicaciones a la vida diaria y reflexiones.

## Estructura del `sermon`
1. Gancho (primeros 15 s), 2. Contexto y pasaje, 3–6. Ideas clave (texto bíblico + explicación + ilustración), 7. Aplicación concreta + compromiso, 8. Preguntas para meditar + oración + invitación a la siguiente publicación. Al menos 3 escenas con `capitulo`. Escribir para el oído: frases de 8 a 20 palabras, segunda persona, referencias escritas como se pronuncian en `texto` y en formato «Lucas 14:33» en `referencia`.

## Estructura del `analisis`
1. Gancho, 2. Qué dice el autor o video analizado (resumen breve, sin reproducirlo), 3. Lo que es correcto y suma, 4. Lo que hay que corregir, con Biblia y EGW verificadas, 5. Conclusión práctica, 6. Pregunta para comentarios. Tono respetuoso: se corrigen ideas, no se ataca a personas.

## Producción (pipeline)
1. Copia los scripts base: `cp -r /mnt/skills/plugins/youtube-agent-skill/scripts <kit>/scripts`.
2. Reemplaza `tts.py` y `validate.py` por las versiones adaptadas guardadas en el Proyecto: `claude/kit/tts.py` y `claude/kit/validate.py` (léelas con la herramienta Projects).
3. Voz IA gratis offline (motor por defecto `TTS_MOTOR=piper`):
   ```bash
   pip install sherpa-onnx soundfile --break-system-packages
   mkdir -p <kit>/voces && cd <kit>/voces
   curl -sL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-es_MX-claude-high.tar.bz2 && tar xjf vits-piper-es_MX-claude-high.tar.bz2
   ```
   Alternativas: `TTS_MOTOR=edge` (requiere red hacia speech.platform.bing.com) o `elevenlabs` (de pago, no por defecto).
4. Imágenes: Pexels si `PEXELS_API_KEY` existe y la red lo permite; si no, `visuals.py --offline` o imágenes propias en `imagenes/<id>.jpg`. No representar a Jesús ni a profetas como personas identificables.
5. Proyecto: `proyectos/<AAAA-MM-DD>-es-<tipo>-<slug>/guion.json` (esquema en `references/guion.md` de youtube-agent-skill; ejemplo en el Proyecto: `claude/kit/guion-noche1.json`).
6. Ejecutar: `python pipeline.py <proyecto>`. El render es lento en la nube (unos 30 min por video de 10 min): lánzalo en segundo plano con nohup y revisa el log.
7. Verifica 3 fotogramas, la miniatura, la duración (ffprobe) y los AVISOS de metadata.py.

## Podcast
- MP3: `ffmpeg -i in -af loudnorm=I=-16:TP=-1.5 -c:a libmp3lame -b:a 128k out.mp3`.
- Video para YouTube: portada 1920×1080 + audio (`-loop 1 -framerate 1 -tune stillimage -r 1`).
- Portada cuadrada de 3000×3000 para Spotify for Creators.

## SEO
- Título de 60 a 90 caracteres, con la palabra clave al inicio.
- Descripción: los primeros 150 caracteres con el valor del video, pasajes bíblicos, citas de EGW, una pregunta para comentar y el aviso «Narración con voz sintética».
- Etiquetas: 10 a 15, con un total de 500 caracteres como máximo. Hashtags: 3 como máximo.
- Activar «Contenido alterado o sintético» cuando corresponda. Asignar playlist: serie, Shorts o Podcast.

## Publicación
- **YouTube:** API de YouTube vía `www.googleapis.com` (alcanzable desde la nube). Token: `POST https://www.googleapis.com/oauth2/v4/token` con `grant_type=refresh_token`, más `client_id`, `client_secret` y `refresh_token` del Fundador (scopes `youtube.upload`, `youtube`, `drive.file`). Elegir siempre el canal MayorDom. Mientras el proyecto de Google Cloud no tenga la auditoría de la API, los videos subidos por API quedan en privado: avisar al Fundador.
- **Drive:** subir los entregables con la API de Drive (`www.googleapis.com/upload/drive/v3`) cuando no se pueda publicar.
- **Instagram:** `vidiq_instagram_publish_reel` (gratis), a partir del enlace del Short en YouTube, solo con una cuenta de Instagram conectada en vidIQ y la aprobación del Fundador.
- **Facebook:** Graph API cuando `graph.facebook.com` esté permitido en la red; si no, Meta Business Suite manual.
- Nunca publicar en público sin la aprobación del Fundador (PUERTA 3 de mayordom-agent-skill).

## Reglas
- Prohibido inventar citas, cifras o títulos. Lo que no se pueda verificar se marca [SIN VERIFICAR] y no se publica.
- Respuestas al Fundador: cortas, concisas y verificables.
- Coordinación de roles: `mayordom-agent-skill` (`/responsabilidad`).