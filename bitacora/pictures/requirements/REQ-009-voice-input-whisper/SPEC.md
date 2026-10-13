---
id: REQ-009
status: done 2026-10-11 (merged fb8477b6; VOZ_* flags unconfirmed)
track: quick
---
# REQ-009 — Voice input everywhere there is free text (Whisper)

Owner (2026-10-09): "mete a Whisper donde haya input de texto". Benchmark (same day): faster-whisper `small` + business
vocabulary prompt on advin-vps CPU: ~3 s per spoken command, 0.6 GB, noisy WER 0.04 (synthetic audio; validate with
real notes).

## Design
- **VPS `voz` service** (isolated compose project, like /opt/modelos-prueba): FastAPI + faster-whisper small (int8,
  pinned av==18.1.0), vocabulary prompt (Sempertex/decor terms), Spanish, max 60 s audio, concurrency 1–2 with a short
  queue, memory/cpu limits; HMAC-signed requests (shared secret, timestamp, replay window); published through Caddy on
  its own sslip host; health endpoint. Never touches demo-decoracion-ai-api.
- **Next route `/api/voz/transcribir`**: session-authenticated, rate-limited, size/duration limits, forwards audio
  signed to the VPS, logs the call in the AI audit (provider "whisper-vps", cost 0, duration), stores no audio.
  Feature flag `VOZ_ENABLED` (off by default in prod until the owner tests).
- **Client `BotonVoz`**: MediaRecorder (webm/opus; fallback mp4 on iOS Safari), tap-to-talk with visible recording
  state and level, max 60 s, cancel, inserts the text at the caret (append), errors in Spanish, hidden when the browser
  has no mic or the flag is off. Accessible (aria-pressed, labels).
- **Where:** every free-text input where a sentence makes sense — Taller AI composer (desktop + phone), customer guided
  chat composer (/asistente), library search, scene name/notes if free text; not numeric fields.
- Privacy: audio never stored; only text and duration logged.
