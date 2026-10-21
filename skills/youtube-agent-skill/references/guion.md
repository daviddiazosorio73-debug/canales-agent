# Guion: reglas, estructura y esquema

## Contenido
1. Reglas de originalidad y derechos
2. Estructura del video diario (domingo a jueves)
3. Estructuras de sábado (intro), viernes (resumen) y sábado (repaso)
4. Estilo de narración (ES / PT)
5. SEO
6. Esquema de guion.json

## 1. Reglas de originalidad y derechos

La Guía de Estudio de la Biblia (Escuela Sabática) es © de la Asociación General de los ASD. Su aviso prohíbe reproducir, adaptar o traducir el texto sin autorización escrita. Las ediciones en español (ACES) y portugués (CPB) están bajo el mismo régimen. Además, YouTube excluye de la monetización el contenido "inauténtico" y producido en masa.

Por eso el guion es un comentario original sobre el tema, no una versión de la lección:

- Usa de la lección solo los datos públicos: número, título, tema del día y los pasajes bíblicos citados. Nunca copies, parafrasees de cerca, traduzcas ni sigas párrafo a párrafo el texto de la lección.
- No reproduzcas las preguntas de la lección. Formula preguntas propias.
- El aporte original tiene que ser real: contexto histórico, aplicación práctica actual, una ilustración propia, conexiones entre textos y una pregunta para meditar.
- Cita textos bíblicos literalmente solo si tienes el texto verificado de una versión permitida (`version_biblica` en guion.json). Si no lo tienes, menciona la referencia y parafrasea. Nunca inventes el texto de un versículo.
- **Espíritu de Profecía (Elena G. de White):** cada cita lleva libro, capítulo o página y es breve, una o dos oraciones como máximo. Antes de usarla, verifícala palabra por palabra en egwwritings.org, en la edición del idioma del video. Si no puedes verificarla, no la cites como textual: menciona la obra y resume la idea con tus palabras. Nunca atribuyas a Elena G. de White una frase que no hayas verificado. Las citas que ya trae la lección sirven como pista de dónde buscar, pero no se copian de la lección.
- Varía la estructura, los ganchos y las ilustraciones entre videos para que no sean repetitivos.

## 2. Video diario: domingo a jueves (800–1800 palabras, unos 6–12 min)

| # | Escena (`capitulo`) | Propósito | Palabras |
|---|---|---|---|
| 1 | Gancho | Pregunta o situación real en los primeros 15 s; anuncia qué se gana al ver | 60–100 |
| 2 | Contexto | Lección N, día, tema; ubicar el pasaje bíblico | 120–200 |
| 3–5 | Desarrollo (2–3 ideas) | Una idea por escena, cada una con texto bíblico, explicación e ilustración | 200–350 c/u |
| 6 | Aplicación | Qué hacer hoy; concreto | 120–200 |
| 7 | Para meditar + cierre | Pregunta para comentar, invitación a suscribirse y a la lección de mañana; oración breve opcional | 80–150 |

## 3. Estructuras de sábado y viernes

La semana va de sábado a sábado. Cada estructura indica sus capítulos en orden.

### `intro` – sábado por la tarde (700–1250 palabras, 5–8 min)
Abre la lección nueva.
1. **Gancho:** una pregunta o situación que el tema de la semana responde.
2. **Panorama:** número y título de la lección, y cómo se conecta con la lección anterior y con el tema del trimestre.
3. **Versículo para memorizar:** la referencia y una explicación breve de por qué es la llave de la semana.
4. **El mapa de la semana:** qué tema toca cada día, de domingo a jueves, en una frase cada uno.
5. **Preguntas guía:** 2 o 3 preguntas originales para estudiar durante la semana.
6. **Cierre:** invitación a seguir los videos diarios.

### `resumen_viernes` – viernes (550–1100 palabras, 4–7 min)
Es corto y sirve para que alumnos y maestros lleguen preparados al sábado.
1. **Gancho:** la idea más fuerte de la semana.
2. **Repaso exprés:** una idea clave por día, de domingo a jueves.
3. **Hilo conductor:** qué une los cinco días.
4. **Preparación para el sábado:** 2 o 3 preguntas originales para la clase.
5. **Cierre:** anuncia el repaso profundo del sábado.

