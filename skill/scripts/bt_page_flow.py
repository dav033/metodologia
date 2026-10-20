"""`/flow`: how the Planner and the Scheduler modules talk, for one run at a time. Pure function: scope in, HTML out.
The drawing and the live stream are `assets/flow-core.js` (decisions) and `assets/flow.js` (DOM); this page only
supplies the frame, the controls and the `data-scope` they read. `?scope=` is global | project:P | run:P/REQ | task:P/REQ/T.

Reading order: the run and its state in one sentence, the task strip, then the map beside the messages. Provider-level
detail (the raw stream, info-only incidents) arrives folded into one digest per attempt and stays hidden until asked for.
"""
from __future__ import annotations

from html import escape as e

from bt_pages import layout

# category class -> what the chip says; the same classes colour the map, the feed and the trace (flow-core.js CATEGORIES)
CATEGORIES = (("k-plan", "plan y asignación"), ("k-run", "ejecución"), ("k-verify", "verificación"),
              ("k-recover", "recuperación"), ("k-state", "estados"), ("k-warn", "avisos"), ("k-bad", "fallos y bloqueos"))
TASK_KEY = (("k-verify", "aceptada"), ("k-run", "en curso"), ("k-recover", "reintentando"), ("k-bad", "bloqueada"),
            ("k-state", "pendiente"))


def flow_page(scope: str = "global", sim: str = "metodologia/REQ-026", token: str = "") -> str:
    """`sim` = project/REQ whose plan «Simular» runs on the core's doubles (default: the DEMO plan)."""
    key = "".join(f'<span class="{cls}"><i></i>{e(text)}</span>' for cls, text in TASK_KEY)
    label = {"global": "todas las ejecuciones"}.get(scope, scope.replace(":", " · "))
    body = f"""<link rel="stylesheet" href="/static/flow.css"><div class="head"><div><p class="eyebrow" id="fl-eyebrow">flujo · {e(label)}</p><h1>Cómo hablan los módulos</h1></div>
<div class="fl-ctrl"><div class="fl-seg" role="group" aria-label="Modo">
<button type="button" id="flow-live" class="on"><i class="fl-dot"></i>En vivo</button><button type="button" id="flow-replay">Repetir</button></div>
<details class="fl-more"><summary>Más</summary><div class="fl-menu">
<button type="button" id="flow-pause">Pausar animación<small>Deja quietas las partículas del mapa</small></button>
<button type="button" id="flow-sim" data-sim="{e(sim)}">Simular<small>Corre el plan {e(sim)} con dobles de M2–M5, sin proveedores ni escribir nada</small></button>
</div></details></div></div>
<div id="flow" class="flowpage" data-scope="{e(scope)}" data-token="{e(token)}">
<section class="fl-runs" id="fl-runs" aria-label="Ejecuciones"><p class="muted">Cargando ejecuciones…</p></section>
<p class="fl-now" id="fl-now" aria-live="polite"></p>
<section class="fl-tasks" id="fl-tasks-box" aria-label="Tareas" hidden>
<div class="fl-row"><h2>Tareas</h2><div class="fl-key">{key}</div><span class="fl-hint">clic en una tarea para seguir su recorrido</span></div>
<div class="fl-chips" id="fl-tasks"></div></section>
<section class="fl-decisions" id="fl-decisions" aria-live="polite" hidden></section>
<section class="fl-stage">
<div class="fl-mapcard"><div class="fl-live" id="fl-live" aria-live="polite" hidden></div><div class="fl-crumbs" id="fl-crumbs"></div>
<div class="fl-mapwrap" id="flow-map"></div>
<div class="fl-replay" id="flow-replaybar" hidden><button type="button" class="fl-btn" id="flow-play">▶ Reproducir</button>
<input type="range" id="flow-seek" min="0" max="1000" value="0" aria-label="Línea de tiempo">
<span id="flow-clock" class="fl-clock">0,0 / 0,0 s</span>
<div class="fl-seg" role="group" aria-label="Velocidad"><button type="button" data-speed="1">1×</button><button type="button" data-speed="5" class="on">5×</button>
<button type="button" data-speed="20">20×</button></div></div></div>
<aside class="fl-panel"><div class="fl-tabs" role="tablist">
<button type="button" role="tab" id="fl-tab-feed" class="on">Mensajes<span class="fl-count" id="fl-feed-n"></span></button>
<button type="button" role="tab" id="fl-tab-trace">Recorrido<span class="fl-count" id="fl-trace-n"></span></button></div>
<div class="fl-pane" id="fl-pane-feed"><div class="fl-cats" id="fl-cats"></div>
<label class="fl-detail"><input type="checkbox" id="fl-detail"> Mostrar detalle del proveedor <span id="fl-detail-n"></span></label>
<ul class="fl-feed" id="flow-feed-list"></ul></div>
<div class="fl-trace" id="fl-trace" hidden></div></aside>
</section></div>
<noscript><p class="muted">Esta vista necesita JavaScript.</p></noscript>
<script src="/static/flow-core.js"></script><script src="/static/flow-failure-links.js"></script>
<script src="/static/flow.js"></script><script src="/static/flow-decisions.js"></script>"""
    return layout("Flujo", body, [("Flujo", "/flow")])
