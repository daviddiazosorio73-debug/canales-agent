---
name: youtube-agent-skill
description: Produce videos largos para YouTube sobre la lección de Escuela Sabática (Escola Sabatina) en español y portugués, de punta a punta. Incluye guion original para la semana completa de sábado a sábado (intro del sábado, temas diarios de domingo a jueves, resumen del viernes y repaso del sábado con Espíritu de Profecía), narración con voz IA (ElevenLabs), imágenes, subtítulos, render con FFmpeg, miniatura, SEO y subida a YouTube. Úsala siempre que el usuario pida un video, guion, miniatura, SEO o publicación de la lección de Escuela Sabática, el tema del día, el resumen de la semana, "el video de hoy", /youtube-agent-skill, o cuando hable del canal de YouTube de la lección, aunque no diga "skill".
---

# YouTube Agent – Escuela Sabática (ES/PT)

Pipeline: **guion original → voz → imágenes → render → miniatura → SEO → subida**. Los scripts están en `scripts/` y Claude escribe el guion. Todo el contenido de cada video vive en una carpeta de proyecto.

## Antes de empezar

- Primera vez o error de credenciales: lee `references/setup.md`.
- Antes de escribir cualquier guion, lee `references/guion.md`. Contiene las reglas de derechos y originalidad, que protegen el canal de reclamos de copyright y de la desmonetización por contenido "inauténtico", además de la estructura y el esquema JSON.

## Formatos

La semana de la lección va de sábado a sábado. Hay un video cada día y el sábado lleva dos.

| Día | Tipo | Contenido | Duración |
|---|---|---|---|
| Sábado (tarde) | `intro` | Introducción de la nueva lección: panorama, versículo para memorizar y preguntas que guiarán la semana | 6 min |
| Domingo a jueves | `diario` | Comentario del tema de cada día | 8–12 min |
| Viernes | `resumen_viernes` | Resumen breve de la semana (domingo a jueves) y preparación para el sábado | 8–12 min |
| Viernes (tarde) | `repaso_sabado` | Repaso general de la lección, profundización del comentario y Espíritu de Profecía | 25–45 min |

Cada viernes se publican dos videos: por la tarde, el `repaso_sabado` de la lección que termina; el sábado por la tarde, el `intro` de la lección siguiente.

Cada video se produce dos veces, en ES y en PT. Cada idioma va a su propio canal y lleva su propio guion escrito de forma nativa, no traducido palabra por palabra, porque la audiencia nota la diferencia.

## Flujo

### 1. Identificar la lección y el día
Busca en la web el título de la lección y el tema del día para la fecha pedida. Las fuentes útiles son sabbath.school, ssnet.org y los sitios de ACES y CPB. Si el título en ES o PT no se puede verificar, usa una descripción del tema en vez de inventar el título oficial y avísalo. Toma de la lección solo el número, el título, el tema y los pasajes bíblicos; el texto de la lección no se usa (ver guion.md).

### 2. Crear el proyecto
```
proyectos/<AAAA-MM-DD>-<lang>-<tipo>/guion.json
```
Por ejemplo: `proyectos/2026-10-12-es-diario/guion.json`. Escribe el guion siguiendo `references/guion.md`.

### 3. Revisión humana
Muestra al usuario un resumen breve: título, gancho, las 2 o 3 ideas, la aplicación y la miniatura. Espera su aprobación antes de sintetizar la voz, que consume créditos. Esta revisión también es la evidencia de autoría humana ante YouTube.

En una ejecución programada o desatendida, produce el video completo y súbelo en **privado**. Avisa que está pendiente de revisión, nunca lo publiques en público sin aprobación.

### 4. Producir
```bash
cd <skill>/scripts
python pipeline.py <proyecto>                 # completo, con ElevenLabs y Pexels
python pipeline.py <proyecto> --mock --offline --borrador   # prueba sin API keys
python pipeline.py <proyecto> --subir         # además sube a YouTube
```
Cada paso también se puede ejecutar por separado: `validate`, `tts`, `visuals`, `render`, `thumbnail`, `metadata` y `upload`. `tts.py` no repite escenas que ya tienen audio, así que si editas una escena borra solo `audio/<id>.*`.

Para usar imágenes propias o generadas con Canva, guárdalas como `imagenes/<id_escena>.jpg` antes de `visuals.py`, que las respeta. Para la miniatura, una imagen guardada como `miniatura_base.jpg` se usa como fondo.

### 5. Verificar antes de entregar
- Extrae 3 fotogramas y míralos: inicio, mitad y una tarjeta de texto.
  ```bash
  ffmpeg -ss 5 -i salida/video.mp4 -frames:v 1 tmp/f1.jpg
  ```
- Mira `salida/miniatura.jpg`.
- Revisa los AVISOS de `metadata.py`, como capítulos o límites de caracteres.
- Confirma la duración con `ffprobe` y que no haya silencios largos.

### 6. Entregar
Envía al usuario `video.mp4`, `miniatura.jpg` y `metadata.json`, o el enlace de `publicado.json` si se subió. Resume en una línea: duración, título y estado (privado o programado para una fecha).

## Calendario semanal sugerido (hora de Lima, UTC−5)

| Día | Video | Publicación |
|---|---|---|
| Viernes | `repaso_sabado` de la lección que termina | 18:00 |
| Sábado | `intro` de la lección nueva | 18:00 |
| Domingo a jueves | `diario` del tema de ese día | 04:00 |
| Viernes | `resumen_viernes` | 04:00 |

Para automatizarlo, crea una tarea programada que genere los guiones de la semana (7 videos por idioma) y los deje en revisión.

## Salidas de un proyecto
```
<proyecto>/
  guion.json
  audio/<id>.mp3 + <id>.align.json
  imagenes/<id>.jpg
  creditos.json
  salida/
    video.mp4
    subtitulos.srt
    miniatura.jpg
    capitulos.json
    metadata.json
    publicado.json
```
