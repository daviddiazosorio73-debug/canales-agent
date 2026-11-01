---
name: cryptuline-ciencia
description: "Cryptuline · Salud con ciencia (canal de YouTube del Fundador): escribe los videos de divulgación de salud y nutrición basados solo en estudios verificados de PubMed (martes salud, viernes nutrición, domingo salud espiritual IASD) y sus 21 Shorts semanales, con revisión médica y una semana de adelanto. Úsala para cualquier guion, tema, título, Short, SEO o revisión médica de Cryptuline."
---

# Cryptuline · Salud con ciencia

> Versión 1.0 · 2026-11-01 · Reglas tomadas de `CLAUDE.md` del repo canales-agent y de director-canales (mandan si difieren; si se contradicen, preguntar al Fundador).

Canal de educación en salud para adultos (+18). Objetivo: que la gente entienda qué dice de verdad la ciencia, con datos verificables y sin promesas. La gerencia (calendario, qué se escribe, aviso al Fundador) es de director-canales; el motor `canales-agent` produce y sube.

## Calendario (hora de Lima, UTC−5)

| Día | Tipo | Tema | Hora |
|---|---|---|---|
| Domingo | `divulgacion` | Salud espiritual con enfoque IASD | 18:00 (23:00Z) |
| Martes | `divulgacion` | Salud | 18:00 (23:00Z) |
| Viernes | `divulgacion` | Nutrición | 18:00 (23:00Z) |
| Todos los días | `short` (3) | Sacados de los 3 temas largos de la semana, sin investigar aparte | 07:00 · 13:00 · 20:30 (12:00Z · 18:00Z · 01:30Z del día siguiente) |

- La educación es el eje de todos los videos.
- **Una semana de adelanto:** la tarea del sábado escribe la semana que empieza 8 días después. El motor sube 7 días antes (`ventana_horas: 168`), en privado con `publicar_en`.
- Espirulina: fuera hasta nuevo aviso del Fundador (`validate.py` lo bloquea).
- Horas iniciales; ajustarlas con los datos de `investigacion/cryptuline.md` cuando haya suficientes.

## Fuentes (solo científicas)

1. Buscar y leer los estudios con el conector PubMed (`search_articles`, `get_article_metadata`) y, como apoyo, `investigacion/cryptuline_pubmed.md`.
2. Preferir revisiones sistemáticas, metaanálisis y ensayos en humanos. Decir siempre el diseño (observacional, ensayo, en animales), el tamaño y los límites.
3. Cada cifra dicha en voz debe estar en el resumen o los metadatos recuperados; redondear hacia abajo. Nada de cifras de memoria.
4. Citar en voz «autor principal, año» y en la descripción: autores, año, título, revista, `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` y DOI si existe.
5. Biblia y Elena G. de White (domingo IASD): Regla única de citas de director-canales.

## Lenguaje obligatorio

- «Este estudio encontró…», «se asoció con…»; nunca «cura», «previene», «garantiza» ni «milagro» como promesa (el validador avisa si aparecen; solo se aceptan en frases que los niegan).
- Cerrar con «consulta a tu médico» antes de cambiar alimentación, actividad física o un tratamiento.
- Nada de inversión, NFT, cripto ni ventas; sí la marca Cryptuline.
- Temas delicados (abuso, salud mental): aclarar que no reemplaza ayuda profesional e invitar a buscarla.

## Estructura del largo (`divulgacion`, 1 000–1 300 palabras, 7–9 escenas)

1. **Gancho** con un dato sorprendente verificado y una pregunta que se responde al final (sin revelarla en título ni miniatura).
2. **Qué es** (definiciones claras).
3. **El estudio**: quién, cuándo, cuántas personas, diseño.
4. **Hallazgos** con cifras exactas del resumen.
5. **Mitos vs. evidencia.**
6. **Cómo leer un estudio** (una enseñanza por video: asociación vs. causa, riesgo relativo, tamaño de muestra…).
7. **Límites** de la evidencia.
8. **Aplicación** práctica y prudente + «consulta a tu médico».
9. **Respuesta** a la pregunta del gancho + invitación a comentar.

Escenas con `id`, `capitulo` (≥3) y `emocion` (gancho, ensenanza, enfasis, narrativo, calido, reflexivo).

## Shorts (21 por semana)

`tipo: "short"`, 2 escenas (`gancho` con `capitulo` y `texto_pantalla`; `mensaje` con `referencia` = «Autor, año»), 90–190 palabras, título con `#shorts` (≤100 caracteres). Uno de cada día lleva al largo más cercano.

## Campos del guion.json

`lang: "es"`, `tipo`, `fecha`, `serie: "Salud con ciencia · Cryptuline"`, `tema`, `voz_fundador: true`, `color_marca: [46, 196, 140]`, `contenido_sintetico: true`, `revision_medica: "pendiente"` (la médica lo cambia a `aprobada` u `observada`), `miniatura` (pocas palabras, elemento de curiosidad), `seo` con `categoria_id: "27"`, `privacidad: "private"`, `publicar_en` en UTC. El avatar sale solo (`canales/cryptuline/assets/avatar.jpg`).

Descripción, al final: bloque «📚 Fuentes (PubMed)» y el aviso: «Contenido educativo para mayores de 18 años. No reemplaza la consulta médica: consulta a tu médico antes de cambiar tu alimentación, tu actividad física o un tratamiento. Narración con voz sintética. Cryptuline.» (`validate.py` exige +18 y «médico»).

## Revisión médica

- Al terminar la semana, avisar al Fundador en una lista corta qué afirmaciones debe revisar la médica (las más sensibles primero).
- La médica revisa antes de la hora de publicación; si algo no va, el Fundador lo deja en privado y Claude corrige.
- Registrar el resultado en `revision_medica` de cada guion (`aprobada` / `observada`).

## Flujo

1. Listar proyectos existentes de la semana (sin duplicados).
2. Elegir los 3 temas (cruzar `investigacion/cryptuline.md` con el calendario) y buscar los estudios en PubMed.
3. Escribir los 3 largos y los 21 Shorts en una pasada.
4. Segunda revisión por un agente distinto: cifras contra los resúmenes, lenguaje, títulos sin spoiler.
5. `python scripts/validate.py <proyecto>` en cada uno; commit y push a `main`.
6. Avisar al Fundador: temas, títulos y lista para la médica.
