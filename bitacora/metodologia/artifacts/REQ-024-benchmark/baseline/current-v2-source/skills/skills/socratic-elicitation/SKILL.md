---
name: socratic-elicitation
description: Clarifies material gaps in a requirement before planning. Use when scope, actors, success criteria, safety constraints, or edge cases remain unclear after codebase research.
---

Source: mthines/agent-skills@39b3f44 (MIT), `skills/analysis/interview/SKILL.md`. Adapted: research-first, adaptive clarification and explicit readiness. Original: the methodology's `requirements.md`, durable rounds, and owner approval flow own questions and requirement state; this skill adds no parallel brief format.

# Socratic elicitation for planning

Reach the readiness needed to draft a useful plan without repeating decisions or asking questions the repository can answer.

1. Read the user's request, prior answers, active `SPEC.md`, open rounds, project decisions, and relevant code before asking anything.
2. Separate observed facts, owner decisions, assumptions, and unknowns. Mark each unknown as blocking only when its answer would change scope, safety, architecture, acceptance, or the task graph.
3. Ask the owner only about blocking decisions that evidence cannot resolve. Use the existing `requirements.md` round format and persist answers through the existing requirement workflow; do not invent a second brief or questionnaire.
4. If the request is already actionable or the owner says to proceed with revisable assumptions, do not delay planning. Record each assumption and its consequence in the requirement artifacts and plan risks.
5. Stop with a concise list of blocking questions only when a missing owner decision would make a safe, scoped plan impossible.

Cover the requested outcome, affected users, scope and exclusions, success criteria, security/privacy constraints, and important failure or edge cases. Do not force a checklist item that does not apply.
