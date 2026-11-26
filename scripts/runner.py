"""Motor automático: produce y sube todo lo pendiente de todos los canales activos.

Recorre canales/<canal>/proyectos/*/guion.json. Un proyecto está pendiente si no tiene
publicado.json. Se procesa si su fecha de publicación cae dentro de VENTANA_HORAS
(o ya pasó). Tras subir, copia publicado.json junto al guion (el workflow lo commitea).

Variables de entorno: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET y un REFRESH_TOKEN_* por canal.
"""
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
VENTANA_HORAS = int(os.environ.get("VENTANA_HORAS", "36"))
MAX_POR_CORRIDA = int(os.environ.get("MAX_POR_CORRIDA", "8"))
URGENTE_HORAS = int(os.environ.get("URGENTE_HORAS", "12"))


def suf(cfg):
    """Proyecto de Google Cloud del canal: "A" (MayorDom-uploader, el de siempre) o "B" (cuota aparte para los canales nuevos)."""
    c = cfg.get("cliente", "A")
    return "" if c == "A" else f"_{c}"


def cuota_f(cfg):
    return ROOT / "canales" / (f"cuota{suf(cfg)}.json")


def token_file(canal, cfg):
    rt = os.environ.get(cfg["secreto"])
    if not rt or not os.environ.get(f"GOOGLE_CLIENT_ID{suf(cfg)}"):
        return False
    d = Path.home() / ".yt-agent"
    d.mkdir(exist_ok=True)
    (d / f"token_{canal}.json").write_text(json.dumps({
        "client_id": os.environ[f"GOOGLE_CLIENT_ID{suf(cfg)}"], "client_secret": os.environ[f"GOOGLE_CLIENT_SECRET{suf(cfg)}"],
        "refresh_token": rt, "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload",
                   "https://www.googleapis.com/auth/youtube.force-ssl"]}))
    return True


def fecha_pub(g):
    p = g.get("seo", {}).get("publicar_en")
    if not p:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(p.replace("Z", "+00:00"))




class CuotaAgotada(Exception):
    pass


def reinicio_cuota(ahora):
    """La cuota diaria de YouTube se reinicia a medianoche, hora del Pacífico."""
    from zoneinfo import ZoneInfo
    pac = ahora.astimezone(ZoneInfo("America/Los_Angeles"))
    sig = (pac + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0)
    return sig.astimezone(timezone.utc)


def run(script, proj, env, *extra):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), str(proj), *extra], env=env)
    if r.returncode == 75 and script == "upload.py":
        raise CuotaAgotada(f"cuota diaria de YouTube agotada en {proj.name}")
    if r.returncode:
        raise RuntimeError(f"{script} falló en {proj.name}")


def run_opc(script, proj, env, *extra):
    """Paso de mejora: si falla, avisa y sigue (no bloquea la publicación)."""
    r = subprocess.run([sys.executable, str(SCRIPTS / script), str(proj), *extra], env=env)
    if r.returncode:
        print(f"AVISO: {script} falló en {proj.name}; se continúa sin esa mejora", flush=True)


def que_hacer(msg):
    """Traduce un fallo a una acción concreta para el Fundador (reporte legible)."""
    m = msg.lower()
    if "invalid_grant" in m or "token" in m and ("expired" in m or "revoked" in m or "falta" in m):
        return "renovar el token de ese canal (pídele a Claude «/token <canal>»)."
    if "quota" in m or "cuota" in m:
        return "nada: el motor espera el reinicio de la cuota y sigue solo."
    if "errores:" in m or "guion" in m:
        return "error del guion: pídele a Claude que lo corrija."
    if "pexels" in m or "visual" in m or "imagen" in m:
        return "fallo de imágenes: suele resolverse solo en la siguiente hora; si se repite, avisa a Claude."
    return "si se repite en la siguiente corrida, avisa a Claude con este mensaje."


def espejo_vale(cfg_m, proj):
    """¿Este proyecto va también al canal espejo? (tipos y patrón del nombre en canales.json)."""
    import re as _re
    try:
        tipo = json.loads((proj / "guion.json").read_text()).get("tipo")
    except Exception:
        return False
    if cfg_m.get("espejo_tipos") and tipo not in cfg_m["espejo_tipos"]:
        return False
    pat = cfg_m.get("espejo_patron")
    return not pat or bool(_re.search(pat, proj.name))


