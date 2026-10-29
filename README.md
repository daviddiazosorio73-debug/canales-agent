# canales-agent

Producción y publicación automática y gratuita de 5 canales de YouTube:
MayorDom · Maestro de Escuela Sabática (ES, solo Shorts) · Escola Sabatina (PT, solo Shorts) · Top 10 Redes Sociales · Cryptuline (pendiente).

## Cómo funciona
1. **Guiones**: cada sábado a las 19:52 (Lima) una tarea programada de Claude (skill director-canales); el libreto del Top 10, los miércoles a las 00:10 escribe los guiones de la semana en `canales/<canal>/proyectos/<fecha>-.../guion.json` y los sube aquí.
2. **Motor** (`.github/workflows/producir.yml`): cada hora GitHub Actions toma lo que se publica en las próximas 36 h, genera voz (gratis), imágenes, render, miniatura y SEO, y lo sube a YouTube programado.
3. **Estado**: al subir, se guarda `publicado.json` junto al guion; `reporte.md` muestra la última corrida.

## Secretos (Settings → Secrets and variables → Actions)
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REFRESH_TOKEN_MAYORDOM`, `REFRESH_TOKEN_ES_SABATICA`, `REFRESH_TOKEN_PT_SABATINA`, `REFRESH_TOKEN_TOP10`, `REFRESH_TOKEN_CRYPTULINE`, `VOICE_KEY` (voz del Fundador); opcionales `PEXELS_API_KEY` y `META_PAGE_TOKEN_<CANAL>`.

## Activar un canal
En `canales.json` pon `"activo": true` y agrega su secreto.
