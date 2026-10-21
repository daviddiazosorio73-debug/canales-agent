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


def token_file(canal, cfg):
    rt = os.environ.get(cfg["secreto"])
    if not rt:
        return False
    d = Path.home() / ".yt-agent"
    d.mkdir(exist_ok=True)
    (d / f"token_{canal}.json").write_text(json.dumps({
        "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": rt, "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": ["https://www.googleapis.com/auth/youtube.upload",
                   "https://www.googleapis.com/auth/youtube.force-ssl"]}))
    return True


def fecha_pub(g):
    p = g.get("seo", {}).get("publicar_en")
    if not p:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(p.replace("Z", "+00:00"))


def run(script, proj, env, *extra):
    r = subprocess.run([sys.executable, str(SCRIPTS / script), str(proj), *extra], env=env)
    if r.returncode:
        raise RuntimeError(f"{script} falló en {proj.name}")


def main():
    canales = json.loads((ROOT / "canales.json").read_text())
    ahora = datetime.now(timezone.utc)
    pendientes = []
    for canal, cfg in canales.items():
        if canal.startswith("_") or not cfg.get("activo"):
            continue
        for gj in sorted((ROOT / "canales" / canal / "proyectos").glob("*/guion.json")):
            proj = gj.parent
            if (proj / "publicado.json").exists():
                continue
            g = json.loads(gj.read_text())
            fp = fecha_pub(g)
            if fp <= ahora + timedelta(hours=VENTANA_HORAS):
                pendientes.append((fp, canal, cfg, proj, g))
    pendientes.sort(key=lambda x: x[0])
    print(f"Pendientes en ventana: {len(pendientes)}")
    hechos, fallos = [], []
    for fp, canal, cfg, proj, g in pendientes[:MAX_POR_CORRIDA]:
        if not token_file(canal, cfg):
            fallos.append(f"{canal}: falta el secreto {cfg['secreto']}")
            continue
        env = dict(os.environ)
        env["TTS_MOTOR"] = cfg.get("tts", "piper")
        if env["TTS_MOTOR"] == "edge":
            env["EDGE_VOICE"] = cfg.get("voz", "es-MX-JorgeNeural")
        else:
            env["PIPER_VOZ"] = cfg.get("voz", "vits-piper-es_MX-claude-high")
        if g.get("tipo") == "short":
            env["VERTICAL"] = "1"
        else:
            env.pop("VERTICAL", None)
        offline = [] if env.get("PEXELS_API_KEY") else ["--offline"]
        if fp < ahora and g.get("seo", {}).get("publicar_en"):
            g["seo"]["publicar_en"] = None  # ya pasó la hora: se publica de inmediato
            g["seo"]["privacidad"] = "public"
            (proj / "guion.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
        try:
            print(f"### {canal} · {proj.name}", flush=True)
            run("validate.py", proj, env)
            run("tts.py", proj, env)
            run("visuals.py", proj, env, *offline)
            run("render.py", proj, env)
            run("thumbnail.py", proj, env)
            run("metadata.py", proj, env)
            run("upload.py", proj, env, "--canal", canal)
            shutil.copy(proj / "salida" / "publicado.json", proj / "publicado.json")
            hechos.append(f"{canal}: {proj.name} → {json.loads((proj / 'publicado.json').read_text())['url']}")
        except Exception as e:  # sigue con el siguiente
            msg = str(e)
            fallos.append(f"{canal}: {proj.name}: {msg}")
            print("FALLO", msg, flush=True)
            if "quota" in msg.lower():
                break
        finally:
            for sub in ("audio", "imagenes", "tmp", "salida"):
                shutil.rmtree(proj / sub, ignore_errors=True)
            (proj / "creditos.json").unlink(missing_ok=True)
    rep = ROOT / "reporte.md"
    rep.write_text(f"# Último reporte ({ahora:%Y-%m-%d %H:%M} UTC)\n\n## Subidos\n"
                   + "".join(f"- {h}\n" for h in hechos) + "\n## Fallos\n" + "".join(f"- {f}\n" for f in fallos))
    print(rep.read_text())


if __name__ == "__main__":
    main()
