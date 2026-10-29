---
name: "mayordom-youtube"
description: "Escribe los guiones del canal YouTube @MayorDom (Mayordomía Bíblica): sermones lun/mié/vie, análisis mar/jue, 3 shorts diarios y podcast; el motor canales-agent produce y publica."
---

# MayorDom YouTube — producción y publicación de punta a punta

Canal: **MayorDom** (@MayorDom, ID `UCxGgMCMbyiCvRo_T-haI_Ug`, Perú). Idioma: español neutro latinoamericano. Todo gratis.

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

## Producción (motor canales-agent, automático)
1. Claude escribe `canales/mayordom/proyectos/<AAAA-MM-DD>-es-<tipo>-<slug>/guion.json` (esquema de youtube-agent-skill; un ejemplo: cualquier proyecto existente del canal). Antes, lista los proyectos: no repitas un día y tipo que ya exista.
2. `python scripts/validate.py <proyecto>`, commit y push a main.
3. El workflow `producir.yml` (cada hora) produce lo que se publica en las próximas 36 h: voz gratis (Piper `vits-piper-es_MX-claude-high`; Chatterbox con la voz del Fundador si `"voz_fundador": true`), imágenes, subtítulos, render (Shorts 1080x1920; insignia 4K), miniatura, SEO, subida y lista automática por tipo.
4. Imágenes propias opcionales en `imagenes/<id>.jpg`. No representar a Jesús ni a profetas como personas identificables.
5. Revisa el resultado en `publicado.json` (URL) y los logs del workflow si algo falló. Nunca borres un `publicado.json`.

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
- **YouTube:** la hace el motor con `REFRESH_TOKEN_MAYORDOM` (secreto de GitHub): sube en privado con `seo.publicar_en` (UTC; Lima = UTC−5) y YouTube lo hace público a esa hora. Sin `publicar_en`, queda privado.
- **Instagram/Facebook:** con `META_PAGE_TOKEN_MAYORDOM` si existe; si no, manual (Meta Business Suite). Instagram vía vidIQ solo con cuenta conectada y aprobación del Fundador.
- Nunca publicar fuera del calendario aprobado (skill director-canales).

## Reglas
- Prohibido inventar citas, cifras o títulos. Lo que no se pueda verificar se marca [SIN VERIFICAR] y no se publica.
- Respuestas al Fundador: cortas, concisas y verificables.
- Coordinación de roles: `mayordom-agent-skill` (`/responsabilidad`).