"""Fotos reales del catálogo para los productos del Perfil de Empresa de Google (Imexpomundo).
Por cada línea toma hasta 3 productos activos con foto y guarda la primera foto (≥ 400 px) en canales/tecnologia/gbp/.
Sin precios. Uso: python scripts/fotos_gbp.py   (en Actions: el catálogo no es accesible desde la sesión de Claude)
"""
import io
import json
import re
import sys
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from tecnologia_gen import catalogo  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "canales" / "tecnologia" / "gbp"
LINEAS = {
    "refrigeracion": r"freezer|refriger|congelador|exhibidor|conservador|mes[oó]n refriger|enfriador|vitrina",
    "ventus": r"ventus",
    "ilumi": r"ilumi",
    "dakota": r"dakota",
    "maquinas": r"popcorn|pop corn|cremolad|empacador|vac[ií]o|cortador|embutid|ca[nñ]a",
}


def inventario():
    """Categorías y marcas del catálogo (sin precios) para armar la clasificación del Perfil de Empresa."""
    import collections
    todos = catalogo()["todos"]
    cats = collections.Counter((p.get("categoria") or "?") for p in todos if p.get("estado") in ("Activo", "Próximo ingreso"))
    por_cat = collections.defaultdict(collections.Counter)
    for p in todos:
        if p.get("estado") in ("Activo", "Próximo ingreso"):
            por_cat[p.get("categoria") or "?"][p.get("marca") or "?"] += 1
    claves = sorted({k for p in todos[:50] for k in p})
    (OUT / "categorias.json").write_text(json.dumps({"campos": claves, "categorias": [
        {"categoria": c, "productos": n, "marcas": dict(por_cat[c])} for c, n in cats.most_common()]}, ensure_ascii=False, indent=1))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inventario()
    if "--solo-inventario" in sys.argv:
        return
    resumen = {}
    for clave, pat in LINEAS.items():
        n = 0
        for p in catalogo()["productos"]:
            txt = " ".join(str(p.get(k, "")) for k in ("marca", "categoria", "nombre", "descripcion"))
            if not re.search(pat, txt, re.I):
                continue
            for u in p["_fotos"]:
                try:
                    r = requests.get(u, timeout=40)
                    im = Image.open(io.BytesIO(r.content)).convert("RGB")
                except Exception:
                    continue
                if min(im.size) < 400:
                    continue
                n += 1
                im.thumbnail((1200, 1200))
                f = OUT / f"{clave}_{n}.jpg"
                im.save(f, quality=90)
                resumen.setdefault(clave, []).append({"archivo": f.name, "marca": p.get("marca"), "categoria": p.get("categoria"),
                                                      "nombre": p.get("nombre"), "codigo": p.get("codigo")})
                break
            if n >= 3:
                break
        print(clave, n)
    (OUT / "fotos.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
