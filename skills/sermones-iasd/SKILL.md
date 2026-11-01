---
name: "sermones-iasd"
description: "Usar para crear sermones y presentaciones de sermones dentro de la teología adventista (IASD): cita versiones bíblicas de sociedades reconocidas, respalda con Elena G. de White e investigación científica revisada por pares, genera imágenes y entrega en .pptx y .txt."
---

# Sermones IASD

> Versión 1.1 · 2026-11-01 · Regla única de citas (alineada con director-canales).

Produce un sermón completo (texto predicable) y su presentación de diapositivas a partir de un tema, un pasaje bíblico o un documento que el usuario entregue. Dos entregables siempre: un `.txt` con el sermón completo y un `.pptx` con la presentación — nunca solo uno de los dos salvo que el usuario pida explícitamente uno solo.

Regla rectora de todo el proceso: **cero alucinaciones, cero suposiciones**. Todo dato verificable (cita bíblica exacta, cita de Elena G. de White, estudio científico, estadística, nombre propio) se busca y se verifica con una herramienta antes de escribirse. Si algo no se puede verificar, se dice explícitamente en el texto («esto no se pudo verificar») en vez de omitirlo o suavizarlo — nunca se inventa una referencia que suene plausible.

## 1. Encuadre antes de investigar

Antes de buscar nada, confirma con el usuario (o infiere del material que entregó) tres cosas: el tema o pasaje central, la ocasión (sermón de semana de oración, campaña de salud, mayordomía, etc. — afecta el tono) y cuánto tiempo de prédica debe durar (orienta la extensión del `.txt`). Si el usuario ya entregó un documento largo (como en la serie "Semana de Reavivamiento Espiritual"), ese documento ES el contenido base — no se reemplaza, se enriquece con lo que falta: citas bíblicas exactas, respaldo de Elena G. de White, investigación científica, y las imágenes.

## 2. Investigación (siempre antes de escribir una sola línea del sermón)

### Base bíblica
- Identifica los pasajes centrales y de apoyo. Para cada uno, da la referencia completa (libro capítulo:versículo) y la versión usada, con su abreviatura (RV1960, NVI, DHH, NTV, LBLA, etc.) — todas reconocidas por sociedades bíblicas (Sociedades Bíblicas Unidas, Biblica). Contrasta al menos 2 versiones cuando el matiz de traducción importe para el punto que se está haciendo.
- **Derechos de autor de la Biblia**: las traducciones modernas (RV1960 en adelante, NVI, DHH, NTV, LBLA, etc.) tienen copyright vigente de sus sociedades bíblicas. Nunca se reproduce un pasaje largo de una versión con copyright — se cita la referencia y, si hace falta una cita textual, se mantiene corta (hasta 2 o 3 versículos seguidos) y siempre atribuida a su versión. Es la Regla única de citas (todas las skills; ver director-canales). Para citas textuales más largas, usa una versión de dominio público (Reina-Valera 1909, Valera 1602, Torres Amat) y dilo explícitamente.
- Nunca cites un versículo de memoria sin confirmar el texto exacto — búscalo (BibleGateway, YouVersion, o la fuente que tengas disponible) antes de transcribirlo.

### Elena G. de White
- Busca citas relevantes en egwwritings.org o whiteestate.org (fuentes oficiales). Cada cita lleva su referencia exacta: libro, página o párrafo (ej. *El Deseado de Todas las Gentes*, p. 123).
- Nunca parafrasees una idea de ella y la presentes como cita textual — si es paráfrasis, dilo ("como explica Elena G. de White en...", sin comillas).
- Si el tema no tiene respaldo directo de ella, dilo — no se fuerza una cita que no aplica.

### Investigación científica
- Para cualquier afirmación de salud, psicología, sociología o ciencia que el sermón haga (común en temas de mayordomía física, salud mental, etc.), busca estudios revisados por pares reales — usa PubMed, Google Scholar vía búsqueda web, o las herramientas de investigación científica disponibles en la sesión. Cita autor(es), año, revista, y el hallazgo concreto — nunca una estadística sin fuente.
- Si no se encuentra respaldo científico sólido para una afirmación que el usuario quiere incluir, dilo claramente en vez de inventar un estudio o inflar la certeza del hallazgo.

### Verificación general
- Cualquier dato histórico, cifra, o referencia a una organización (Asociación, Unión, División) se verifica igual que lo bíblico/EGW/científico — nunca se asume.

## 3. Redacción del sermón (`.txt`)

Estructura estándar, ajustable al tema: título; introducción (gancho que conecta con la audiencia); cuerpo organizado en puntos principales, cada uno con su respaldo bíblico, su respaldo de Elena G. de White cuando exista, y su respaldo científico cuando aplique; aplicación práctica concreta; llamado/cierre. Se escribe como texto predicable completo (oraciones completas, en el tono de quien predica), no como una lista de viñetas — las viñetas son para las diapositivas, el `.txt` es el sermón en sí.

Termina el `.txt` con una sección "Fuentes" que liste cada versión bíblica usada, cada cita de Elena G. de White con su referencia completa, y cada estudio científico citado (autor, año, revista/DOI o enlace) — así todo queda verificable por el usuario o por un tercero.

El contenido debe enmarcarse dentro de la teología adventista (las 28 Creencias Fundamentales como referencia doctrinal). Si el tema roza un punto doctrinal donde hay más de una postura dentro del adventismo, se puede mencionar, pero sin presentar como consenso oficial algo que no lo es.

## 4. Presentación (`.pptx`)

Sigue la identidad visual ya establecida en el proyecto "Sermones" de David (serie "Semana de Reavivamiento Espiritual", 8 diapositivas, pptxgenjs con `LAYOUT_WIDE`, helpers `shadow()`, `badge()`, `footer()`, `kicker()`, `title()`, `photoCard()`, paleta cálida de campaña) salvo que el usuario pida otra línea visual — revisa builds anteriores del mismo proyecto (`tema03/build.js`, `tema07/build.js`, `tema04/build.js` si existen en el entorno) como referencia de patrón antes de construir uno nuevo.

**Imágenes**: genera imágenes hiperrealistas alusivas al tema con la herramienta de generación de imágenes disponible en la sesión (p. ej. Canva generate-image). El objetivo es la mayor resolución posible — en la práctica, las herramientas disponibles a veces solo devuelven miniaturas de baja resolución; en ese caso aplica el pipeline ya usado en el proyecto (reescalado Lanczos a ~1600px + unsharp mask + ajuste de contraste/color vía PIL) para acercarse a calidad 4K, y dile al usuario honestamente cuál fue la resolución final lograda — nunca afirmes "4K" si la imagen entregada no se acerca a esa resolución real.

**QA obligatorio antes de entregar**: renderiza el `.pptx` a PDF con LibreOffice headless, cuenta las páginas, y rasteriza cada diapositiva a PNG para revisarla visualmente (recorte y zoom si hace falta) — confirma que no haya texto desbordado y que la simetría del diseño se mantenga, igual que en las entregas anteriores de la serie.

## 5. Entrega

Construye en un directorio de trabajo propio del tema, copia los entregables finales a la carpeta de salida, y entrega ambos archivos (`.pptx` y `.txt`) con el resumen de fuentes a la vista. Si alguna cita bíblica, de Elena G. de White o científica no pudo verificarse, dilo en el mensaje de entrega, no solo en el archivo.