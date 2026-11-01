# T3.15 preserved verification evidence

Source: the captured output log for attempt `pictures-REQ-021-r35-T3.11-a1-b576d185`; its handoff manifest records snapshot SHA `860f035eae5be26f75208b4fb14621bd18ada15f`, identical to the audited HEAD. This is historical same-snapshot evidence, not a fresh execution in T3.15. The project source checkout supplied to T3.15 is incomplete, so no application command was rerun here.

- `npx tsx scripts/test/test-glb-todos-los-tipos.ts` — exit 0; 53 element types and zero known structural defects.
- Blender 4.5.15 import (`verificar_glb.py`) and `comparar_glb.py` — exit 0; `GLB matches 53 element types within 1 mm and 1/255.`
- `npx tsx --conditions=react-server scripts/test/test-exportadores-escena-taller.ts` — exit 0; export test passed for expanded instance positions/colours and preserved editor scene.
- `npm run taller:test-harness-esenciales` — exit 0; harness assertions passed, including an invocation of the integration entry point with synthetic comparison failure, expected process exit 1, and evidence status `failed`.
- `python3 scripts/test/blender/test_comparar_glb.py` — exit 0; four tests passed.
- The original attempt output log is retained at `/home/david/dev/metodologia/bitacora/.state/durable/attempts-root/attempts/pictures-REQ-021-r35-T3.11-a1-b576d185/output.log`.
