#!/usr/bin/env python3
"""globalusage: cuota de todas las suscripciones (Claude, Codex, Antigravity) sin gastar tokens de modelo.
Uso: globalusage [--guardado]
Por defecto lee la cuota EN VIVO (unos 4 s; caché de 20 s). --guardado muestra la última medición del temporizador horario.
Cada fila muestra la edad de su medición."""
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

def barra(p):
    n = round(p / 10)
    c = "\033[31m" if p >= 85 else "\033[33m" if p >= 60 else "\033[32m"
    return f"{c}{'█' * n}{'░' * (10 - n)}\033[0m {p:5.1f}%"

def cuando(ts):
    d = dt.datetime.fromtimestamp(ts)
    hoy = d.date() == dt.date.today()
    return d.strftime("%H:%M" if hoy else "%a %H:%M")

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

def linea(nombre, w, extra=""):
    h, s = w.get("five_hour"), w.get("seven_day")
    def f(x):
        if not x:
            return "sin datos".ljust(28)
        if x["resets_at"] < dt.datetime.now().timestamp():  # la medición es de antes de que la ventana se renovara
            return f"\033[2m{'ventana renovada (dato viejo)':<28}\033[0m"
        return f"{barra(x['used_percent'])} ↺{cuando(x['resets_at']):<9}"
    marca = nombre == ACTUAL
    etiqueta = f"\033[1;7m▶ {nombre:<14}\033[0m" if marca else f"  {nombre:<14}"
    print(f"{etiqueta} 5h {f(h)} 7d {f(s)} {extra}{'  ◀ esta sesión' if marca else ''}")

print(f"\033[1mUso de suscripciones · {dt.datetime.now():%H:%M}\033[0m")
for r in rows:
    if r["profile"] in ALIAS:
        continue  # alias de otra cuenta (misma cuenta registrada dos veces)
    linea(r["profile"], r.get("windows", {}), f"· medido hace {edad(r.get('observed_at'))}" + ("" if r["status"] == "ok" else f" [{r['status']}]"))
try:
    a = json.loads((STATE / "agy-usage.json").read_text())
    linea("antigravity", a["windows"], f"· medido hace {edad(a['observed_at'])}")
except Exception:
    print(f"  {'antigravity':<14} sin medición")

hoy = dt.date.today().isoformat()
import bt_events
t = bt_events.summary([r for r in bt_events.read_all() if str(r.get("ts") or "").startswith(hoy)],
                      ("agent", "model"))
if t:
    print("\n\033[1mHoy por modelo\033[0m  intentos · verificados · tokens medidos · costo reportado · cobertura tokens/costo")
    for g in t:
        k = f"{g['agent']}/{g['model']}"
        tokens = f"{g['tokens_measured'] / 1000:.0f}k" if g["measured"] else "—"
        usd = g["cost_usd_reported"]
        cost = f"US${usd:.2f}" if usd is not None else "—"
        coverage = f"{g['measured']}/{g['attempts']} · {g['cost_measured']}/{g['attempts']}"
        print(f"{k:<28} {g['attempts']:>3} · {g['done']:>3} · {tokens:>8} · {cost} · {coverage}")
