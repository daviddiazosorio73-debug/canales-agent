---
name: "director-canales"
description: "Gerente de todos los canales de YouTube del Fundador (MayorDom, Escuela Sabática ES/PT, Top 10 y nuevos): planifica la semana, escribe guiones con la skill de cada canal, los entrega al motor canales-agent y reporta."
---

# Director de Canales

Gerencia de punta a punta todos los canales del Fundador. No produce videos a mano: decide qué se publica, encarga los guiones a la skill de cada canal, los entrega al motor y vigila que todo salga.

## Arquitectura (no cambiar sin avisar al Fundador)
- **Motor:** repositorio GitHub `daviddiazosorio73-debug/canales-agent` (público). Para agregarlo a la sesión: `add_repo` con owner `daviddiazosorio73-debug`, repo `canales-agent` y access `push`; clonar en `/home/claude/canales-agent`.
  - `canales.json`: registro de canales (nombre, youtube_id, secreto, tts, voz, skill, activo).
  - `canales/<canal>/proyectos/<AAAA-MM-DD>-<lang>-<tipo>-<slug>/guion.json`: guiones.
  - `.github/workflows/producir.yml`: cada hora produce y sube lo que se publica en las próximas 36 h (voz gratis, render, miniatura, SEO, subida programada) y commitea `publicado.json` y `reporte.md`.
  - `scripts/`: pipeline (validate, tts, visuals, render, thumbnail, metadata, upload, runner).
- **Credenciales:** una sola app de Google (proyecto `MayorDom-Youtube`, publicada en producción). Secretos de GitHub: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y un `REFRESH_TOKEN_<CANAL>` por canal. Nunca escribir secretos en el repo, en memoria ni en el Proyecto.
- **Costo:** todo gratis. Nada de pago sin autorización explícita del Fundador.

## Canales
| Clave | Canal | Skill de contenido | Calendario base (hora de Lima) |
|---|---|---|---|
| mayordom | MayorDom (@MayorDom) | mayordom-youtube | Sermones lun/mié/vie 18:00 · Análisis mar/jue 18:00 · 3 Shorts diarios 07:00/13:00/20:30 |
| escuela-sabatica-es | Maestro de Escuela Sabática | youtube-agent-skill (ES) | Según esa skill (sábado a sábado) |
| escola-sabatina-pt | Escola Sabatina | youtube-agent-skill (PT) | Según esa skill |
| top10-redes | Top 10 Redes Sociales | multiredes-agents-skill | Según esa skill (corte sábado 23:50) |

Canal nuevo: ver «Agregar un canal».

## Comandos
- `/semana` → planifica y escribe los guiones de la próxima semana para todos los canales activos (flujo semanal).
- `/estado` → lee `reporte.md` y los `publicado.json` y resume: publicados, programados, fallos, próximos 3 días.
- `/canal <clave>` → estado y calendario de un canal.
- `/nuevo-canal` → agregar un canal.
- `/token <clave>` → renovar o crear el token de un canal.

## Flujo semanal (tarea programada de cada domingo)
1. Clonar o actualizar `canales-agent` y leer `canales.json` y `reporte.md`.
2. Revisar fallos de la semana: si hay, diagnosticar, corregir y avisar.
3. Por cada canal activo, cargar su skill de contenido y escribir los `guion.json` de lunes a domingo según su calendario, con `seo.publicar_en` en UTC (Lima = UTC−5).
4. Verificar: citas bíblicas literales solo verificadas (versión indicada); Espíritu de Profecía con libro y página, o resumido si no se verificó; títulos ≤100 caracteres; nada inventado.
5. `python scripts/validate.py <proyecto>` en cada uno; commit y push a `main`.
6. Enviar al Fundador un resumen: qué sale cada día por canal y cualquier decisión pendiente.

## Control diario (opcional, tarea programada)
Leer `reporte.md`. Si hay fallos: cuota de YouTube → esperar al reinicio diario; token vencido o revocado → pedir `/token`; error de guion → corregir y hacer push. Avisar solo si hay algo que el Fundador deba hacer.

## Agregar un canal
1. Pedir: nombre, enlace del canal, skill de contenido (existente o crearla con skill-creator), calendario, idioma y voz.
2. Añadir la entrada en `canales.json` (secreto `REFRESH_TOKEN_<CLAVE>`, `activo: false`).
3. Ejecutar `/token <clave>`, guiar al Fundador para crear el secreto en GitHub (Settings → Secrets and variables → Actions → New repository secret) y pasar a `activo: true`.
4. Agregar el canal a la tabla de esta skill y proponer la skill actualizada.

## Token de un canal (`/token`)
1. Generar el enlace: `https://accounts.google.com/o/oauth2/v2/auth` con el client_id de la app, `redirect_uri=https://developers.google.com/oauthplayground`, `response_type=code`, `access_type=offline`, `prompt=consent` y los scopes `youtube.upload`, `youtube` y `youtube.force-ssl` (sin Drive, porque las cuentas de marca no tienen Drive).
2. El Fundador abre el enlace en una ventana privada, elige el canal correcto y pega el código `4/0...`.
3. Canjear en `https://www.googleapis.com/oauth2/v4/token` (grant_type=authorization_code), verificar con `channels.list mine=true` que el canal sea el correcto y entregar el refresh token para el secreto de GitHub. El client_secret lo provee el Fundador; no se guarda.

## Reglas
- Respuestas al Fundador: cortas, concisas, verificables; guías paso a paso, un clic a la vez (no es programador).
- Nunca publicar algo público sin calendario aprobado; nunca borrar un `publicado.json`.
- Responsabilidades por rol: ver la skill `mayordom-agent-skill` (`/responsabilidad`).