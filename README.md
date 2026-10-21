# canales-agent

Producción y publicación automática y gratuita de 4 canales de YouTube:
MayorDom · Maestro de Escuela Sabática (ES) · Escola Sabatina (PT) · Top 10 Redes.

## Cómo funciona
1. **Guiones**: cada domingo una tarea programada de Claude escribe los guiones de la semana en `canales/<canal>/proyectos/<fecha>-.../guion.json` y los sube aquí.
2. **Motor** (`.github/workflows/producir.yml`): cada hora GitHub Actions toma lo que se publica en las próximas 36 h, genera voz (gratis), imágenes, render, miniatura y SEO, y lo sube a YouTube programado.
3. **Estado**: al subir, se guarda `publicado.json` junto al guion; `reporte.md` muestra la última corrida.

## Secretos (Settings → Secrets and variables → Actions)
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `REFRESH_TOKEN_MAYORDOM`, `REFRESH_TOKEN_ES_SABATICA`, `REFRESH_TOKEN_PT_SABATINA`, `REFRESH_TOKEN_TOP10`, opcional `PEXELS_API_KEY`.

## Activar un canal
En `canales.json` pon `"activo": true` y agrega su secreto.
