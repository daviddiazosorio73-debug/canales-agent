# Instrucciones para Claude en este repositorio
- Este repo es el motor de los 4 canales del Fundador. Respuestas cortas, verificables, sin inventar citas.
- Guiones: `canales/<canal>/proyectos/<AAAA-MM-DD>-<lang>-<tipo>-<slug>/guion.json` (esquema de youtube-agent-skill; tipos: sermon, analisis, short, intro, diario, resumen_viernes, repaso_sabado).
- `seo.publicar_en` en UTC (Lima = UTC−5). Nunca borres un `publicado.json`.
- Para MayorDom sigue la skill mayordom-youtube; Escuela Sabática ES/PT: youtube-agent-skill; Top 10: multiredes-agents-skill.
- Tras escribir guiones: valida con `python scripts/validate.py <proyecto>`, commitea y haz push a main. El workflow hace el resto.
- Voz del Fundador (clonada, Chatterbox): en el `guion.json` del video insignia pon `"voz_fundador": true`. Cada escena puede llevar `"emocion"`: gancho, enfasis, narrativo, ensenanza, agil, calido, reflexivo u oracion. Si no la lleva, se infiere del id de la escena y del texto. Usa la expresividad donde corresponda: gancho enérgico, historias narradas, enseñanza clara, oración pausada y Shorts ágiles.
- Top 10 SEMANAL: datos y producción automáticos; el LIBRETO lo escribe Claude (tarea del domingo 00:10 Lima) sobre la plantilla, con un plazo de 100 min; si no llega, sale la plantilla. Flujo: `.github/workflows/top10-semanal.yml` (domingo 04:55 UTC) → `scripts/top10_semana.py` (datos + guiones por plantilla, ediciones en `scripts/top10_ediciones.json`: Oceanía, Asia, África, Europa, América y Mundial; vetos en `scripts/top10_vetos.json`) → producción en paralelo → `scripts/top10_cadena.py` (lista «Vuelta al mundo» y enlace a la siguiente parada). Hashtag del canal: #Top10RS.
- Libreto Top 10 (Claude): en cada proyecto del día reescribe SOLO `escenas[].texto` en el idioma de `lang`, usando únicamente datos de `categorias3.json` (cifras redondeadas hacia abajo, nada inventado), suspenso sin revelar el podio antes de su puesto, apertura con gancho, transiciones entre categorías, cierre con «siguiente parada» y #Top10RS. Si la plantilla trae un anuncio (p. ej. «desde la semana 45 sumamos TikTok»), consérvalo en el cierre. En los continentes conserva la invitación a suscribirse (ganadores del continente primero; el top 3 de cada lista pasa al mundial). El Top 10 Mundial NO investiga aparte: se arma con los 3 primeros de cada categoría de cada continente (mismo corte y mismas cifras). Mantén ids, `video_id`, `capitulo`, `emocion`. Luego `"libreto": "claude"`, valida, commit y push.
- Top 10 (manual/antiguo): copia `categorias3.json` (listas views/comments/likes del #1 al #10) dentro del proyecto. Con eso el motor genera solo: fichas de impacto con conteo animado, tabla final por categoría, miniatura de impacto, SEO del conteo (etiquetas frecuentes, hashtags, menciones @creador) y agrega el video a la lista «Top 10 Redes Sociales · Ediciones semanales». Escenas: ids `v10…v01`, `c10…c01`, `l10…l01` con `video_id` y `modo` (completo/rapido).

## Buenas prácticas para todos los canales (pedidas por el Fundador)
- Las mejoras se INTEGRAN a lo ya aprobado; nunca reemplazan una presentación que funcionó (p. ej. Top 10: secuencias de cuadros + fichas nuevas).
- Suspenso: el gancho promete, no revela. No anticipes el resultado (Top 10: ni nombre ni imagen del podio antes de su puesto; en sermones: plantea la pregunta y responde al final). Miniatura, título y descripción tampoco revelan el desenlace.
- Miniatura de impacto: pocas palabras, texto gigante con contorno, un elemento de curiosidad (pregunta o casilla "?"), máx. 1280x720.
- Video en 4K (3840x2160) para Top 10 y videos insignia (`voz_fundador`) o con `"res_4k": true`. Shorts: 1080x1920.
- SEO: etiquetas propias primero; el motor suma las del nicho (`investigacion/<canal>.seo.json`, semanal) y, en Top 10, las de los videos del conteo con menciones @creador.
- Listas de reproducción automáticas por tipo (`canales.json` → `listas`); no hace falta crearlas a mano.
- Datos y citas solo verificados; las cifras salen de la API.

## Cryptuline (canal de espirulina con ciencia)
- Proyectos en `canales/cryptuline/proyectos/`: 3 videos `tipo: "divulgacion"` por semana (mar, jue, sáb 23:00 UTC = 18:00 Lima) y 3 `short` diarios (12:00, 18:00 y 01:00 UTC = 07:00, 13:00, 20:00 Lima). Horas iniciales: ajústalas con Analytics.
- Tema del mes y ángulos: `canales/cryptuline/ruta.json`. Fuentes: SOLO `investigacion/cryptuline_pubmed.md` (PubMed, semanal). Cita en voz (autor principal, año) y en la descripción: autores, año, revista y `https://pubmed.ncbi.nlm.nih.gov/<PMID>/`.
- Sin afirmaciones de cura/prevención: «este estudio encontró…», con límites (tamaño, en animales o humanos) y «consulta a tu médico». Nada de inversión, NFT, cripto ni ventas; sí la marca Cryptuline.
- Viralidad científica: gancho con dato sorprendente verificado, pregunta que se responde al final, mitos vs evidencia. `voz_fundador: true` en todo; el avatar sale solo (assets/avatar.jpg). `categoria_id: "27"`.
