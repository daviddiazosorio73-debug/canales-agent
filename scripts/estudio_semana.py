"""Rutina semanal del Fundador en YouTube Studio (sin Claude, sin API): escribe canales/ESTUDIO_SEMANA.md con
enlaces directos, canal por canal, para lo que la API no permite hacer:
  1. Fijar el comentario con pregunta (el motor ya lo publica)   2. Pantalla final (importar de un video)
  3. Revisar subtítulos (una muestra por canal)                   4. Comprobar 4K (insignia y Top 10)
  5. Escuchar 1 insignia/largo y 1 Short por canal (ajustar voz y emociones)
Cubre los videos largos publicados en los últimos 7 días. Uso: python scripts/estudio_semana.py
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = "https://studio.youtube.com/video/{}"
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def main():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=7)
    L = [f"# Rutina semanal en YouTube Studio — {ahora - timedelta(hours=5):%Y-%m-%d %H:%M} (Lima)\n",
         "Orden por video: ① fijar comentario → ② pantalla final → ③ subtítulos (1 por canal) → ④ 4K si dice «sí».",
         "Escuchar: 1 largo y 1 Short por canal; anota en el chat qué voz o emoción ajustar.\n"]
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo"):
            continue
        largos, shorts = [], []
        for pj in sorted((ROOT / "canales" / canal / "proyectos").glob("*/publicado.json")):
            g = json.loads((pj.parent / "guion.json").read_text())
            pub = (g.get("seo") or {}).get("publicar_en")
            if not pub:
                continue
            t = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if not desde <= t <= ahora:
                continue
            vid = json.loads(pj.read_text()).get("video_id")
            fila = (t, vid, g.get("seo", {}).get("titulo", pj.parent.name)[:60], g)
            (shorts if g.get("tipo") == "short" else largos).append(fila)
        L.append(f"## {cfg['nombre']}\n")
        if largos:
            L.append("| Fecha | Video | ① Comentario | ② Pantalla final | ③ Subtítulos | ④ 4K |")
            L.append("|---|---|---|---|---|---|")
            for k, (t, vid, tit, g) in enumerate(sorted(largos)):
                cuatro_k = "sí" if (g.get("voz_fundador") or g.get("res_4k") or g.get("tipo") == "top10") else "—"
                L.append(f"| {DIAS[(t - timedelta(hours=5)).weekday()]} {t - timedelta(hours=5):%d} | [{tit}](https://youtu.be/{vid}) | [fijar]({S.format(vid)}/comments) | "
                         f"[editar]({S.format(vid)}/edit) | " + (f"[revisar]({S.format(vid)}/translations)" if k == 0 else "—")
                         + f" | {cuatro_k} |")
        else:
            L.append("Sin videos largos publicados esta semana.")
        oir = [f for f in sorted(largos) if f[3].get("voz_fundador") or f[3].get("insignia")] or sorted(largos)
        esc = []
        if oir:
            esc.append(f"[largo: {oir[-1][2]}](https://youtu.be/{oir[-1][1]})")
        if shorts:
            s = sorted(shorts)[-1]
            esc.append(f"[Short: {s[2]}](https://youtube.com/shorts/{s[1]})")
        L.append("\n**Escuchar:** " + (" · ".join(esc) if esc else "—") + "\n")
    (ROOT / "canales" / "ESTUDIO_SEMANA.md").write_text("\n".join(L) + "\n")
    print("OK canales/ESTUDIO_SEMANA.md")


if __name__ == "__main__":
    main()
