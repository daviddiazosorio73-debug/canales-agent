"""Índice de la lección de Escuela Sabática (sin Claude): toma los TEMAS DEL DÍA de la lección de la semana
desde https://escuelasabaticamaestros.com (fuente indicada por el Fundador) y los guarda en
investigacion/leccion_<año>T<n>.json, que usa validate.py. Solo guarda títulos y fechas; nunca el texto de la lección.

Uso: python scripts/leccion_indice.py [URL_de_la_lección] [--probar]   (sin URL: la lección más reciente de la portada)
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITIO = "https://escuelasabaticamaestros.com/"
MESES = {m: i for i, m in enumerate(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                     "septiembre", "octubre", "noviembre", "diciembre"], 1)}
DIAS = "Sábado|Domingo|Lunes|Martes|Miércoles|Jueves|Viernes"


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (canales-agent; indice de temas)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def lineas(htm):
    htm = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", htm, flags=re.S | re.I)
    htm = re.sub(r"<h[1-6][^>]*>", "\n## ", htm, flags=re.I)
    htm = re.sub(r"</?(p|div|br|h[1-6]|li|section|article|header|span)[^>]*>", "\n", htm, flags=re.I)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", htm))
    return [re.sub(r"\s+", " ", x).strip() for x in txt.split("\n") if x.strip()]


def ultima_leccion(portada):
    """URL de la lección más reciente enlazada en la portada (absoluta o relativa); None si la portada ya es la lección."""
    urls = set(re.findall(r'href="((?:https://escuelasabaticamaestros\.com)?/(\d{4})/(\d{2})/(\d{2})/leccion-\d+-[^"#?]+)"', portada))
    if not urls:
        return None
    u = max(urls, key=lambda u: (u[1], u[2], u[3]))[0]
    return u if u.startswith("http") else SITIO.rstrip("/") + u


def parsear(htm):
    L = lineas(htm)
    num = next((int(m.group(1)) for x in L if (m := re.match(r"Lecci[oó]n (\d+)\s*[·\-–]", x))), None)
    m_sab = next((m for x in L if (m := re.search(r"Para el S[aá]bado (\d{1,2}) de (\w+) de (\d{4})", x))), None)
    if not num or not m_sab:
        sys.exit("No pude leer el número de lección o la fecha «Para el Sábado …».")
    anio_clase = int(m_sab.group(3))
    i0 = next((i for i, x in enumerate(L) if re.match(r"Lecci[oó]n \d+\s*[·\-–]", x)), 0)
    titulo = next((x[3:] for x in L[i0:] if x.startswith("## ") and len(x) > 4 and "Escuela Sab" not in x), "")
    dias = {}
    for i, x in enumerate(L):
        m = re.fullmatch(rf"({DIAS}) (\d{{1,2}})(?:\.?\s?[°º])? de ([a-záéíóú]+)", x, flags=re.I)
        if not m or m.group(3).lower() not in MESES:
            continue
        sig = next((y for y in L[i + 1:i + 4] if y.startswith("## ")), None)
        if not sig:
            continue
        mes = MESES[m.group(3).lower()]
        anio = anio_clase - 1 if (mes == 12 and MESES.get(m_sab.group(2).lower()) == 1) else anio_clase
        dias[date(anio, mes, int(m.group(2))).isoformat()] = (m.group(1).capitalize(), sig[3:].strip())
    if len(dias) < 6:
        sys.exit(f"Solo encontré {len(dias)} días; la página cambió de formato. Revisión manual.")
    return num, titulo, dias


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        url, htm = args[0], bajar(args[0])
    else:
        portada = bajar(SITIO)
        url = ultima_leccion(portada) or SITIO
        htm = portada if url == SITIO else bajar(url)
    num, titulo, dias = parsear(htm)
    if "--probar" in sys.argv:  # solo muestra lo leído, no guarda
        print(f"Lección {num}: {titulo} ({url})")
        for f, (d, t) in sorted(dias.items()):
            print(f"  {f} {d}: {t}")
        return
    primero = min(dias)
    anio, mes = int(primero[:4]), int(primero[5:7])
    trimestre = f"{anio}T{(mes - 1) // 3 + 1}"
    p = ROOT / "investigacion" / f"leccion_{trimestre}.json"
    idx = json.loads(p.read_text()) if p.exists() else {"trimestre": trimestre, "fuentes": [], "fechas": {}}
    if url not in idx["fuentes"]:
        idx["fuentes"].append(url)
    cambios = 0
    for f, (dia_sem, tema) in sorted(dias.items()):
        if dia_sem == "Sábado":
            tema = f"{tema} (versículo para memorizar)"
        actual = idx["fechas"].get(f) or {}
        if actual.get("dia") and actual.get("leccion") == num:
            continue  # ya verificado: no se pisa
        idx["fechas"][f] = dict(actual, leccion=num, titulo=titulo or actual.get("titulo"), dia=tema)
        cambios += 1
        print(f"+ {f} · lección {num} · {tema}")
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    print(f"OK {p.name}: {cambios} días nuevos (lección {num}, {url})")


if __name__ == "__main__":
    main()
