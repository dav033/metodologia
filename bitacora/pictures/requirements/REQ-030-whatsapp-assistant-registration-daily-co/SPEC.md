---
id: REQ-030
status: in-progress
created: 2026-11-11
track: quick
---
# REQ-030 — WhatsApp assistant: registration, daily conversation limit, palette advice, background prompts

## Problem & goal
The live WhatsApp channel (`pictures-whatsapp-bot`, `services/telegram-globos`, sketch mode on, open to anyone) feels like a
menu bot: free text outside a sketch shows the menu, typed event descriptions at the colour step are rejected as unknown
colours, typed place descriptions at the place step get «Elige una opción», and described backgrounds are weakly honoured
in the generated picture. Anyone can use it anonymously and without a daily conversation bound.

Owner's /goal (2026-11-11, verbatim intent): make it an assistant instead of a bot; recommend several colour palettes as the
web does; make the prompt honour the person's background descriptions; limit to 5 conversations per user/number per day;
ask for email and name first, linked to the number and stored in a database — without them nothing works. Use Codex Terra
medium and the normal Claude account as subagents.

**Success looks like:** an unregistered number can only register; a registered number gets a warm, named assistant that
understands free text, proposes up to 3 Sempertex palettes from an event description, uses typed place descriptions in the
picture, and is cut at the 6th conversation of the Bogotá day.

## Decisions (made without asking, owner's standing autonomy instruction; recorded as D-111)
1. **Registration (gate before everything).** Unknown number → ask name, then email. Stored in the production Postgres
   (`pictures`, table `whatsapp_contactos`, migration 063): phone digits in clear (null for BSUID users), keyed hash of the
   WhatsApp id (unique), name, lower-cased email, `account_id` linked when a Pictures account has that email (case-insensitive),
   timestamps. No account is created or invited. Without both fields: no count, no sketch, no assistant. DB unreachable →
   short «no puedo atenderte ahora», nothing else (fail closed). Bot connects with its own least-privilege role
   (`WHATSAPP_DATABASE_URL`, role `whatsapp_bot`, created ops-side; the migration grants only if the role exists).
2. **Conversation = session.** A message from a registered number starts a new conversation when that number sent nothing in
   the previous 30 min or on a new Bogotá day. `DAILY_CONVERSATIONS_PER_USER` (default 5). The blocked conversation gets one
   polite message; following messages in the same window get silence. `WHATSAPP_ADMIN_NUMBERS` are exempt. Registration
   exchanges do not count. Counted in the bot's SQLite.
3. **Palettes.** Free text at the colour step that is not fully a colour list is an event description → up to 3 palettes from
   the web's palette-advice domain (`adviceInstruction`/`readAdvice`, real chart codes only), shown with the existing palette
   card and a list (reason as row description), plus «Otras paletas» and the starters. The same from a free-text request
   outside a sketch («un baby shower de osos»).
4. **Assistant.** Copy rewritten warm and first-person, uses the registered first name. Free text outside a sketch goes to a
   Gemini text call (gemini-3.6-flash, JSON schema) that classifies intent (sketch / count / help / question / greeting) and
   writes a short reply; the bot acts on the intent deterministically. The model grants nothing; on failure → menu. Own daily
   counter for text calls.
5. **Backgrounds.** At the place step any typed text that is not an option is the description (no need to press «Lo describo»),
   up to 300 chars. The description is rewritten by the text model into a concise English scene that keeps every element the
   person asked for (fallback: the raw text), and a bot-side prompt (`wa-sketch-described.v2`) puts the background instruction
   first-class: replace the sketch's plain background entirely with that scene, every requested element visible, balloons
   untouched. The web's prompt is not changed.

## Out of scope
- Turning on the full guided conversation (`CONVERSATION_BASE_URL`), creating Pictures accounts, sending emails, verifying
  email ownership, the Vercel `/api/whatsapp/webhook` path.

## Edge cases & errors
- BSUID senders (hidden number): registered with phone null. Invalid email → asked again with an example. A name that is
  a greeting/command («hola», «menú») is not taken as a name. Duplicate deliveries are deduplicated as today.
- Text-model failure or quota: palettes fall back to the starters; place description falls back to the raw text; free text
  falls back to the menu.

## Constraints
- Phone numbers never in logs (hashed id only). No images stored. Deadlines on every external call.
- Rollback: env flags off / previous image; migration additive.
