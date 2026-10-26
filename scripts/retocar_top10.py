"""Retoque de un Top 10 ya publicado: miniatura de impacto + menciones @ + etiquetas y hashtags del conteo.
No re-sube el video ni toca publicado.json.  Uso: python retocar_top10.py <proyecto_dir> --canal <canal>
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from googleapiclient.http import MediaFileUpload  # noqa: E402
from upload import service  # noqa: E402

S = Path(__file__).parent


def main():
    proj = Path(sys.argv[1])
    canal = sys.argv[sys.argv.index("--canal") + 1]
    vid = json.loads((proj / "publicado.json").read_text())["video_id"]
    yt = service(canal)
    v = yt.videos().list(part="snippet", id=vid).execute()["items"][0]
    sn = v["snippet"]
    tmp = Path(tempfile.mkdtemp())
    for f in ("guion.json", "categorias3.json"):
        shutil.copy(proj / f, tmp / f)
    g = json.loads((tmp / "guion.json").read_text())
    g["seo"].update({"descripcion": sn.get("description", ""), "tags": sn.get("tags", []), "hashtags": []})
    (tmp / "guion.json").write_text(json.dumps(g, ensure_ascii=False))
    subprocess.run([sys.executable, str(S / "top10_seo.py"), str(tmp), "--canal", canal], check=True)
    subprocess.run([sys.executable, str(S / "top10_miniatura.py"), str(tmp)], check=True)
    g = json.loads((tmp / "guion.json").read_text())
    desc = g["seo"]["descripcion"]
    nuevos = [h for h in g["seo"]["hashtags"] if f"#{h}".lower() not in desc.lower()]
    if nuevos:
        desc += "\n" + " ".join("#" + h for h in nuevos)
    tags = []
    for t in g["seo"]["tags"]:
        if len(",".join(tags + [t])) <= 500:
            tags.append(t)
    yt.videos().update(part="snippet", body={"id": vid, "snippet": {
        "title": sn["title"], "description": desc[:5000], "tags": tags, "categoryId": sn["categoryId"],
        "defaultLanguage": sn.get("defaultLanguage", "es"), "defaultAudioLanguage": sn.get("defaultAudioLanguage", "es")}}).execute()
    mini = tmp / "salida" / "miniatura.jpg"
    if mini.exists():
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(mini))).execute()
        shutil.copy(mini, proj / "miniatura_impacto.jpg")
    (proj / "retoque_v2.ok").write_text("miniatura sin spoiler + descripción en orden alfabético\n")
    print(f"Retocado https://youtu.be/{vid}: {len(tags)} etiquetas, miniatura={'sí' if mini.exists() else 'no'}")


if __name__ == "__main__":
    main()
