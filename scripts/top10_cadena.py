"""Une las ediciones del Top 10 de la semana en una lista "Vuelta al mundo" que termina en el Top 10 Mundial
y agrega a cada descripción el enlace a la siguiente parada (y a la lista completa). Idempotente.
Uso: python top10_cadena.py   (después de producir las ediciones; token de top10-redes)
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANAL = "top10-redes"
TXT = {"es": ("▶ Siguiente parada", "📺 Vuelta al mundo completa (termina en el Top 10 Mundial)"),
       "en": ("▶ Next stop", "📺 Full world tour (ends with the global Top 10)"),
       "pt": ("▶ Próxima parada", "📺 Volta ao mundo completa (termina no Top 10 Mundial)"),
       "fr": ("▶ Prochaine étape", "📺 Tour du monde complet (se termine par le Top 10 mondial)")}


def ejecuta(req, intentos=6):
    """YouTube responde a veces 409 SERVICE_UNAVAILABLE / 5xx en inserciones seguidas: reintenta con espera."""
    from googleapiclient.errors import HttpError
    for k in range(intentos):
        try:
            return req.execute()
        except HttpError as e:
            if e.resp.status in (409, 500, 503) and k < intentos - 1:
                time.sleep(5 * (k + 1))
                continue
            raise


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
    titulo = f"Top 10 · Vuelta al mundo / World Tour · Semana {n}"
    if not S.get("playlist"):
        # reutiliza la lista si ya se creó en una corrida que se cortó (evita duplicados)
        previas = [p for p in ejecuta(yt.playlists().list(part="snippet,contentDetails", mine=True, maxResults=50)).get("items", [])
                   if p["snippet"]["title"] == titulo]
        if previas:
            previas.sort(key=lambda p: -p["contentDetails"]["itemCount"])
            S["playlist"] = previas[0]["id"]
            S["en_lista"] = [it["snippet"]["resourceId"]["videoId"] for it in ejecuta(yt.playlistItems().list(
                part="snippet", playlistId=S["playlist"], maxResults=50)).get("items", [])]
            if len(previas) > 1:
                print("cadena: aviso, listas duplicadas sin usar:", [p["id"] for p in previas[1:]])
        else:
            S["playlist"] = ejecuta(yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": titulo,
                            "description": "Oceanía → Asia → África → Europa → América → Top 10 Mundial. Mírala en orden. #Top10RS"},
                "status": {"privacyStatus": "public"}}))["id"]
            S["en_lista"] = []
            time.sleep(5)
        sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))
    pl = S["playlist"]
    for i, (vid, g) in enumerate(eds):
        if vid not in S["en_lista"]:
            ejecuta(yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pl, "position": min(i, len(S["en_lista"])), "resourceId": {"kind": "youtube#video", "videoId": vid}}}))
            S["en_lista"].append(vid)
            sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))
            time.sleep(2)
    S.setdefault("enlazados", [])
    for i, (vid, g) in enumerate(eds):
        sig = eds[i + 1] if i + 1 < len(eds) else None
        clave = f"{vid}>{sig[0] if sig else 'fin'}"
        if clave in S["enlazados"]:
            continue
        v = ejecuta(yt.videos().list(part="snippet,localizations", id=vid))["items"][0]
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
        ejecuta(yt.videos().update(part=partes, body=body))
        S["enlazados"].append(clave)
        sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))
        print(f"+ enlazado {g['edicion']} → {sig[1]['edicion'] if sig else 'fin'}")
    sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
