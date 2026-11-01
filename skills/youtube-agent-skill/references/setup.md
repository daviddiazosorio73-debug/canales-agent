# Configuración inicial (una sola vez)

## 1. Dependencias
```bash
# FFmpeg con libass (Linux: apt install ffmpeg; Mac: brew install ffmpeg; Windows: winget install ffmpeg)
pip install pillow requests edge-tts google-api-python-client google-auth-oauthlib
```

## 2. Variables de entorno
| Variable | Uso |
|---|---|
| `EDGE_VOICE_ES` / `EDGE_VOICE_PT` | Opcional. Voz gratis por idioma; por defecto `es-MX-JorgeNeural` y `pt-BR-AntonioNeural` |
| `EDGE_RATE` | Opcional. Ritmo de la voz; por defecto `-4%` |
| `PEXELS_API_KEY` | Imágenes gratuitas (pexels.com/api) |

**Voz:** gratis con edge-tts (no necesita cuenta ni clave). La voz clonada del Fundador (Chatterbox, gratis) solo funciona en el motor canales-agent. No se usan servicios de pago sin autorización del Fundador.

## 3. YouTube Data API (por canal ES y PT)
1. En Google Cloud Console, crea un proyecto y habilita **YouTube Data API v3**.
2. Configura la pantalla de consentimiento OAuth y agrega tu correo como usuario de prueba.
3. Crea Credenciales → ID de cliente OAuth → **App de escritorio** y descarga el JSON en `~/.yt-agent/client_secret.json`.
4. La primera vez que ejecutes `upload.py --canal es` se abre el navegador. Elige el canal en español. Repite con `--canal pt` para el canal en portugués. Los tokens se guardan en `~/.yt-agent/token_<canal>.json`.

**Importante:** Google restringe a "privado" los videos subidos por API desde proyectos no verificados creados después del 28 de julio de 2020. Mientras tanto, el flujo sube en privado y tú publicas desde YouTube Studio. Para publicar o programar automáticamente, solicita la auditoría de la API (YouTube API Services – Audit and Quota Extension Form).

## 4. Recursos de marca (opcionales)
- `assets/logo.png`: logo con fondo transparente, se muestra arriba a la derecha.
- `assets/musica/*.mp3`: música libre de derechos (por ejemplo, de la Biblioteca de audio de YouTube). El volumen baja automáticamente cuando hay voz.
- `assets/fonts/*Bold*.ttf` y `*Regular*.ttf`: tipografía de marca, por ejemplo Montserrat (licencia OFL).
- `color_marca` en guion.json, en RGB.
