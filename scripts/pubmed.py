"""Investigación científica semanal (gratis, PubMed/NCBI E-utilities) para canales con canales/<canal>/ruta.json.
Escribe investigacion/<canal>_pubmed.md con los estudios más recientes del tema del mes: PMID, año, revista,
tipo de publicación, título y resumen recortado. Claude escribe los libretos SOLO con estas fuentes (citando PMID).
"""
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parent.parent
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def main():
    hoy = datetime.now(timezone.utc)
    for ruta in (ROOT / "canales").glob("*/ruta.json"):
        canal = ruta.parent.name
        R = json.loads(ruta.read_text())["meses"]
        mes = R.get(hoy.strftime("%Y-%m")) or R[sorted(R)[0]]
        q = mes["pubmed"]
        ids = requests.get(EU + "esearch.fcgi", params={"db": "pubmed", "term": q, "retmax": 25, "sort": "relevance",
                                                       "retmode": "json", "tool": "canales-agent"}, timeout=60).json()["esearchresult"]["idlist"]
        time.sleep(0.5)
        L = [f"# PubMed · {canal} · {hoy:%Y-%m-%d}", f"Tema del mes: **{mes['tema']}** · Ángulos: {', '.join(mes['angulos'])}",
             f"Búsqueda: `{q}`", "", "Usa solo estos estudios; cita como (PMID 12345). Resúmenes recortados.", ""]
        if ids:
            x = ET.fromstring(requests.get(EU + "efetch.fcgi", params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}, timeout=90).content)
            for a in x.findall(".//PubmedArticle"):
                pmid = a.findtext(".//PMID")
                tit = "".join(a.find(".//ArticleTitle").itertext()) if a.find(".//ArticleTitle") is not None else ""
                rev = a.findtext(".//Journal/Title") or ""
                anio = a.findtext(".//PubDate/Year") or (a.findtext(".//PubDate/MedlineDate") or "")[:4]
                tipos = ", ".join(t.text for t in a.findall(".//PublicationType") if t.text and t.text != "Journal Article")
                abst = " ".join("".join(p.itertext()) for p in a.findall(".//Abstract/AbstractText"))
                abst = re.sub(r"\s+", " ", abst)[:900]
                L += [f"## PMID {pmid} · {anio} · {rev}", f"**{tit}**" + (f" _({tipos})_" if tipos else ""), abst, ""]
        out = ROOT / "investigacion" / f"{canal}_pubmed.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text("\n".join(L))
        print(f"OK {out.name}: {len(ids)} estudios")


if __name__ == "__main__":
    main()
