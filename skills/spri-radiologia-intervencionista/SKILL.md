---
name: spri-radiologia-intervencionista
description: "Dirige el canal de YouTube de la Sociedad Peruana de Radiología Intervencionista (SPRI): calendario, temas, casos publicados, procedimientos y eventos a la luz de la evidencia de las principales revistas del mundo, guiones de largos y Shorts, visuales 4K/3D, SEO y paso a Facebook, Instagram y TikTok. Úsala para cualquier video, Short, tema, guion, SEO o programación del canal SPRI."
---

# SPRI · Radiología Intervencionista con evidencia

> Versión 1.1 · 2026-11-16 · Idiomas: español, inglés y portugués. v1.0: creada por orden del Fundador. Manda sobre el calendario y el formato del canal SPRI; las reglas generales del motor están en `CLAUDE.md` del repo canales-agent y en director-canales (si se contradicen, preguntar al Fundador).

Canal de la **Sociedad Peruana de Radiología Intervencionista (SPRI)**, autorizado por la SPRI. Objetivo: posicionar la marca SPRI como referente de radiología intervencionista en el Perú y Latinoamérica, explicando temas, casos, procedimientos y sus eventos (indicaciones, técnica, complicaciones, resultados) a la luz de la ciencia actual, y vinculando la actualidad médica con la investigación y los tratamientos intervencionistas. Todo gratis y de primera calidad.

Público doble: colegas (médicos, residentes, tecnólogos, enfermería) y pacientes y familias. Cada video dice al inicio a quién va dirigido y usa lenguaje claro sin perder rigor.

## Calendario (hora de Lima, UTC−5)

| Formato | `tipo` | Cuándo | Duración |
|---|---|---|---|
| **Evidencia al día**: un tema de actualidad médica o científica y lo que dice la evidencia intervencionista | `divulgacion` | Martes 20:00 (01:00Z del miércoles) | 8–12 min, 4K |
| **Caso y procedimiento**: un caso publicado, paso a paso (indicación, técnica, eventos, resultado, evidencia) | `analisis` | Jueves 20:00 (01:00Z del viernes) | 8–12 min, 4K |
| **Shorts** | `short` | Lunes a sábado 12:30 (17:30Z) | 45–60 s |

- Se escribe con **1 semana de adelanto** (la tarea del sábado escribe la semana que empieza 8 días después; `ventana_horas: 168`). Revisa el Fundador (médico) antes de la hora; si algo no va, se deja en privado y se corrige.
- Domingo: sin publicación (descanso y análisis de datos).
- Horas iniciales: ajustarlas con Analytics del canal a las 4 semanas.
- **Fases:** 1) YouTube largos y Shorts → 2) Facebook e Instagram (Reels, con `META_PAGE_TOKEN_SPRI` y el mismo usuario del sistema de Meta) → 3) TikTok (subida manual o API cuando haya cuenta de empresa aprobada).

## Idiomas: español, inglés y portugués (orden del Fundador, 16-nov-2026)
- **Largos:** un solo video. Narración principal en español (`lang: "es"`) y, en cada escena, `texto_en` y `texto_pt` con la misma idea y un largo parecido (±15 %; si queda más largo, se acorta). El motor arma las pistas de audio en inglés (en-US-AndrewNeural) y portugués (pt-BR-AntonioNeural), ajustadas al tiempo de cada escena, con sus subtítulos, y las deja en la release «audios-extra» del repo: se agregan en YouTube Studio → el video → Idiomas → Agregar audio (la API de YouTube no permite subirlas). Por eso los largos de SPRI van sin subtítulos pegados en la imagen.
- **Título y descripción** traducidos en `seo.localizaciones`: `{"en": {"title", "description"}, "pt": {"title", "description"}}` (el motor los sube solos).
- **Shorts:** narración en español, con título y descripción traducidos (`seo.localizaciones`).
- Términos técnicos: usar el nombre aceptado en cada idioma (p. ej. TACE / quimioembolización transarterial; embolização). Siglas en inglés entre paréntesis la primera vez.

