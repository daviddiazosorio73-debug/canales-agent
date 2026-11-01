"""Vigía de la semana (sin Claude): comprueba que la semana que empieza tenga guiones en cada canal.

Uso: python scripts/vigia_semana.py [AAAA-MM-DD]   (domingo de inicio; por defecto, el próximo domingo en Lima)
Sale con error (GitHub avisa por correo) si falta algún día o tipo. Cryptuline se revisa con 1 semana de adelanto.
"""
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


def main():
    if len(sys.argv) > 1:
        inicio = date.fromisoformat(sys.argv[1])
    else:
        hoy = (datetime.now(timezone.utc) - timedelta(hours=5)).date()
        inicio = hoy + timedelta(days=(6 - hoy.weekday()) % 7 or 7)
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
