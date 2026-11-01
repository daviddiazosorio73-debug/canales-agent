"""Vigía de la semana (sin Claude): comprueba que la semana que empieza tenga guiones en cada canal.

Uso: python scripts/vigia_semana.py [AAAA-MM-DD]   (domingo de inicio; por defecto, el próximo domingo en Lima)
Sale con error (GitHub avisa por correo) si falta algún día o tipo. Cryptuline se revisa con 1 semana de adelanto.
Con --indice (sábado 19:00 Lima): revisa que investigacion/leccion_*.json tenga verificado el tema de cada día de esa semana,
para que el Fundador lo envíe ANTES de la tarea del sábado (sin tema verificado no se escriben Shorts de Escuela Sabática).
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LARGOS = {  # weekday(): 0 = lunes … 6 = domingo
    "mayordom": {0: "sermon", 1: "analisis", 2: "sermon", 3: "analisis", 4: "sermon"},
    "escuela-sabatica-es": {},
    "escola-sabatina-pt": {},
    "cryptuline": {6: "divulgacion", 1: "divulgacion", 4: "divulgacion"},
}
ADELANTO = {"cryptuline": 7}


def tiene(canal, dia, tipo):
    base = ROOT / "canales" / canal / "proyectos"
    return any(base.glob(f"{dia.isoformat()}-*-{tipo}-*/guion.json"))


def indice(inicio):
    fechas = {}
    for f in sorted((ROOT / "investigacion").glob("leccion_*.json")):
        fechas.update(json.loads(f.read_text()).get("fechas", {}))
    faltan = [(inicio + timedelta(days=k)).isoformat() for k in range(7)
              if not (fechas.get((inicio + timedelta(days=k)).isoformat()) or {}).get("dia")]
    if faltan:
        print(f"FALTA el tema del día de la lección (Escuela Sabática) para: {', '.join(faltan)}.")
        print("leccion-semanal.yml no pudo leerlos de escuelasabaticamaestros.com: envía a Claude una foto de la lección (temas del domingo al viernes).")
        sys.exit(1)
    print(f"OK: temas del día verificados para la semana del {inicio}.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        inicio = date.fromisoformat(args[0])
    else:
        hoy = (datetime.now(timezone.utc) - timedelta(hours=5)).date()
        inicio = hoy + timedelta(days=(6 - hoy.weekday()) % 7 or 7)
    if "--indice" in sys.argv:
        return indice(inicio)
    faltan = []
    for canal, largos in LARGOS.items():
        ini = inicio + timedelta(days=ADELANTO.get(canal, 0))
        for k in range(7):
            dia = ini + timedelta(days=k)
            tipos = [f"short{n}" for n in (1, 2, 3)] + ([largos[dia.weekday()]] if dia.weekday() in largos else [])
            faltan += [f"{canal} {dia} {t}" for t in tipos if not tiene(canal, dia, t)]
    if faltan:
        print(f"FALTAN {len(faltan)} guiones para la semana del {inicio}:")
        print("\n".join(" - " + f for f in faltan))
        sys.exit(1)
    print(f"OK: semana del {inicio} completa en {len(LARGOS)} canales.")


if __name__ == "__main__":
    main()