## Shorts (6 por semana, rotan)
1. **¿Sabías que…?** un dato verificado de un estudio.
2. **Mito vs evidencia.**
3. **El procedimiento en 60 segundos** (qué es, para quién, cómo se hace).
4. **El número que importa** (una cifra del estudio y qué significa).
5. **Glosario IR** (un término: TACE, TIPS, embolización de miomas, ablación, PICC…).
6. **La pregunta del paciente** (respuesta clara + «consulta a tu médico»).
Uno por semana lleva al largo más cercano. 2 escenas, 90–190 palabras, `#shorts`.

## Fuentes (solo revisadas por pares; verificar autores, año, revista y DOI antes de usar)

**Generales (orden del Fundador):** New England Journal of Medicine, The Lancet, JAMA, BMJ, Nature Medicine, NIH-PubMed (conector PubMed), revistas médicas de la Sociedad Peruana de Medicina Interna, SciELO Ciencias de la Salud.

**Radiología intervencionista por región (las 3 principales de cada una):**
- **EE. UU.:** Journal of Vascular and Interventional Radiology (JVIR, SIR), Radiology (RSNA), American Journal of Roentgenology (AJR).
- **Europa:** CardioVascular and Interventional Radiology (CVIR, CIRSE), European Radiology (ESR), Insights into Imaging.
- **Reino Unido:** Clinical Radiology (Royal College of Radiologists), British Journal of Radiology (BJR), The Lancet / BMJ.
- **Alemania:** RöFo (Deutsche Röntgengesellschaft), CVIR Endovascular, Deutsches Ärzteblatt International.
- **Japón:** Japanese Journal of Radiology, Interventional Radiology (Japanese Society of Interventional Radiology), Cancer Science (oncología, Japanese Cancer Association).
- **Corea:** Korean Journal of Radiology, Journal of the Korean Society of Radiology, Ultrasonography (Korean Society of Ultrasound in Medicine).
- **China:** Journal of Interventional Medicine, Chinese Medical Journal, Chinese Journal of Radiology (中华放射学杂志; usar el resumen en inglés).
- **Latinoamérica y Perú:** SciELO, LILACS, Revista Peruana de Medicina Experimental y Salud Pública, Anales de la Facultad de Medicina (UNMSM), Revista de la Sociedad Peruana de Medicina Interna.
- **Guías:** CIRSE Standards of Practice, SIR Practice Parameters, ESR, NICE (Reino Unido), guías del MINSA.

Reglas:
1. Preferir revisiones sistemáticas, metaanálisis, ensayos y guías; decir siempre el diseño, el tamaño y los límites.
2. Cada cifra dicha en voz debe estar en el resumen o texto recuperado; redondear hacia abajo; nada de memoria.
3. Citar en voz «autor principal, revista, año»; en la descripción, la referencia completa con enlace (PubMed o revista) y DOI.
4. Sin preprints como base, sin notas de prensa, sin material promocional de fabricantes. Marcas de dispositivos: solo si el estudio las nombra y sin recomendar una.
5. Actualidad: vincular la noticia médica con la evidencia; si es una noticia, citar la fuente periodística y el estudio original.

## Casos clínicos e imágenes (privacidad primero)
- **Solo casos publicados** con licencia que permita reutilizar (CC BY o CC BY-SA, por ejemplo artículos de acceso abierto en PubMed Central) y repositorios libres (Wikimedia Commons, Openverse). Citar autor, revista, licencia y enlace.
- **No usar** licencias «NC» (no comercial) mientras el canal pueda monetizar, ni imágenes con datos del paciente (nombre, fecha de nacimiento, número de historia, rostro).
- **Nunca** casos ni imágenes de pacientes propios del Fundador o de colegas en esta etapa (decisión del Fundador, 16-nov-2026; Ley 29733 de datos personales).

