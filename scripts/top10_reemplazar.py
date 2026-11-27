"""Cierra el reemplazo de ediciones rehechas (top10_rehacer.py), solo cuando la nueva YA está subida:
  1) borra de YouTube el video viejo y lo saca de las listas del canal;
  2) en los Shorts del podio cambia el enlace viejo por el nuevo (guion si no se subió; videos.update si ya se subió);
  3) deja la semana apuntando a las carpetas nuevas para que top10_cadena.py rehaga la «Vuelta al mundo».
Nunca borra carpetas ni publicado.json: anota «reemplazado.json» en la carpeta vieja. Idempotente.
Uso: python top10_reemplazar.py <semana_json>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload import service  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CANAL = "top10-redes"
PROY = ROOT / "canales" / CANAL / "proyectos"


def main():
    sp = ROOT / sys.argv[1]
    S = json.loads(sp.read_text())
    nuevas = S.get("orden_v2") or []
    yt = service(CANAL)
    cambios = {}
    for rel in nuevas:
        d = ROOT / rel
        if not (d / "publicado.json").exists():
            print("aún no sube:", d.name)
            continue
        g = json.loads((d / "guion.json").read_text())
        vieja = ROOT / g["reemplaza"]
        nuevo = json.loads((d / "publicado.json").read_text())
        viejo = json.loads((vieja / "publicado.json").read_text())
        cambios[viejo["url"]] = nuevo["url"]
        if (vieja / "reemplazado.json").exists():
            continue
        try:
            yt.videos().delete(id=viejo["video_id"]).execute()
            print("- borrado", viejo["video_id"], vieja.name)
        except Exception as ex:
            print("  no se pudo borrar", viejo["video_id"], str(ex)[:120])
            if "notFound" not in str(ex) and "404" not in str(ex):
                continue
        (vieja / "reemplazado.json").write_text(json.dumps({"por": rel, "video_nuevo": nuevo["video_id"]}, indent=1))
    if not cambios:
        return
    # listas del canal: fuera los videos borrados
    viejos_ids = {u.rsplit("/", 1)[-1] for u in cambios}
    tok = None
    while True:
        r = yt.playlists().list(part="id", mine=True, maxResults=50, pageToken=tok).execute()
        for pl in r.get("items", []):
            t2 = None
            while True:
                it = yt.playlistItems().list(part="snippet", playlistId=pl["id"], maxResults=50, pageToken=t2).execute()
                for x in it.get("items", []):
                    if x["snippet"]["resourceId"].get("videoId") in viejos_ids:
                        try:
                            yt.playlistItems().delete(id=x["id"]).execute()
                        except Exception:
                            pass
                t2 = it.get("nextPageToken")
                if not t2:
                    break
        tok = r.get("nextPageToken")
        if not tok:
            break
    # Shorts del podio: enlace a la edición nueva
    for gj in PROY.glob("*short-top10*/guion.json"):
        g = json.loads(gj.read_text())
        desc = g.get("seo", {}).get("descripcion", "")
        nd = desc
        for a, b in cambios.items():
            nd = nd.replace(a, b)
        if nd == desc:
            continue
        g["seo"]["descripcion"] = nd
        gj.write_text(json.dumps(g, ensure_ascii=False, indent=2))
        pub = gj.parent / "publicado.json"
        if pub.exists():
            vid = json.loads(pub.read_text())["video_id"]
            try:
                v = yt.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]
                d2 = v["description"]
                for a, b in cambios.items():
                    d2 = d2.replace(a, b)
                yt.videos().update(part="snippet", body={"id": vid, "snippet": {"title": v["title"], "description": d2,
                                                                                 "categoryId": v["categoryId"], "tags": v.get("tags", [])}}).execute()
                print("~ short actualizado", gj.parent.name)
            except Exception as ex:
                print("  short", gj.parent.name, str(ex)[:100])
        else:
            print("~ guion de short actualizado", gj.parent.name)
    # la semana pasa a las carpetas nuevas; la cadena se rehace sola
    if all((ROOT / r / "publicado.json").exists() for r in nuevas) and S.get("orden") != nuevas:
        S["orden_v1"], S["orden"] = S["orden"], nuevas
        S["en_lista"], S["enlazados"] = [x for x in S.get("en_lista", []) if x not in viejos_ids], []
    sp.write_text(json.dumps(S, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
