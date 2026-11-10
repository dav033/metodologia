# Follow-up prompt: balloon count (REQ-026), after session 00431355 (2026-11-10)

Paste this into a new session started in `~/dev/pictures-wt/conteo-entrenamiento`:

---

Continue the automatic balloon count of Pictures (REQ-026). Talk to me in Spanish; I do not want permission questions (see the memory `pictures-sin-pedir-permiso`). Read these first:
`~/dev/pictures-infra/conteo/lab/LEEME.md` (all rounds, «Adopted» sections and sealed-check notes), decisions D-107, D-108 and D-109 in `~/bitacora/pictures/DECISIONS.md`, pending items P-313 and P-314, and the memories `pictures-3010-main`, `pictures-conteo-agresivo` and `pictures-subagentes-cuentas`.

## State in production (main 11648eaed, Vercel; VPS `pictures-conteo:2`)
- Automatic count = detector t2 + CountGD, blended 70/30 (VPS service `pictures-conteo`, image `:2`). Image `:3`, which adds CountGD++, is built but not live: it took about 60 s per photo against the web's 60 s deadline, so it was rolled back to `:2`.
- Contador: three large cards **Bajo / Normal / Alto** (×0.956 / ×1.02 / ×1.07) above the photo. One count brings all three totals (`totalesGrosor`), and switching does not recount. The band is ±30 %.
- Corrections are open to every role with the Contador (fixed today; before, only admins could send them). Admin › Subidas keeps every Contador photo.
- localhost:3010 runs `~/dev/pictures-wt/main-local`. After each push to main, run `~/dev/pictures-infra/actualizar-main-local.sh`. The render worker stays in the pilot worktree; do not touch it.

**Coordination:** another Claude session (pilot-d1) also works on the count. It ran its own speed lane, `lab/al-velocidad`, and made 92a5a3baf, 0a5c44cff and main 2ec2c87d7. Before touching the VPS service `pictures-conteo`, tell it (or check `ListAgents`) so you do not both redeploy. Always merge origin/main before pushing.

## Pending, in order
1. **CountGD++ speed (lane `an` finished, `lab/an-velocidad/REPORTE.md`).** CountGD and CountGD++ share identical backbone weights; `velocidad.diff` shares the Swin-B pass with 0 count drift and about 0.55x the counters' time. The estimate on the VPS is about 35 s, or about 30 s with `torch.compile`.
   - Apply the patch to `scripts/conteo-vision/conteo_countgd.py` and `servicio_yolo.py`, turn CountGD++ on, rebuild `pictures-conteo:3` on the VPS (`/opt/pictures-conteo/build`, back up `compose.yml` first) and measure the real latency with 3 photos.
   - If it stays under about 40 s, raise the web's `PLAZO_MS` in `src/lib/contador/foto-yolo.ts` to 75 s (the route's `maxDuration` is 75) and switch to it. Otherwise try `torch.compile`, or leave it off.
   - Evidence for the three-way blend: −1.52 MAPE points on 234 real photos, nothing fitted on them (lab `ak-contadores-abiertos`).
   - The CountGD++ code is already in main (92a5a3baf) but switched off (0a5c44cff). To turn it on, add `--countgdpp-codigo /opt/countgdpp --countgdpp-pesos /modelo/countgdpp` to the command; the weights are already in `/opt/pictures-conteo/modelo/countgdpp/`.
2. **Real-session check (P-313).** Ask me for access to `davidt@sempertex.com`; do not reset its password. Then check Admin › Subidas, a correction sent by an internal employee, and the thickness cards in production.
3. **Clean real truth (P-314).** When there are about 50 corrections in `contador_correcciones` (or about 40 cases in `lab/datos/web_reservado4.jsonl`), recalibrate production's mapper and the thickness factors with that truth, and judge the frozen candidates once.
4. **Optional:** hand-label the thickness of about 40 real photos so a thickness predictor can be judged. Lane `as` showed that predicting thickness from the image fails on real photos (29.8 % against 28.3 % for always-Bajo).

## Lessons that must not be lost
- What is fitted on renders on a black background, or on the totals that decorators state on the web, does not hold on sealed real photos. Front-view renders in a room do behave like real photos (`lab/ao-mas-renders`, `ar-grosor-sala`).
- Seed luck in the detector is bigger than the 1.5-point bar. Judge any new detector over several seeds or many real photos.
- Collection agents that use web search stall in long commands. Give them short runs (≤15 cases, ≤40 min, commands <60 s). Web sources are close to exhausted: 429, 403 and DuckDuckGo bot checks.
- Visual pages: the box gallery is at http://localhost:8130/ and the thickness page at http://localhost:8130/grosor.html (`~/dev/pictures-infra/conteo/galeria`, `generar.py` and `grosor_datos.py`).

---
