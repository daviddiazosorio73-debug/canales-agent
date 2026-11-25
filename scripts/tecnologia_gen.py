"""Tecno Log IA · Shorts automáticos del catálogo (sin voz).

Calendario (orden del Fundador, 23-nov-2026): 7 Shorts por día de domingo a viernes; sábado descanso.
  · 1 diario de NUESTRA MARCA y servicios (catálogo digital, orden con firma, multimarca, cobertura, ofertas, asesoría).
  · 6 de productos, al azar entre MARCA (3 productos de una marca) y LÍNEA (3 productos de una categoría).
Horas Lima: 07:00 · 09:30 · 12:30 (marca propia) · 15:30 · 18:00 · 20:00 · 21:30.

planificar(cola): agrega a la cola los Shorts de los próximos días (solo datos; el video se arma al subir).
asegurar_video(it): renderiza el MP4 de un Short generado si aún no existe (Playwright + ffmpeg).
Productos y fotos: API pública del catálogo (precios NO se muestran). Frase obligatoria en todo el material.
"""
import hashlib
import json
import math
import random
import re
import struct
import subprocess
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "canales" / "tecnologia"
GEN = DIR / "videos" / "gen"
SITIO = "https://daviddiazosorio73-debug.github.io/catalogo/"
API = "https://script.google.com/macros/s/AKfycby_n087GKueloyFmtqNp7u-LcsRmKk9m3fZ70deCms2PhRr8vL4qsZL0oG9Jw5xOUs9/exec"
WA = "928 146 619"
FRASE = "SOLO PARA DISTRIBUIDORES Y MAYORISTAS"
LIMA = timezone(timedelta(hours=-5))
HORAS = ["07:00", "09:30", "12:30", "15:30", "18:00", "20:00", "21:30"]
HORA_PROPIA = "12:30"
DIAS_ADELANTE = 3
INICIO = datetime(2026, 11, 24).date()  # empieza el martes 24-nov-2026
NO_REPETIR_DIAS = 45
W, H, FPS = 1080, 1920, 30

TEMAS_PROPIOS = ["catalogo", "orden", "multimarca", "cobertura", "ofertas", "asesoria"]


# ----------------------------------------------------------------------------- datos
_CAT = None


def catalogo():
    global _CAT
    if _CAT is None:
        d = requests.get(API, params={"accion": "productos"}, timeout=120).json()
        try:
            espejo = set(requests.get(SITIO + "assets/d/index.json", timeout=30).json())
        except Exception:
            espejo = set()
        prods = []
        for p in d.get("productos", []):
            if p.get("estado") not in ("Activo", "Próximo ingreso"):
                continue
            fotos = []
            for u in [p.get("foto")] + list(p.get("fotos") or []):
                m = re.search(r"/d/([\w-]{20,})|[?&]id=([\w-]{20,})", u or "")
                if m:
                    i = m.group(1) or m.group(2)
                    fotos.append(SITIO + f"assets/d/{i}.webp" if i in espejo else f"https://lh3.googleusercontent.com/d/{i}=w1000")
                elif u:
                    fotos.append(u if u.startswith("http") else SITIO + u.lstrip("./"))
            if fotos:
                p["_fotos"] = fotos
                prods.append(p)
        _CAT = {"productos": prods, "todos": d.get("productos", []), "config": d.get("config", {})}
    return _CAT


def limpio(s, n=None):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if not n or len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def tag(s):
    return re.sub(r"[^0-9A-Za-zÁÉÍÓÚÑáéíóúñ]", "", s.title())


