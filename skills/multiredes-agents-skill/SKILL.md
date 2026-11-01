---
name: "multiredes-agents-skill"
description: "Top 10 Redes Sociales (@Top10RedesSociales): conteo semanal automático en el motor canales-agent (corte miércoles 00:00 Lima, ediciones por continente + Mundial), libreto de Claude y Shorts del podio."
---

# Top 10 Redes Sociales — conteo semanal (vigente: motor canales-agent)

> Versión 1.1 · 2026-11-01 · El formato antiguo pasó a skills/multiredes-agents-skill/ARCHIVO.md del repo.

Canal @Top10RedesSociales (ID `UC5hAk81MlV4wE5Lvl9PV1lQ`), hashtag #Top10RS. **Ninguna cifra sale de la IA: todas salen de la API oficial de YouTube** (`categorias3.json`). Úsala cuando el Fundador pida el conteo, el libreto, los Shorts, la miniatura o el SEO del Top 10, o /multiredes-agents-skill. Las reglas detalladas del libreto están en `CLAUDE.md` del repo `canales-agent` (mandan sobre esta skill si difieren). Repo: `add_repo` owner `daviddiazosorio73-debug`, repo `canales-agent`, access `push`; clonar en `/home/claude/canales-agent`.

## Calendario vigente (todo automático salvo el libreto)
| Momento (Lima, UTC−5) | Paso | Dónde |
|---|---|---|
| **Miércoles 00:00** (05:00Z) | Corte semanal: datos + guiones por plantilla de las 6 ediciones | `.github/workflows/top10-semanal.yml` → `scripts/top10_semana.py` |
| **Miércoles 00:10** | Claude reescribe el libreto (plazo 100 min; si no llega, sale la plantilla) | Tarea programada «Top 10: libretos del miércoles» |
| Miércoles–jueves | Producción en paralelo (4K), subida privada con `publicar_en` | mismo workflow |
| Al terminar la producción | Cadena «Vuelta al mundo» (lista + enlace a la siguiente parada) y **3 Shorts por edición** | `scripts/top10_cadena.py`, `scripts/top10_shorts.py` |
| **Domingo 06:00 hora local** de cada continente | Estreno: Oceanía (Sídney) → Asia (Calcuta) → África (El Cairo) → Europa (París) → América (Lima) → Mundial (Lima) | `scripts/top10_ediciones.json` |
| Estreno + 7 h / + 14 h 30 / + 25 h | Shorts del podio: vistas, comentarios, likes (1080x1920) | `scripts/top10_short_visual.py` en el runner |
| Sábado | No corre nada del Top 10 | — |

Idiomas: América narra en español; el resto en inglés con títulos/descripciones traducidos (`locs`). Vetos en `scripts/top10_vetos.json`. El **Mundial no investiga aparte**: se arma con los 3 primeros de cada categoría de cada continente (mismo corte, mismas cifras).

## Libreto (lo único que escribe Claude)
- En cada proyecto `tipo: "top10"` del día reescribe SOLO `escenas[].texto` en el idioma de `lang`, con datos de `categorias3.json` (cifras redondeadas hacia abajo, nada inventado).
- Suspenso: ni nombre ni imagen del podio antes de su puesto; gancho de apertura; transiciones entre categorías; cierre con «siguiente parada» y #Top10RS; conservar anuncios de la plantilla (p. ej. «desde la semana 45 sumamos TikTok»).
- Reglas: anunciar el corte (miércoles a las cero horas, hora de Lima, Perú); conservar «¿premiación real para los ganadores? Comenta #PremiosTop10RS» (en voz: «el hashtag Premios Top 10 RS, todo junto»); en continentes, invitación a suscribirse (ganadores del continente primero; el top 3 de cada lista pasa al mundial).
- Mantener ids, `video_id`, `capitulo`, `emocion`. Poner `"libreto": "claude"`, `python scripts/validate.py <proyecto>`, commit y push a main.

## Shorts del Top 10 (automáticos, no los escribe Claude)
`scripts/top10_shorts.py` crea 3 por edición ya subida (podio #3, #2, #1 de una categoría + enlace a la edición). Omite ediciones sin `publicar_en` o cuyo estreno pasó hace más de 24 h (no rellena ediciones viejas; `--todas` lo fuerza). Lista: «Shorts · Top 10 Redes Sociales».

## Reglas del canal
- Nombre y gráficos propios: nunca "Billboard", "Grammy" ni logos de las redes. Solo datos públicos del creador.
- Voz IA: `containsSyntheticMedia` = true. Subidas privadas con `publicar_en`; nunca público sin calendario aprobado. Nunca borrar un `publicado.json`.
- Todo gratis; nada de pago sin autorización del Fundador. Nunca escribir secretos en el repo, memoria ni Proyecto. Si el Fundador pega una clave en el chat, úsala solo en un archivo privado de la sesión y recuérdale rotarla.

## Archivo: kit del PC (formato antiguo)
El formato anterior (LATAM ES/PT, corte sábado 23:50, en vivo domingo 16:00 con la app ViralTop10 LATAM, extracción con Apify, scripts `common.py`, `extract_youtube.py`, `extract_apify.py`, `normalize.py`, `score.py`, `export_app.py`, `cards.py`, `tts_gratis.py`, `validate_top10.py`, `pipeline_top10.py` y su `config.json`) **no es el calendario vigente**. Su texto y scripts completos están en el repo: `canales-agent/skills/multiredes-agents-skill/ARCHIVO.md`. Úsalo solo si el Fundador lo pide expresamente (p. ej. para un en vivo con la app del conductor).