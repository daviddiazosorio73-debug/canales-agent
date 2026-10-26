"""Une las ediciones del Top 10 de la semana en una lista "Vuelta al mundo" que termina en el Top 10 Mundial
y agrega a cada descripción el enlace a la siguiente parada (y a la lista completa). Idempotente.
Uso: python top10_cadena.py   (después de producir las ediciones; token de top10-redes)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANAL = "top10-redes"
TXT = {"es": ("▶ Siguiente parada", "📺 Vuelta al mundo completa (termina en el Top 10 Mundial)"),
       "en": ("▶ Next stop", "📺 Full world tour (ends with the global Top 10)"),
       "pt": ("▶ Próxima parada", "📺 Volta ao mundo completa (termina no Top 10 Mundial)"),
       "fr": ("▶ Prochaine étape", "📺 Tour du monde complet (se termine par le Top 10 mondial)")}


def main():
    semanas = sorted((ROOT / "canales" / CANAL).glob("semana_*.json"))
    if not semanas:
        return
    sp = semanas[-1]
    S = json.loads(sp.read_text())
    eds = []
    for rel in S["orden"]:
        d = ROOT / rel
        if (d / "publicado.json").exists():
            g = json.loads((d / "guion.json").read_text())
            eds.append((json.loads((d / "publicado.json").read_text())["video_id"], g))
    if len(eds) < 2:
        print("cadena: aún no hay suficientes ediciones publicadas")
        return
    yt = service(CANAL)
    n = S["semana"].split("W")[-1]
    if not S.get("playlist"):
        S["playlist"] = yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": f"Top 10 · Vuelta al mundo / World Tour · Semana {n}",
                        "description": "Oceanía → Asia → África → Europa → América → Top 10 Mundial. Mírala en orden. #Top10RS"},
            "status": {"privacyStatus": "public"}}).execute()["id"]
        S["en_lista"] = []
    pl = S["playlist"]
    for i, (vid, g) in enumerate(eds):
        if vid not in S["en_lista"]:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pl, "position": min(i, len(S["en_lista"])), "resourceId": {"kind": "youtube#video", "videoId": vid}}}).execute()
            S["en_lista"].append(vid)
    S.setdefault("enlazados", [])
    for i, (vid, g) in enumerate(eds):
        sig = eds[i + 1] if i + 1 < len(eds) else None
        clave = f"{vid}>{sig[0] if sig else 'fin'}"
        if clave in S["enlazados"]:
            continue
        v = yt.videos().list(part="snippet,localizations", id=vid).execute()["items"][0]
        sn = v["snippet"]

        def bloque(lang, base):
            a, b = TXT.get(lang, TXT["en"])
            extra = ""
            if sig:
                extra += f"{a}: {sig[1]['continente']} → https://youtu.be/{sig[0]}?list={pl}\n"
            extra += f"{b}: https://www.youtube.com/playlist?list={pl}\n\n"
            base = base.split("\n\n", 1)[-1] if base.startswith(("▶", "📺")) else base
            return (extra + base)[:5000]

        body = {"id": vid, "snippet": {"title": sn["title"], "categoryId": sn["categoryId"], "tags": sn.get("tags", []),
                                       "defaultLanguage": sn.get("defaultLanguage", g["lang"]),
                                       "description": bloque(g["lang"], sn.get("description", ""))}}
        partes = "snippet"
        if v.get("localizations"):
            body["localizations"] = {l: {"title": x["title"], "description": bloque(l, x.get("description", ""))}
                                     for l, x in v["localizations"].items()}
            partes += ",localizations"
        yt.videos().update(part=partes, body=body).execute()
        S["enlazados"].append(clave)
        print(f"+ enlazado {g['edicion']} → {sig[1]['edicion'] if sig else 'fin'}")
    sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