def guardar_ya(proj, espejo=None):
    """Commit + push del proyecto recién publicado. Nunca detiene el motor si falla (se guarda al final)."""
    g = ["git", "-c", "user.name=canales-bot", "-c", "user.email=canales-bot@users.noreply.github.com"]
    try:
        subprocess.run(g + ["add", str(proj / "guion.json"), *[str(f) for f in proj.glob("publicado*.json")]], cwd=ROOT, check=True)
        subprocess.run(g + ["commit", "-q", "-m", f"Publicado: {proj.name}"], cwd=ROOT, check=True)
        for _ in range(4):
            if subprocess.run(g + ["pull", "-q", "--rebase", "-X", "theirs", "--autostash"], cwd=ROOT).returncode == 0 \
                    and subprocess.run(g + ["push", "-q"], cwd=ROOT).returncode == 0:
                return
            subprocess.run(g + ["rebase", "--abort"], cwd=ROOT, capture_output=True)
    except Exception as ex:
        print(f"AVISO: no se pudo guardar al instante {proj.name}: {ex}", flush=True)


def main():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    pausados, avisos_pausa = set(), []
    for f in sorted((ROOT / "canales").glob("cuota*.json")):
        hasta = datetime.fromisoformat(json.loads(f.read_text())["hasta"].replace("Z", "+00:00"))
        if ahora < hasta and not os.environ.get("IGNORAR_CUOTA"):
            pausados.add(f.name)
            avisos_pausa.append(f"Cuota diaria de YouTube agotada ({f.stem}): espera hasta las {hasta - timedelta(hours=5):%H:%M} de Lima y sigue solo.")
        else:
            f.unlink()
    activos = {c for c, v in canales.items() if not c.startswith("_") and isinstance(v, dict) and v.get("activo")}
    # Espejos: un canal activo puede volver a publicar los videos de otros canales (canales.json → espejo_de).
    espejos = {}
    for m in activos:
        for c in canales[m].get("espejo_de") or []:
            espejos.setdefault(c, []).append(m)
    pendientes = []
    try:
        REPRODUCIR = set(json.loads((ROOT / ".github" / "top10_reproducir.json").read_text()).get("proyectos", []))
    except Exception:
        REPRODUCIR = set()
    for canal, cfg in canales.items():
        if canal.startswith("_") or not isinstance(cfg, dict):
            continue
        if not cfg.get("activo") and not espejos.get(canal):
            continue
        if cfg.get("activo") and cuota_f(cfg).name in pausados and not espejos.get(canal):
            continue
        for gj in sorted((ROOT / "canales" / canal / "proyectos").glob("*/guion.json")):
            proj = gj.parent
            if (proj / "publicado.json").exists():
                continue
            g = json.loads(gj.read_text())
            solo = os.environ.get("SOLO_PROYECTO")
            if solo and proj.resolve() != (ROOT / solo).resolve():
                continue
            if not solo and g.get("motor") == "top10-semanal" and str(proj.relative_to(ROOT)) in REPRODUCIR:
                continue  # lo está reintentando top10-reproducir.yml: no subirlo dos veces
            if not solo and g.get("motor") == "top10-semanal":
                desde = g.get("reintento_desde")  # lo produce su propio workflow; aquí solo se reintenta si falló
                if not desde or datetime.fromisoformat(desde.replace("Z", "+00:00")) > ahora:
                    continue
            fp = fecha_pub(g)
            if fp <= ahora + timedelta(hours=int(cfg.get("ventana_horas", VENTANA_HORAS))):
                pendientes.append((fp, canal, cfg, proj, g))
    # 1) lo que sale en las próximas URGENTE_HORAS, por hora (nada pierde su horario);
    # 2) el resto, por prioridad del canal (canales.json → prioridad) y luego por hora.
    urg = ahora + timedelta(hours=URGENTE_HORAS)
    pendientes.sort(key=lambda x: (0, 0, x[0]) if x[0] <= urg else (1, x[2].get("prioridad", 9), x[0]))
    print(f"Pendientes en ventana: {len(pendientes)}")
    hechos, fallos = [], []
    pausa = None
    import time as _time
    t0 = _time.monotonic()
    presupuesto = int(os.environ.get("PRESUPUESTO_MIN", "200"))  # el job muere a los 300 min: se para antes y guarda
    for fp, canal, cfg, proj, g in pendientes[:MAX_POR_CORRIDA]:
        usados = (_time.monotonic() - t0) / 60
        pesado = bool(g.get("voz_fundador")) and g.get("tipo") != "short"  # voz clonada en CPU: 1-2 h por largo
        if usados > presupuesto or (pesado and usados > presupuesto - 100):
            print(f"Tiempo de esta corrida usado ({usados:.0f} min): {proj.name} sigue en la próxima.", flush=True)
            continue
        propio = bool(cfg.get("activo")) and cuota_f(cfg).name not in pausados
        mis_espejos = [m for m in espejos.get(canal, []) if espejo_vale(canales[m], proj)
                       and cuota_f(canales[m]).name not in pausados and not (proj / f"publicado_{m}.json").exists()]
        if not propio and not mis_espejos:
            continue
        if propio and not token_file(canal, cfg):
            fallos.append(f"{canal}: falta el secreto {cfg['secreto']} (o GOOGLE_CLIENT_ID{suf(cfg)})")
            continue
        env = dict(os.environ)
        env["TTS_MOTOR"] = "chatterbox" if g.get("voz_fundador") and (ROOT / "voces" / "david.wav").exists() else cfg.get("tts", "piper")
        if env["TTS_MOTOR"] == "edge":
            env["EDGE_VOICE"] = cfg.get("voz", "es-MX-JorgeNeural")
        else:
            env["PIPER_VOZ"] = cfg.get("voz", "vits-piper-es_MX-claude-high")
        av = ROOT / "canales" / canal / "assets" / "avatar.jpg"
        if av.exists():
            env["AVATAR"] = str(av)
        else:
            env.pop("AVATAR", None)
        if g.get("tipo") == "short":
            env["VERTICAL"] = "1"
        else:
            env.pop("VERTICAL", None)
        if g.get("tipo") != "short" and (g.get("tipo") == "top10" or g.get("voz_fundador") or g.get("res_4k")):
            env["RES_4K"] = "1"
        else:
            env.pop("RES_4K", None)
        offline = []  # sin clave de Pexels igual busca imágenes libres (Openverse / Wikimedia); el degradado es el último recurso
        if fp < ahora and g.get("seo", {}).get("publicar_en"):
            g["seo"]["publicar_en"] = None  # ya pasó la hora: se publica de inmediato
            g["seo"]["privacidad"] = "public"
            (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
        try:
            print(f"### {canal} · {proj.name}", flush=True)
            run("validate.py", proj, env)
            run("tts.py", proj, env)
            top10 = g.get("tipo") == "top10"
            if top10:
                run_opc("top10_fichas.py", proj, env)
                run("top10_visuales.py", proj, env)
            if g.get("top10_short"):
                run_opc("top10_short_visual.py", proj, env)
            run("visuals.py", proj, env, *offline)
            if cfg.get("audios_extra") and not g.get("audios_extra") and g.get("tipo") in cfg.get("audios_extra_tipos", [g.get("tipo")]):
                g["audios_extra"] = cfg["audios_extra"]
                (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
            multi = bool(g.get("audios_extra"))  # 1 video con varias pistas de idioma: sin subtítulos quemados
            run("render.py", proj, env, *(["--sin-subtitulos-quemados"] if multi else []))
            # Idiomas extra para todos los canales (orden del Fundador, 23-nov-2026): traducción del audio
            # (texto narrado) → título/descripción localizados + pistas de audio en la release «audios-extra».
            idiomas = [l for l in (cfg.get("idiomas_extra", canales.get("_idiomas_extra", {}).get("idiomas", []))) if l != g["lang"]]
            if idiomas:
                r = subprocess.run([sys.executable, str(SCRIPTS / "traducir.py"), str(proj), *idiomas], env=env)
                if r.returncode:
                    print("AVISO: traducción a idiomas extra no se completó", flush=True)
                g = json.loads((proj / "guion.json").read_text())
                voces = canales.get("_idiomas_extra", {}).get("voces", {})
                pistas = dict(g.get("audios_extra") or {})
                for l in idiomas:
                    if voces.get(l) and any(e.get(f"texto_{l}") for e in g["escenas"]):
                        pistas.setdefault(l, voces[l])
                if pistas:
                    g["audios_extra"] = pistas
                    (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
                    multi = True  # el video ya se renderizó: solo se generan las pistas aparte
            run("thumbnail.py", proj, env)
            if top10:
                run_opc("top10_miniatura.py", proj, env)
                run_opc("top10_seo.py", proj, env, "--canal", canal)
            run("metadata.py", proj, env)
            for m in mis_espejos:  # copia en los canales espejo (mismo video ya renderizado)
                if not token_file(m, canales[m]):
                    fallos.append(f"{m}: falta el secreto {canales[m]['secreto']} (o GOOGLE_CLIENT_ID{suf(canales[m])})")
                    continue
                try:
                    run("upload.py", proj, env, "--canal", m)
                    shutil.copy(proj / "salida" / "publicado.json", proj / f"publicado_{m}.json")
                    if not propio:
                        shutil.copy(proj / "salida" / "publicado.json", proj / "publicado.json")
                    guardar_ya(proj, m)
                    hechos.append(f"{m} (espejo de {canal}): {proj.name} → {json.loads((proj / f'publicado_{m}.json').read_text())['url']}")
                except CuotaAgotada:
                    hasta = reinicio_cuota(datetime.now(timezone.utc))
                    cuota_f(canales[m]).write_text(json.dumps({"hasta": hasta.strftime("%Y-%m-%dT%H:%M:%SZ"), "motivo": f"espejo {m}"}))
                    pausados.add(cuota_f(canales[m]).name)
                except Exception as ex:
                    fallos.append(f"{m} (espejo de {canal}): {proj.name}: {ex}")
            if not propio:
                continue
            run("upload.py", proj, env, "--canal", canal)
            shutil.copy(proj / "salida" / "publicado.json", proj / "publicado.json")
            guardar_ya(proj)  # se sube a git al instante: si la corrida se corta, no se vuelve a subir (sin duplicados)
            if multi:  # pistas ES/PT/…: se dejan en la release «audios-extra» para subirlas en YouTube Studio
                try:
                    run("audios_extra.py", proj, env)
                    arch = []
                    for f in sorted((proj / "salida").glob("audio_*.m4a")) + sorted((proj / "salida").glob("subtitulos_*.srt")):
                        dst = proj / "salida" / f"{proj.name}__{f.name}"
                        f.rename(dst)
                        arch.append(str(dst))
                    if subprocess.run(["gh", "release", "view", "audios-extra"], env=env, capture_output=True).returncode:
                        subprocess.run(["gh", "release", "create", "audios-extra", "--title", "Pistas de audio extra",
                                        "--notes", "Audios y subtítulos en otros idiomas para YouTube Studio → Idiomas."], env=env)
                    subprocess.run(["gh", "release", "upload", "audios-extra", *arch, "--clobber"], env=env, check=True)
                    hechos.append(f"{canal}: {proj.name}: pistas de idioma listas para Studio → release «audios-extra»")
                except Exception as ex:
                    fallos.append(f"{canal}: {proj.name}: pistas de idioma: {ex}")
            if (cfg.get("meta") or {}).get("secreto") and env.get(cfg["meta"]["secreto"]):
                r = subprocess.run([sys.executable, str(SCRIPTS / "meta.py"), "encolar", str(proj), "--canal", canal], env=env)
                if r.returncode:
                    print("AVISO: no se pudo encolar para Instagram/Facebook", flush=True)
            hechos.append(f"{canal}: {proj.name} → {json.loads((proj / 'publicado.json').read_text())['url']}")
        except CuotaAgotada as e:  # no es un error del motor: se pausa ese proyecto de Cloud hasta el reinicio
            hasta = reinicio_cuota(datetime.now(timezone.utc))
            cuota_f(cfg).write_text(json.dumps({"hasta": hasta.strftime("%Y-%m-%dT%H:%M:%SZ"), "motivo": str(e)}))
            pausados.add(cuota_f(cfg).name)
            pausa = f"Cuota diaria de YouTube agotada ({cuota_f(cfg).stem}); se reanuda a las {hasta - timedelta(hours=5):%H:%M} de Lima."
            print(pausa, flush=True)
            if all(cuota_f(c).name in pausados for _, _, c, _, _ in pendientes):
                break
        except Exception as e:  # sigue con el siguiente
            msg = str(e)
            fallos.append(f"{canal}: {proj.name}: {msg}")
            print("FALLO", msg, flush=True)
        finally:
            for sub in ("audio", "imagenes", "tmp", "salida"):
                shutil.rmtree(proj / sub, ignore_errors=True)
            (proj / "creditos.json").unlink(missing_ok=True)
    rep = ROOT / "reporte.md"
    rep.write_text(f"# Último reporte ({ahora:%Y-%m-%d %H:%M} UTC)\n\n## Subidos\n"
                   + "".join(f"- {h}\n" for h in hechos) + "\n## Fallos\n" + "".join(f"- {f}\n  - Qué hacer: {que_hacer(f)}\n" for f in fallos)
                   + (f"\n## En pausa\n- {pausa}\n" if pausa else "")
                   + "".join(f"\n## En pausa\n- {a}\n" for a in avisos_pausa))
    print(rep.read_text())
    if fallos:
        sys.exit(1)  # GitHub envía un correo al Fundador cuando la corrida falla


if __name__ == "__main__":
    main()
