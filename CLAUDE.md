# Instrucciones para Claude en este repositorio
- Este repo es el motor de los 4 canales del Fundador. Respuestas cortas, verificables, sin inventar citas.
- Guiones: `canales/<canal>/proyectos/<AAAA-MM-DD>-<lang>-<tipo>-<slug>/guion.json` (esquema de youtube-agent-skill; tipos: sermon, analisis, short, intro, diario, resumen_viernes, repaso_sabado).
- `seo.publicar_en` en UTC (Lima = UTC−5). Nunca borres un `publicado.json`.
- Para MayorDom sigue la skill mayordom-youtube; Escuela Sabática ES/PT: youtube-agent-skill; Top 10: multiredes-agents-skill.
- Tras escribir guiones: valida con `python scripts/validate.py <proyecto>`, commitea y haz push a main. El workflow hace el resto.
- Voz del Fundador (clonada, Chatterbox): en el `guion.json` del video insignia pon `"voz_fundador": true`. Cada escena puede llevar `"emocion"`: gancho, enfasis, narrativo, ensenanza, agil, calido, reflexivo u oracion. Si no la lleva, se infiere del id de la escena y del texto. Usa la expresividad donde corresponda: gancho enérgico, historias narradas, enseñanza clara, oración pausada y Shorts ágiles.
- Top 10: copia `categorias3.json` (listas views/comments/likes del #1 al #10) dentro del proyecto. Con eso el motor genera solo: fichas de impacto con conteo animado, tabla final por categoría, miniatura de impacto, SEO del conteo (etiquetas frecuentes, hashtags, menciones @creador) y agrega el video a la lista «Top 10 Redes Sociales · Ediciones semanales». Escenas: ids `v10…v01`, `c10…c01`, `l10…l01` con `video_id` y `modo` (completo/rapido).