## Visuales: 4K, 3D y 360
- Cada escena con `visual.query` EN INGLÉS y concreta (p. ej. «catheter angiography suite», «liver anatomy 3D render», «interventional radiologist fluoroscopy»). El motor pone clips 4K de Pexels (`clips_largos: true`, requiere `PEXELS_API_KEY`) y, si no hay, imágenes libres ≥2000 px de Openverse o Wikimedia Commons, con créditos y licencia en la descripción.
- **Ilustraciones 3D:** buscar renders 3D anatómicos con licencia libre (Wikimedia Commons, Openverse, BodyParts3D CC BY-SA, NIH 3D) y ponerlos en `imagenes/<id>.jpg`. Fase siguiente: render propio de modelos 3D libres con Blender en GitHub Actions (gratis).
- **360:** fase posterior (video equirrectangular con metadatos esféricos); solo cuando haya material 360 libre o propio sin pacientes.
- Videos largos en 4K (`res_4k: true`); Shorts 1080x1920. Miniatura de impacto con la marca SPRI y una pregunta.

## Estructura de los largos
**Evidencia al día (martes):** 1) gancho con la noticia o pregunta clínica; 2) para quién es el video; 3) contexto y anatomía (3D si hay); 4) qué dice la evidencia (estudios con cifras); 5) cómo lo resuelve la radiología intervencionista; 6) límites y lo que falta investigar; 7) mensaje para colegas y para pacientes; 8) cierre SPRI + pregunta para comentarios.
**Caso y procedimiento (jueves):** 1) gancho con el caso (sin datos personales); 2) presentación del caso publicado; 3) indicación y alternativas; 4) técnica paso a paso; 5) eventos y complicaciones (frecuencia según la literatura); 6) resultado y seguimiento; 7) qué aprendimos y qué dice la evidencia; 8) cierre SPRI.
Mínimo 3 escenas con `capitulo`; `emocion` en cada escena; voz: edge `es-PE-AlexNeural`, o `voz_fundador: true` en el insignia mensual.

## SEO y marca
- Título: procedimiento o enfermedad al inicio + beneficio o pregunta («¿Embolización de miomas sin cirugía? Lo que dice la evidencia 2026»). 60–90 caracteres. Sin promesas de curación.
- Descripción: resumen de 150 caracteres, capítulos, referencias completas, aviso «Contenido educativo; no reemplaza la consulta médica», enlaces de la SPRI.
- Etiquetas: SPRI, Sociedad Peruana de Radiología Intervencionista, radiología intervencionista, el procedimiento, la enfermedad, términos en inglés (interventional radiology).
- Marca: logo SPRI en la miniatura y en la pantalla final; color de marca del manual de la SPRI cuando el Fundador lo entregue.

## Campos del guion.json
`lang: "es"`, `texto_en` y `texto_pt` en cada escena de los largos, `seo.localizaciones` (en, pt), `tipo`, `fecha`, `serie` («Evidencia al día · SPRI» o «Caso y procedimiento · SPRI»), `tema`, `res_4k: true` en los largos, `contenido_sintetico: true`, `revision_medica: "pendiente"`, `seo` con `categoria_id: "27"` (Educación), `privacidad: "private"` y `publicar_en` en UTC, `visual.query` en cada escena. Carpeta: `canales/spri/proyectos/<AAAA-MM-DD>-es-<tipo>-<slug>/`.

## Flujo semanal (dentro de «Director de canales: semana», sábado)
1. Listar proyectos existentes (sin duplicados).
2. Elegir 2 temas (uno de actualidad, un caso publicado) y buscar la evidencia en las fuentes de arriba.
3. Escribir los 2 largos y los 6 Shorts en una pasada.
4. Segunda revisión por un agente distinto: cifras contra los resúmenes, privacidad del caso, licencias de imágenes, títulos sin promesas.
5. `python scripts/validate.py <proyecto>`; commit y push a `main`.
6. Avisar al Fundador: temas, títulos y qué revisar antes de la hora.

## Puesta en marcha (una sola vez)
1. Crear el canal de YouTube como cuenta de marca «SPRI · Radiología Intervencionista» (o el nombre que apruebe la SPRI), con logo y banner de la SPRI.
2. Llave de YouTube con OAuth Playground (mismo cliente MayorDom-uploader) eligiendo el canal SPRI → secreto `REFRESH_TOKEN_SPRI` en GitHub.
3. Poner su `youtube_id` en `canales.json` → `spri` y cambiar `activo` a `true`.
4. Fase 2: página de Facebook e Instagram de la SPRI, compartidas con el usuario del sistema `canales-agent` → `META_PAGE_TOKEN_SPRI`.