### `repaso_sabado` – sábado por la mañana (2200–3800 palabras, 15–25 min)
Es el video más profundo de la semana y está pensado para maestros y alumnos antes de la clase.
1. **Gancho**
2. **Repaso general:** las ideas de la semana en orden, más breve que el viernes.
3. **Profundización** (2 o 3 capítulos): contexto histórico y cultural, idiomas originales cuando aporten (solo datos verificables), conexiones con otros libros de la Biblia y respuesta a una pregunta difícil del tema.
4. **Espíritu de Profecía:** 2 o 4 citas breves y verificadas de Elena G. de White sobre el tema, cada una con su referencia en `referencia` y comentada. Sigue las reglas de la sección 1.
5. **Aplicación personal y para la iglesia**
6. **Preguntas para la clase:** originales, para debatir.
7. **Cierre:** anuncia la introducción de la nueva lección esa misma tarde.

## 4. Estilo de narración

- Escribe para el oído: frases de 8 a 20 palabras, segunda persona y tono cálido. Nada de "en este video vamos a…" en la primera frase.
- Los números y referencias se escriben como se pronuncian: "Juan capítulo tres, versículo dieciséis" dentro de `texto`. La forma "Juan 3:16" va en `referencia`, para la tarjeta en pantalla.
- Cada escena debe entenderse sola, porque se narra por separado.
- **Español:** neutro latinoamericano, sin modismos de un solo país.
- **Portugués:** portugués de Brasil nativo, escrito directamente en PT y no traducido literalmente del ES. Los nombres bíblicos siguen la forma de la Almeida (João, Tiago, Isaías).

## 5. SEO

- **Título:** de 60 a 70 caracteres, con la palabra clave al inicio. Patrón: `Lección 3: <Tema del día> | Escuela Sabática <fecha corta>`. En PT: `Lição 3: … | Escola Sabatina`.
- **Descripción:** los primeros 150 caracteres resumen el valor del video. Siguen 2 o 3 párrafos, los pasajes bíblicos y una invitación a suscribirse. Los capítulos y créditos los agrega `metadata.py`.
- **Tags:** entre 10 y 15, con un total de 500 caracteres como máximo. Mezcla tags amplios ("escuela sabática", "lección de escuela sabática") con específicos (tema, libro bíblico, número de lección y trimestre).
- **Hashtags:** 3 como máximo.
- **Miniatura:** `linea1` con 2 a 4 palabras de impacto, `linea2` con 1 a 3 palabras en el color de marca y `etiqueta` del tipo "LECCIÓN 3 · LUNES". No repitas el título.

## 6. Esquema de guion.json

```json
{
  "lang": "es",
  "tipo": "diario",  // intro | diario | resumen_viernes | repaso_sabado
  "trimestre": "2026-T4",
  "leccion": 3,
  "dia": "lunes",
  "fecha": "2026-10-12",
  "tema": "Cómo identificar a un verdadero profeta",
  "version_biblica": "RV1909",
  "color_marca": [212, 168, 83],
  "contenido_sintetico": true,
  "miniatura": {"linea1": "¿Profeta verdadero", "linea2": "o falso?", "etiqueta": "LECCIÓN 3 · LUNES", "imagen": "gancho"},
  "seo": {
    "titulo": "...", "descripcion": "...", "tags": ["..."], "hashtags": ["EscuelaSabatica"],
    "privacidad": "private", "publicar_en": "2026-10-13T10:00:00Z", "lista_id": null
  },
  "escenas": [
    {
      "id": "gancho",
      "capitulo": "Introducción",
      "texto": "Texto narrado...",
      "texto_pantalla": "Idea clave corta (opcional)",
      "referencia": "Deuteronomio 18:22 (opcional)",
      "visual": {"query": "búsqueda en inglés para Pexels"}
    }
  ]
}
```

- `capitulo` se pone solo en las escenas que abren un capítulo de YouTube. Se necesitan al menos 3, y la primera escena siempre lleva uno.
- `visual.query` va en inglés, que da mejores resultados en Pexels. Evita imágenes que representen a Jesús o a profetas como personas identificables; prefiere paisajes bíblicos, rollos, lámparas, desierto, luz y manos sobre una Biblia.
- `publicar_en` usa formato RFC3339 en UTC. Lima es UTC−5, así que las 05:00 de Lima son las 10:00Z.
