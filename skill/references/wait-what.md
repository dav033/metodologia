# Wait, what: stop, restate the claim, wait

Source: mattpocock/skills@49dd158 (MIT), skills/productivity/wait-what/SKILL.md. Adapted here: an immediate
re-pitch of the last message using the project's glossary. Original here: the disputed claim is restated in at most
five plain Spanish sentences, no new action is taken, and the agent waits. Not imported: ASD-STE100 (an English
register standard; replaced by plain Spanish). License: `third-party-notices.md`.

## Load when

The owner signals the last message did not land or is being challenged: "wait what", "espera, ¿qué?", "no
entiendo", "no te entendí", "¿cómo así?", "eso no es lo que pedí", "¿por qué dices eso?". Load it at once, before
continuing whatever you were doing. It is a circuit breaker, not a planning flow.

## Do

1. **Stop.** Take no further action on the claim in dispute: no new tool calls, edits, commands or delegations
   that depend on it. Do not undo what is already done and do not kill running work without asking; say that
   it is still running if it is.
2. **Restate the disputed claim** in at most five plain Spanish sentences, in this order, skipping a step that does
   not apply:
   - what you said or proposed, in one sentence;
   - why, with the one fact or file that supports it;
   - what you would do next if it stands;
   - what is uncertain or assumed;
   - the single question you need answered, if any.
3. **Use the project's words.** Take domain terms from `GLOSSARY.md` when it exists; avoid your own jargon,
   file-internal names and abbreviations the owner never used. Short sentences, one idea each.
4. **Wait.** End the turn. Do not add options, a new plan or a list of alternatives, and do not apologise at length.
5. **Follow the answer.** If it shows you were wrong, say so in one sentence, correct it, and record the
   correction where it matters (day log; DECISIONS.md if a decision changed). If you were right, say so with the
   evidence and ask whether to continue. If the cause was a missing term, offer to add it to the glossary.

## Boundaries

- The `Aye` prefix and the Spanish rule still apply; five sentences is a ceiling, not a target.
- Do not turn it into a new interview round or a hidden approval gate; nothing here changes `requirements.md` or
  the plan gate.
- If the correction contradicts a standing rule (a permission, a no-push rule), follow
  `self-improvement.md` §When a user-controlled rule blocks the goal instead of silently complying.
- Do not repeat the original message louder. The point is a clearer restatement, not a longer one.
- Repeated occurrences of the same confusion are friction: log it with `bitacora.py learn add --scope skill|project
  --evidence ...` (`retro-feedback.md`), once, not on every instance.
