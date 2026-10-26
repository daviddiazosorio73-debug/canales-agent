"""Listas de reproducción automáticas (corre en Actions después de runner.py).

canales.json → "listas": {"<tipo>": "<nombre de la lista>"} por canal (o seo.lista_nombre en el guion).
Para cada proyecto con publicado.json: crea la lista si no existe (pública) y agrega el video si falta.
Salta los videos privados que no están programados (p. ej. ediciones retiradas).
Guarda ids en canales/<canal>/listas.json (no toca ningún publicado.json).
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from runner import token_file  # noqa: E402
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    canales = json.loads((ROOT / "canales.json").read_text())
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo"):
            continue
        mapa = cfg.get("listas", {})
        candidatos = []
        for gj in sorted((ROOT / "canales" / canal / "proyectos").glob("*/guion.json")):
            pub = gj.parent / "publicado.json"
            if not pub.exists():
                continue
            g = json.loads(gj.read_text())
            nombre = g.get("seo", {}).get("lista_nombre") or mapa.get(g.get("tipo"))
            if nombre:
                candidatos.append((nombre, json.loads(pub.read_text())["video_id"]))
        if not candidatos:
            continue
        ruta = ROOT / "canales" / canal / "listas.json"
        L = json.loads(ruta.read_text()) if ruta.exists() else {"ids": {}, "videos": {}}
        pendientes = [(n, v) for n, v in candidatos if v not in L["videos"].get(n, [])]
        if not pendientes or not token_file(canal, cfg):
            continue
        yt = service(canal)
        estado = {}
        ids = list({v for _, v in pendientes})
        for i in range(0, len(ids), 50):
            for it in yt.videos().list(part="status", id=",".join(ids[i:i + 50])).execute().get("items", []):
                estado[it["id"]] = it["status"]
        for nombre, vid in pendientes:
            st = estado.get(vid)
            if not st or (st.get("privacyStatus") == "private" and not st.get("publishAt")):
                continue
            if nombre not in L["ids"]:
                existentes = yt.playlists().list(part="snippet", mine=True, maxResults=50).execute().get("items", [])
                pl = next((p["id"] for p in existentes if p["snippet"]["title"] == nombre), None)
                if not pl:
                    pl = yt.playlists().insert(part="snippet,status", body={
                        "snippet": {"title": nombre, "description": cfg.get("listas_desc", {}).get(nombre, "")},
                        "status": {"privacyStatus": "public"}}).execute()["id"]
                    print(f"+ lista creada: {nombre} ({pl})")
                L["ids"][nombre] = pl
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": L["ids"][nombre], "position": 0,
                "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            L["videos"].setdefault(nombre, []).append(vid)
            print(f"+ {canal}: {vid} → {nombre}")
        ruta.write_text(json.dumps(L, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # una lista nunca debe tumbar la corrida
        print("listas: aviso:", e)
        if os.environ.get("LISTAS_ESTRICTO"):
            raise