# ----------------------------------------------------------------------------- plan
def a_utc(dia, hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(dia.year, dia.month, dia.day, h, m, tzinfo=LIMA).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dia_lima(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(LIMA)


def usados(cola, dias):
    lim = datetime.now(timezone.utc) - timedelta(days=dias)
    ids = set()
    for it in cola:
        g = it.get("gen") or {}
        if datetime.fromisoformat(it["publicar_en"].replace("Z", "+00:00")) >= lim:
            ids.update(g.get("ids", []))
    return ids


_FOTO_OK = {}


def foto_ok(url):
    """La foto carga y es una foto real (no un logo chico): lado mayor >= 400 px."""
    if url not in _FOTO_OK:
        try:
            import io
            from PIL import Image
            r = requests.get(url, timeout=40)
            ok = r.status_code == 200 and r.headers.get("content-type", "").startswith("image/")
            _FOTO_OK[url] = ok and max(Image.open(io.BytesIO(r.content)).size) >= 400
        except Exception:
            _FOTO_OK[url] = False
    return _FOTO_OK[url]


def elegir(rnd, tipo, evitar_ids, evitar_grupos):
    P = [p for p in catalogo()["productos"] if p["id"] not in evitar_ids]
    clave = "marca" if tipo == "marca" else "categoria"
    grupos = {}
    for p in P:
        if p.get(clave):
            grupos.setdefault(p[clave], []).append(p)
    ok = sorted(g for g, l in grupos.items() if len(l) >= 3 and g not in evitar_grupos) or \
        sorted(g for g, l in grupos.items() if len(l) >= 3)
    rnd.shuffle(ok)
    for g in ok[:6]:
        l = grupos[g][:]
        rnd.shuffle(l)
        if tipo == "marca":  # variedad: primero categorías distintas
            vistos, a, b = set(), [], []
            for p in l:
                (b if p.get("categoria") in vistos else a).append(p); vistos.add(p.get("categoria"))
            l = a + b
        elegidos = []
        for p in l[:12]:
            if foto_ok(p["_fotos"][0]):
                elegidos.append(p)
            if len(elegidos) == 3:
                return g, elegidos
    return None, []


def seo(tipo, grupo, ps, tema=None):
    cat = catalogo()
    n_total = len(cat["todos"])
    marcas = sorted({p.get("marca") for p in cat["todos"] if p.get("marca")})
    link = SITIO + "?d=yt"
    if tipo == "propia":
        t = TEMA[tema]
        titulo = t["titulo"]
        resumen = t["resumen"].format(n=n_total, m=len(marcas), marcas=", ".join(marcas[:6]))
        preguntas = t["preguntas"]
        tags = ["tecno log ia", "catálogo mayorista", "distribuidores perú", "mayoristas perú", "proveedor mayorista perú",
                "venta al por mayor", "catálogo digital", "electrodomésticos por mayor"] + [m.lower() for m in marcas[:6]]
        hashtags = "#TecnoLogIA #Mayoristas #Distribuidores #Peru #CatalogoDigital #Shorts"
    else:
        lista = "; ".join(f"{p.get('marca', '')} {limpio(p['nombre'], 60)} (código {p['codigo']})" for p in ps)
        cats = sorted({p.get("categoria", "") for p in ps})
        mks = sorted({p.get("marca", "") for p in ps})
        if tipo == "linea":
            titulo = f"{limpio(grupo, 48)}: 3 modelos para tu negocio · Mayoristas Perú #Shorts"
            resumen = (f"Tecno Log IA distribuye {grupo.lower()} ({', '.join(mks)}) a distribuidores y mayoristas de todo el Perú. "
                       f"En este video: {lista}.")
            preguntas = [f"¿Dónde comprar {grupo.lower()} al por mayor en Perú?",
                         f"¿Qué modelos de {grupo.lower()} hay para negocios?",
                         f"¿Cómo pido precio de {grupo.lower()} para distribuidores?"]
            if ps[0].get("ideal"):
                resumen += f" Ideal para: {limpio(ps[0]['ideal'], 160)}"
        else:
            titulo = f"{grupo}: 3 productos para distribuidores en Perú · {limpio(cats[0], 30)} y más #Shorts"
            resumen = (f"Tecno Log IA distribuye la marca {grupo} a distribuidores y mayoristas de todo el Perú. "
                       f"En este video: {lista}.")
            preguntas = [f"¿Dónde comprar productos {grupo} al por mayor en Perú?",
                         f"¿Quién distribuye {grupo} para tiendas y mayoristas en Perú?",
                         f"¿Qué productos {grupo} hay en el catálogo de Tecno Log IA?"]
        tags = ([c.lower() for c in cats] + [m.lower() for m in mks] + [f"{c.lower()} por mayor" for c in cats[:2]]
                + [f"{c.lower()} perú" for c in cats[:2]] + [p["codigo"] for p in ps]
                + ["distribuidores perú", "mayoristas perú", "tecno log ia", "venta al por mayor"])
        hashtags = " ".join(dict.fromkeys(["#" + tag(x) for x in mks + cats[:2]] + ["#TecnoLogIA", "#Mayoristas", "#Distribuidores", "#Peru", "#Shorts"]))
    titulo = titulo[:100]
    desc = (f"En resumen: {resumen}\n\n"
            + "Preguntas que responde este video:\n" + "\n".join("• " + q for q in preguntas) + "\n\n"
            + f"✅ {FRASE.capitalize()}. Precios y stock por WhatsApp.\n"
            + f"🛒 Catálogo digital (+{n_total} productos; cotiza y firma tu orden en línea): {link}\n"
            + f"📲 WhatsApp distribuidores: {WA} · https://wa.me/51928146619\n\n"
            + "Tecno Log IA · Venta multimarca para distribuidores y mayoristas de todo el Perú.\n\n" + hashtags)
    texto_reel = desc.replace("#Shorts", "").strip()
    tags = list(dict.fromkeys(t for t in tags if t))
    while len(",".join(tags)) > 480:
        tags.pop()
    return titulo, desc[:4900], tags, texto_reel


def planificar(cola):
    hoy = datetime.now(LIMA).date()
    desde = max(hoy + timedelta(days=1), INICIO)
    # Los packs Oster ya hechos que no se subieron: se reubican (2 por día) en horas de producto
    prehechos = [it for it in cola if not it.get("gen") and not it.get("youtube_id") and not it.get("pausado")
                 and not it.get("plan_v2") and dia_lima(it["publicar_en"]).date() >= desde]
    for it in prehechos:
        it["_reubicar"] = True
    # El Short del catálogo digital (estaba en pausa hasta el lanzamiento) es la 1ª marca propia
    for it in cola:
        if it.get("clave") == "catalogo_digital" and it.get("pausado") and not it.get("plan_v2"):
            it.pop("pausado", None); it["_reubicar"] = True; it["tema_propio"] = "catalogo"
    cambios = 0
    rnd_global = random.Random(str(desde))
    tema_i = sum(1 for it in cola if (it.get("gen") or {}).get("tipo") == "propia")
    for k in range(DIAS_ADELANTE):
        dia = desde + timedelta(days=k)
        if dia.weekday() == 5:  # sábado: descanso
            for it in cola:
                if it.get("_reubicar") and dia_lima(it["publicar_en"]).date() == dia:
                    it["publicar_en"] = "2099-01-01T00:00:00Z"  # se reubica abajo
            continue
        del_dia = [it for it in cola if not it.get("_reubicar") and it["publicar_en"] < "2099"
                   and dia_lima(it["publicar_en"]).date() == dia]
        if len(del_dia) >= 7:
            continue
        ocupadas = [dia_lima(it["publicar_en"]) for it in del_dia]
        libres = []
        for h in HORAS:
            hh, mm = map(int, h.split(":"))
            t = datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=LIMA)
            if all(abs((t - o).total_seconds()) >= 3600 for o in ocupadas):
                libres.append(h)
        libres = libres[: 7 - len(del_dia)]
        tiene_propia = any((it.get("gen") or {}).get("tipo") == "propia" or it.get("tema_propio") for it in del_dia)
        rnd = random.Random(f"tecno-{dia}")
        evitar = usados(cola, NO_REPETIR_DIAS)
        grupos_dia = set()
        oster_hoy = sum(1 for it in del_dia if not it.get('gen') and it.get('clave') != 'catalogo_digital')
        for h in libres:
            if not tiene_propia and (h == HORA_PROPIA or h == libres[-1]):
                tiene_propia = True
                cat_short = next((it for it in cola if it.get("clave") == "catalogo_digital" and it.get("_reubicar")), None)
                if cat_short:
                    cat_short["publicar_en"] = a_utc(dia, h); cat_short.pop("_reubicar"); cat_short["plan_v2"] = True; cambios += 1
                    continue
                tema = TEMAS_PROPIOS[tema_i % len(TEMAS_PROPIOS)]; tema_i += 1
                titulo, desc, tags, reel = seo("propia", None, [], tema)
                clave = f"gen-{dia}-{h.replace(':', '')}-propia"
                cola.append({"clave": clave, "archivo": f"gen/{clave}.mp4", "titulo": titulo, "descripcion": desc, "tags": tags,
                             "publicar_en": a_utc(dia, h), "texto_reel": reel, "gen": {"tipo": "propia", "tema": tema, "ids": []}})
                cambios += 1
                continue
            pend = [it for it in cola if it.get("_reubicar") and it.get("clave") != "catalogo_digital"]
            if pend and oster_hoy < 2:
                it = pend[0]; it["publicar_en"] = a_utc(dia, h); it.pop("_reubicar"); it["plan_v2"] = True; oster_hoy += 1; cambios += 1
                continue
            tipo = rnd.choice(["marca", "linea"])
            grupo, ps = elegir(rnd, tipo, evitar, grupos_dia)
            if not ps:
                tipo = "linea" if tipo == "marca" else "marca"
                grupo, ps = elegir(rnd, tipo, evitar, grupos_dia)
            if not ps:
                continue
            grupos_dia.add(grupo)
            evitar.update(p["id"] for p in ps)
            titulo, desc, tags, reel = seo(tipo, grupo, ps)
            clave = f"gen-{dia}-{h.replace(':', '')}-{tipo}"
            cola.append({"clave": clave, "archivo": f"gen/{clave}.mp4", "titulo": titulo, "descripcion": desc, "tags": tags,
                         "publicar_en": a_utc(dia, h), "texto_reel": reel,
                         "gen": {"tipo": tipo, "grupo": grupo, "ids": [p["id"] for p in ps]}})
            cambios += 1
    # Lo que no alcanzó lugar queda para los días siguientes (sin fecha en sábado)
    for it in cola:
        if it.get("_reubicar"):
            it["publicar_en"] = "2099-01-01T00:00:00Z"  # sin lugar todavía: se ubica en la próxima corrida
            it.pop("_reubicar")
    cola.sort(key=lambda x: x["publicar_en"])
    return cambios


# Reubicar en la próxima corrida lo marcado como pendiente
def _marcar_pendientes(cola):
    for it in cola:
        if it.pop("pendiente_reubicar", None):
            it["_reubicar"] = True


TEMA = {
    "catalogo": {"titulo": "Catálogo mayorista en tu celular: +900 productos · Tecno Log IA #Shorts",
                 "resumen": "Tecno Log IA tiene un catálogo digital con {n} productos de marcas como {marcas}, solo para distribuidores y mayoristas del Perú: buscas por código, producto o marca, armas tu pedido y firmas tu orden en línea.",
                 "preguntas": ["¿Dónde ver un catálogo mayorista de electrodomésticos y equipos en Perú?", "¿Cómo cotizar al por mayor desde el celular?", "¿Qué marcas distribuye Tecno Log IA?"],
                 "hook": ["TU CATÁLOGO", "MAYORISTA", "en el celular"],
                 "puntos": [("✓", "Busca por código, producto o marca"), ("✓", "Arma tu pedido en minutos"), ("✓", "Firma tu orden en línea")]},
    "orden": {"titulo": "Cómo hacer tu pedido mayorista en 3 pasos · Tecno Log IA #Shorts",
              "resumen": "En el catálogo digital de Tecno Log IA un distribuidor hace su pedido en 3 pasos: elige productos, escribe su RUC y firma la orden en la pantalla; la orden en PDF llega a su correo.",
              "preguntas": ["¿Cómo hacer un pedido al por mayor en línea en Perú?", "¿Cómo recibo mi orden de compra en PDF?", "¿Necesito RUC para comprar como distribuidor?"],
              "hook": ["TU PEDIDO", "EN 3 PASOS", "con tu RUC"],
              "puntos": [("1", "Elige productos y cantidades"), ("2", "Escribe tu RUC y tus datos de envío"), ("3", "Firma: tu orden llega en PDF a tu correo")]},
    "multimarca": {"titulo": "Un solo proveedor, muchas marcas: Tecno Log IA para mayoristas #Shorts",
                   "resumen": "Tecno Log IA es un proveedor multimarca para distribuidores y mayoristas del Perú: {m} marcas y {n} productos en un solo catálogo, entre ellas {marcas}.",
                   "preguntas": ["¿Qué proveedor mayorista tiene varias marcas en Perú?", "¿Dónde compro Oster y equipos comerciales al por mayor?", "¿Cómo simplificar mis compras como distribuidor?"],
                   "hook": ["UN PROVEEDOR", "MUCHAS MARCAS", "para tu tienda"],
                   "puntos": [("✓", "{m} marcas en un solo catálogo"), ("✓", "+{n} productos"), ("✓", "Un solo contacto para todo tu pedido")]},
    "cobertura": {"titulo": "Distribuidores de todo el Perú: así te atendemos · Tecno Log IA #Shorts",
                  "resumen": "Tecno Log IA atiende a distribuidores y mayoristas de todas las zonas del Perú (Lima y Callao, Norte, Centro, Sur Chico, Sur, Sur Andino y Oriente) con catálogo digital y atención por WhatsApp.",
                  "preguntas": ["¿Qué proveedor mayorista atiende provincias del Perú?", "¿Cómo compro al por mayor desde provincia?", "¿Cómo contacto a Tecno Log IA?"],
                  "hook": ["TODO", "EL PERÚ", "una sola red"],
                  "puntos": [("✓", "Lima y Callao · Norte · Centro"), ("✓", "Sur Chico · Sur · Sur Andino · Oriente"), ("✓", "Atención por WhatsApp " + WA)]},
    "ofertas": {"titulo": "Ofertas del mes para distribuidores · Tecno Log IA #Shorts",
                "resumen": "Cada mes Tecno Log IA publica ofertas del día, de la semana y del mes para distribuidores y mayoristas del Perú en su catálogo digital de {n} productos.",
                "preguntas": ["¿Dónde ver ofertas mayoristas en Perú?", "¿Qué ofertas hay este mes para distribuidores?", "¿Cómo pido precio de las ofertas?"],
                "hook": ["OFERTAS", "DEL MES", "para mayoristas"],
                "puntos": [("✓", "Ofertas del día"), ("✓", "Ofertas de la semana"), ("✓", "Ofertas del mes")]},
    "asesoria": {"titulo": "¿No sabes qué pedir? Te armamos el pedido · Tecno Log IA #Shorts",
                 "resumen": "Tecno Log IA asesora a distribuidores y mayoristas del Perú para armar su pedido según su tipo de negocio, con productos de su catálogo de {n} productos, por WhatsApp.",
                 "preguntas": ["¿Quién me asesora para armar un pedido mayorista?", "¿Qué equipos necesito para mi negocio?", "¿Cómo contacto a un asesor de Tecno Log IA?"],
                 "hook": ["TE ARMAMOS", "EL PEDIDO", "según tu negocio"],
                 "puntos": [("✓", "Cuéntanos tu negocio"), ("✓", "Te proponemos productos del catálogo"), ("✓", "Confirmas por WhatsApp " + WA)]},
}


# ----------------------------------------------------------------------------- render
CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;overflow:hidden;font-family:'Space Grotesk',Arial,sans-serif;color:#fff;
 background:radial-gradient(ellipse at 50% 38%,#3a4060 0%,#22263a 45%,#11131c 100%)}
.top{position:absolute;top:90px;left:0;right:0;text-align:center}.top img{width:640px}
.frase{position:absolute;bottom:110px;left:60px;right:60px;text-align:center;font-weight:800;font-size:44px;color:#151823;
 background:linear-gradient(180deg,#fff0a8,#f2c94c 55%,#d9a520);border-radius:999px;padding:22px 10px;box-shadow:0 10px 0 #8a6200,0 0 40px rgba(242,201,76,.45)}
.hook{position:absolute;top:560px;left:40px;right:40px;text-align:center}
.k{display:inline-block;font-size:38px;letter-spacing:8px;color:#9fe9ff;border:2px solid rgba(34,225,255,.6);border-radius:999px;padding:10px 28px;margin-bottom:40px}
.h1{font-size:120px;font-weight:700;line-height:.95;text-shadow:0 8px 0 #0008,0 0 30px rgba(232,38,79,.5)}
.h2{font-size:84px;font-weight:700;line-height:1.05;margin-top:24px;background:linear-gradient(180deg,#fff7d6,#f5b820);-webkit-background-clip:text;color:transparent}
.h3{font-size:46px;color:#d6d9e8;margin-top:36px}
.card{position:absolute;top:330px;left:70px;right:70px;height:900px;background:#fff;border-radius:44px;display:flex;align-items:center;justify-content:center;
 box-shadow:0 40px 80px rgba(0,0,0,.55),0 0 0 6px rgba(242,201,76,.35)}
.card img{width:86%;height:86%;object-fit:contain}
.num{z-index:3;position:absolute;top:300px;left:40px;width:120px;height:120px;border-radius:50%;background:#e8264f;font-size:64px;font-weight:700;display:flex;align-items:center;justify-content:center;box-shadow:0 0 30px rgba(232,38,79,.6)}
.info{position:absolute;top:1270px;left:70px;right:70px}
.chips{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:22px}
.chip{font-size:36px;font-weight:600;padding:10px 24px;border-radius:999px;background:rgba(255,255,255,.12);border:2px solid rgba(34,225,255,.6)}
.cod{font-family:'JetBrains Mono',monospace;font-size:38px;color:#07070c;background:#22e1ff;border-radius:14px;padding:8px 22px}
.nom{font-size:58px;font-weight:700;line-height:1.08}
.pts{position:absolute;top:560px;left:70px;right:70px}
.pt{display:flex;gap:30px;align-items:center;background:rgba(255,255,255,.08);border:2px solid rgba(255,255,255,.15);border-radius:30px;padding:36px;margin-bottom:34px}
.pt b{flex:0 0 120px;height:120px;border-radius:28px;background:#e8264f;display:flex;align-items:center;justify-content:center;font-size:64px}
.pt span{font-size:54px;font-weight:600;line-height:1.1}
.cta{position:absolute;top:400px;left:60px;right:60px;text-align:center}
.cta .t{font-size:96px;font-weight:700;line-height:1}
.cta .w{margin:40px auto 0;display:inline-block;background:#13a653;border-radius:26px;padding:22px 40px;font-size:66px;font-weight:700}
.cta .q{margin:50px auto 0;width:420px;height:420px;background:#fff;border-radius:30px;padding:24px}
.cta .q img{width:100%;height:100%}
.cta .s{font-size:44px;color:#d6d9e8;margin-top:30px;line-height:1.2}
"""


def html(cuerpo):
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@500&display=swap' rel='stylesheet'>"
            f"<style>{CSS}</style></head><body><div class='top'><img src='{SITIO}assets/logo-wordmark.png'></div>{cuerpo}"
            f"<div class='frase'>{FRASE}</div></body></html>")


def esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def qr_dataurl():
    import base64, io
    import qrcode
    img = qrcode.make(SITIO + "?d=short", box_size=10, border=1)  # escaneado desde un Short
    b = io.BytesIO(); img.save(b, format="PNG")
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


def escenas(it, app=None):
    g = it["gen"]; cat = catalogo()
    porid = {p["id"]: p for p in cat["productos"]}
    n_total = len(cat["todos"]); marcas = sorted({p.get("marca") for p in cat["todos"] if p.get("marca")})
    E = []
    if g["tipo"] == "propia":
        t = TEMA[g["tema"]]
        E.append(html(f"<div class='hook'><div class='k'>TECNO LOG IA</div><div class='h1'>{t['hook'][0]}</div><div class='h2'>{t['hook'][1]}</div><div class='h3'>{t['hook'][2]}</div></div>"))
        pts = "".join(f"<div class='pt'><b>{a if a in '123' else i}</b><span>{esc(b.format(n=n_total, m=len(marcas)))}</span></div>" for i, (a, b) in enumerate(t["puntos"], 1))
        E.append(html(f"<div class='pts'>{pts}</div>"))
        if app:  # captura real del catálogo digital dentro de un celular
            E.append(html(f"<div style='position:absolute;top:300px;left:270px;width:540px;height:1170px;border-radius:70px;background:#0b0c12;padding:22px;"
                          f"box-shadow:0 40px 90px rgba(0,0,0,.6),0 0 0 4px #3a4160'><img src='{app}' style='width:100%;height:100%;object-fit:cover;object-position:top;border-radius:50px'></div>"
                          f"<div class='h3' style='position:absolute;top:1520px;left:0;right:0;text-align:center'>Así se ve tu catálogo</div>"))
        if g["tema"] == "multimarca":
            E.append(html("<div class='pts'>" + "".join(f"<div class='pt'><b>✓</b><span>{esc(m)}</span></div>" for m in marcas[:6]) + "</div>"))
    else:
        ps = [porid[i] for i in g["ids"] if i in porid]
        if len(ps) < 2:
            raise RuntimeError("productos no disponibles: " + ",".join(g["ids"]))
        k = "LÍNEA" if g["tipo"] == "linea" else "MARCA"
        sub = limpio(ps[0].get("ideal"), 90) if g["tipo"] == "linea" and ps[0].get("ideal") else f"{len(ps)} productos para tu tienda"
        E.append(html(f"<div class='hook'><div class='k'>{k}</div><div class='h1' style='font-size:{110 if len(g['grupo']) < 18 else 86}px'>{esc(g['grupo'].upper())}</div><div class='h3'>{esc(sub)}</div></div>"))
        for n, p in enumerate(ps, 1):
            E.append(html(f"<div class='num'>{n}</div><div class='card'><img src='{p['_fotos'][0]}'></div>"
                          f"<div class='info'><div class='chips'><span class='chip'>{esc(p.get('marca'))}</span><span class='cod'>{esc(p['codigo'])}</span></div>"
                          f"<div class='nom'>{esc(limpio(p['nombre'], 70))}</div></div>"))
    E.append(html(f"<div class='cta'><div class='t'>Pide tu precio</div><div class='w'>WhatsApp {WA}</div>"
                  f"<div class='q'><img src='{qr_dataurl()}'></div><div class='s'>Catálogo digital · +{n_total} productos<br>cotiza y firma tu orden en línea</div></div>"))
    return E


def musica(ruta, dur, semilla):
    """Fondo musical suave generado (sin derechos de terceros)."""
    import numpy as np
    sr = 44100; rnd = random.Random(semilla)
    raiz = rnd.choice([220.0, 233.08, 246.94, 261.63])
    prog = [[0, 4, 7], [-3, 0, 4], [5, 9, 12], [7, 11, 14]]
    t = np.arange(int(sr * dur)) / sr
    y = np.zeros_like(t)
    compas = dur / 4
    for i, ac in enumerate(prog):
        a, b = int(i * compas * sr), int((i + 1) * compas * sr)
        tt = t[a:b] - t[a]
        env = np.minimum(1, tt / 0.4) * np.minimum(1, (compas - tt) / 0.4)
        for s in ac:
            f = raiz * 2 ** (s / 12)
            y[a:b] += env * (0.5 * np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(2 * np.pi * 2 * f * tt))
    bpm = 100; paso = 60 / bpm
    for k in range(int(dur / paso)):  # pulso suave
        a = int(k * paso * sr); n = int(0.12 * sr)
        if a + n < len(y):
            tt = np.arange(n) / sr
            y[a:a + n] += 0.9 * np.sin(2 * np.pi * (90 - 300 * tt) * tt) * np.exp(-tt * 30)
    y = y / (np.abs(y).max() + 1e-9) * 0.35
    fade = int(0.8 * sr); y[-fade:] *= np.linspace(1, 0, fade); y[:int(0.3 * sr)] *= np.linspace(0, 1, int(0.3 * sr))
    with wave.open(str(ruta), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(v * 32767)) for v in y))


def asegurar_video(it):
    """Devuelve la ruta del MP4; lo renderiza si es un Short generado y aún no existe."""
    ruta = DIR / "videos" / it["archivo"]
    if ruta.exists() or not it.get("gen"):
        return ruta
    GEN.mkdir(parents=True, exist_ok=True)
    tmp = GEN / ("tmp_" + it["clave"]); tmp.mkdir(exist_ok=True)
    from playwright.sync_api import sync_playwright
    pngs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        app = None
        if it["gen"]["tipo"] == "propia" and it["gen"]["tema"] in ("catalogo", "orden", "ofertas", "multimarca"):
            try:
                import base64
                m = b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
                m.goto(SITIO + "?d=yt", wait_until="networkidle", timeout=90000)
                m.wait_for_timeout(2500)
                # Sin precios en piezas públicas: se ocultan todos los montos «S/ …» y la cinta PVP
                m.evaluate("""() => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                  const ns = []; while (w.nextNode()) if (/S\\/\\s?\\d|PVP/.test(w.currentNode.nodeValue)) ns.push(w.currentNode.parentElement);
                  ns.forEach(e => e.style.visibility = 'hidden'); }""")
                app = "data:image/png;base64," + base64.b64encode(m.screenshot()).decode()
                m.close()
            except Exception as e:
                print("Captura del catálogo: no se pudo:", str(e)[:120])
        pags = escenas(it, app)
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, h in enumerate(pags):
            pg.set_content(h, wait_until="networkidle", timeout=90000)
            pg.wait_for_timeout(400)
            f = tmp / f"e{i}.png"; pg.screenshot(path=str(f)); pngs.append(f)
        b.close()
    durs = [2.6] + [3.0] * (len(pngs) - 2) + [3.6]
    X = 0.35
    clips = []
    for i, (f, d) in enumerate(zip(pngs, durs)):
        c = tmp / f"c{i}.mp4"
        z = "min(zoom+0.0007,1.07)" if i % 2 == 0 else "if(eq(on,1),1.07,max(zoom-0.0007,1))"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", str(FPS), "-i", str(f),
                        "-vf", f"scale=2160:-1,zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},format=yuv420p",
                        "-t", str(d), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(c)], check=True)
        clips.append((c, d))
    # Unión con transición
    entradas, filtros, off, prev = [], [], 0.0, "0:v"
    for c, _ in clips:
        entradas += ["-i", str(c)]
    for i in range(1, len(clips)):
        off += clips[i - 1][1] - X
        filtros.append(f"[{prev}][{i}:v]xfade=transition={'slideleft' if i % 2 else 'fade'}:duration={X}:offset={off:.2f}[v{i}]")
        prev = f"v{i}"
    total = sum(d for _, d in clips) - X * (len(clips) - 1)
    wav = tmp / "m.wav"; musica(wav, total, it["clave"])
    tmpout = tmp / "out.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *entradas, "-i", str(wav), "-filter_complex", ";".join(filtros),
                    "-map", f"[{prev}]", "-map", f"{len(clips)}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(tmpout)], check=True)
    tmpout.rename(ruta)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()
    return ruta


if __name__ == "__main__":
    import sys
    cola = json.loads((DIR / "cola.json").read_text())
    if "--plan" in sys.argv:
        _marcar_pendientes(cola)
        print("Agregados/reubicados:", planificar(cola))
        (DIR / "cola.json").write_text(json.dumps(cola, ensure_ascii=False, indent=2) + "\n")
    if "--render" in sys.argv:
        clave = sys.argv[sys.argv.index("--render") + 1]
        it = next(x for x in cola if x["clave"] == clave)
        print(asegurar_video(it))
