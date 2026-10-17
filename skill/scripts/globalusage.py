#!/usr/bin/env python3
"""globalusage: cuota de todas las suscripciones (Claude, Codex, Antigravity) sin gastar tokens de modelo.
Uso: globalusage [--guardado]
Por defecto lee la cuota EN VIVO (unos 4 s; caché de 20 s). --guardado muestra la última medición del temporizador horario.
Cada cuenta muestra, para la ventana de 5 horas y la de la semana, el uso y cuándo se renueva (en cuánto tiempo y fecha/hora
de Colombia, America/Bogota), más la edad de su medición."""
import datetime as dt, json, subprocess, sys, pathlib

STATE = pathlib.Path.home() / "bitacora/.state"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def leer_en_vivo():
    """Lee ahora mismo la cuota de cada cuenta Claude/Codex (solo lectura, sin llamar al modelo ni renovar credenciales).
    No toca el almacén del temporizador horario ni su límite de una lectura por hora. Cada cuenta falla por separado."""
    import bt_quota_live
    return bt_quota_live.read_all_live()


def leer_guardado():
    cmd = ["python3", str(pathlib.Path(__file__).resolve().parent / "bitacora.py"), "usage", "show"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout)


try:
    rows = leer_guardado() if "--guardado" in sys.argv else leer_en_vivo()
    if "--guardado" not in sys.argv and any(r["status"] != "ok" for r in rows):
        # una cuenta falló en vivo (p. ej. http_429): se muestra su última medición guardada, marcada con el error
        try:
            guardadas = {r["profile"]: r for r in leer_guardado()}
        except Exception:
            guardadas = {}
        rows = [({**guardadas[r["profile"]], "status": f"guardada; en vivo: {r['status']}"}
                 if r["status"] != "ok" and r["profile"] in guardadas and guardadas[r["profile"]].get("windows") else r)
                for r in rows]
except Exception as e:
    print(f"(lectura en vivo falló: {type(e).__name__}; uso la última medición guardada)", file=sys.stderr)
    try:
        rows = leer_guardado()
    except Exception as e2:
        sys.exit(f"no pude leer el uso: {e2}")

try:
    from zoneinfo import ZoneInfo
    BOGOTA = ZoneInfo("America/Bogota")
except Exception:  # sin base tz: Colombia es UTC-5 todo el año
    BOGOTA = dt.timezone(dt.timedelta(hours=-5), "COT")
DIAS = ("lun", "mar", "mié", "jue", "vie", "sáb", "dom")
MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
DIM, BOLD, RST = "\033[2m", "\033[1m", "\033[0m"


def ahora():
    return dt.datetime.now(BOGOTA)


def barra(p, ancho=20):
    n = round(p / 100 * ancho)
    c = "\033[31m" if p >= 85 else "\033[33m" if p >= 60 else "\033[32m"
    return f"{c}{'█' * n}{'░' * (ancho - n)}{RST} {p:5.1f}%"


def duracion(seg):
    """'2 d 4 h 12 min', 'en 3 h 05 min', 'en 12 min' (solo las unidades que importan)."""
    m = max(0, int(seg // 60))
    d, resto = divmod(m, 1440)
    h, mi = divmod(resto, 60)
    if d:
        return f"{d} d {h} h {mi:02d} min"
    return f"{h} h {mi:02d} min" if h else f"{mi} min"


def fecha(ts):
    d = dt.datetime.fromtimestamp(ts, BOGOTA)
    return f"{DIAS[d.weekday()]} {d.day} {MESES[d.month - 1]} {d:%H:%M}"


def cuando(ts):
    """'en 2 d 4 h 12 min  ·  dom 18 oct 13:59' en hora de Colombia."""
    return f"en {duracion(ts - ahora().timestamp())}  ·  {fecha(ts)}"


def perfil_actual():
    """Perfil desde el que corre esta sesión (ver bt_quota_live.current_profile)."""
    import bt_quota_live
    return bt_quota_live.current_profile()


ACTUAL = perfil_actual()


def _alias():
    """Perfiles que comparten cuenta con otro perfil ya mostrado (bt_agents.account_key), p. ej. claude = claude-personal."""
    try:
        import bt_agents, bt_profiles
        vistos, alias = {}, set()
        for pid in sorted(bt_profiles.load(), key=lambda x: (x in ("claude", "codex"), x)):
            k = bt_agents.account_key(pid)
            if k in vistos:
                alias.add(pid)
            vistos[k] = pid
        return alias
    except Exception:
        return {"claude", "codex"}


ALIAS = _alias()


def edad(ts):
    if not ts:
        return "?"
    m = round((dt.datetime.now().timestamp() - ts) / 60)
    return f"{m} min" if m < 90 else f"{m // 60} h"


def ventana(etiqueta, x):
    """Una línea por ventana: barra, % usado y cuándo se renueva (en cuánto tiempo y fecha/hora de Colombia)."""
    usado, reset = (x or {}).get("used_percent"), (x or {}).get("resets_at")
    if usado is None:
        return f"    {etiqueta:<8} {DIM}sin datos{RST}"
    if reset is None:
        return f"    {etiqueta:<8} {barra(usado)}   renueva: {DIM}la API no lo informó{RST}"
    if reset < ahora().timestamp():  # la medición es anterior a la renovación de la ventana
        return f"    {etiqueta:<8} {DIM}ya se renovó (dato viejo, último {usado:.0f}%){RST}"
    return f"    {etiqueta:<8} {barra(usado)}   renueva {BOLD}{cuando(reset)}{RST}"


def bloque(nombre, w, medido, estado="ok"):
    marca = nombre == ACTUAL
    titulo = f"\033[1;7m ▶ {nombre} {RST}" if marca else f"{BOLD}  {nombre}{RST}"
    nota = "" if estado == "ok" else f"  {DIM}[{estado}]{RST}"
    print(f"{titulo}  {DIM}medido hace {edad(medido)}{RST}{nota}{'  ◀ esta sesión' if marca else ''}")
    print(ventana("5 horas", (w or {}).get("five_hour")))
    print(ventana("semana", (w or {}).get("seven_day")))
    print()


print(f"{BOLD}Uso de suscripciones{RST}  {DIM}{ahora():%d/%m/%Y %H:%M} hora Colombia (UTC-5){RST}\n")
for r in rows:
    if r["profile"] in ALIAS:
        continue  # alias de otra cuenta (misma cuenta registrada dos veces)
    bloque(r["profile"], r.get("windows", {}), r.get("observed_at"), r["status"])
try:
    a = json.loads((STATE / "agy-usage.json").read_text())
    bloque("antigravity", a["windows"], a["observed_at"])
except Exception:
    print(f"{BOLD}  antigravity{RST}  {DIM}sin medición{RST}\n")

hoy = dt.date.today().isoformat()
import bt_events
t = bt_events.summary([r for r in bt_events.read_all() if str(r.get("ts") or "").startswith(hoy)],
                      ("agent", "model"))
if t:
    print(f"{BOLD}Hoy por modelo{RST}  intentos · verificados · tokens medidos · costo reportado · cobertura tokens/costo")
    for g in t:
        k = f"{g['agent']}/{g['model']}"
        tokens = f"{g['tokens_measured'] / 1000:.0f}k" if g["measured"] else "—"
        usd = g["cost_usd_reported"]
        cost = f"US${usd:.2f}" if usd is not None else "—"
        coverage = f"{g['measured']}/{g['attempts']} · {g['cost_measured']}/{g['attempts']}"
        print(f"{k:<28} {g['attempts']:>3} · {g['done']:>3} · {tokens:>8} · {cost} · {coverage}")
