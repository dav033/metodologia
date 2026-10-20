// Builders for the plan-side commands of command.schema.json. They are pure so tests can check the exact wire shape.
import type { Decision, Plan, Round } from "./snapshot";

export type Command = Record<string, unknown>;
const base = (type: string, target: Record<string, unknown>, state: string, key: string): Command => ({
  schemaVersion: 1, idempotencyKey: `web-${key}`, type, target, precondition: { state },
});

export const roundId = (round: number) => `round-${String(round).padStart(2, "0")}`;
/** `approve` while the plan waits for review, `launch` once approved; anything else has no run button. */
export const runAction = (plan: Plan): "approve" | "launch" | null => plan.state === "review" ? "approve" : plan.state === "approved" && !plan.active ? "launch" : null;

export function planCommand(type: "approve" | "launch" | "cancel-plan" | "delete-plan", plan: Plan, typedReq: string, key: string): Command {
  return { ...base(type, { kind: "plan", project: plan.project, req: plan.req }, plan.state, key), confirmation: { typedReq } };
}

export function answerRoundCommand(plan: Plan, round: Round, answer: Record<string, { choice?: string; text?: string; note?: string }>, key: string): Command {
  return { ...base("answer-round", { kind: "round", project: plan.project, req: plan.req, roundId: roundId(round.round) }, plan.commandState ?? plan.runState ?? plan.state, key), answer };
}

export function answerDecisionCommand(plan: Plan, decision: Decision, option: string, reason: string, key: string): Command {
  return { ...base("answer-decision", { kind: "run", project: plan.project, req: plan.req }, plan.commandState ?? plan.runState ?? plan.state, key),
    requestId: decision.id, option, ...(reason.trim() ? { reason: reason.trim() } : {}) };
}

const taskTarget = (plan: { project: string; req: string }, taskId: string) => ({ kind: "task", project: plan.project, req: plan.req, taskId });

/** Retry a task; a `route` pins the route chosen from `GET /routes`, `reason` goes into the next attempt's prompt. */
export function retryCommand(run: { project: string; req: string; state: string }, taskId: string, route: string | undefined, reason: string, key: string): Command {
  return { ...base("retry", taskTarget(run, taskId), run.state, key), ...(route ? { route } : {}), ...(reason.trim() ? { reason: reason.trim() } : {}) };
}

export function noteCommand(run: { project: string; req: string; state: string }, taskId: string, note: string, key: string): Command {
  return { ...base("note", taskTarget(run, taskId), run.state, key), note: note.trim() };
}

/** Edit a task's brief: pinned to the plan's state and revision N; the laptop freezes revision N+1. */
export function editBriefCommand(plan: Plan, taskId: string, brief: string, criteria: string[], key: string): Command {
  const command = base("edit-brief", taskTarget(plan, taskId), plan.planCommandState ?? plan.state, key);
  return { ...command, precondition: { ...(command.precondition as object), ...(plan.planRevision === undefined ? {} : { revision: plan.planRevision }) },
    brief: brief.trim(), ...(criteria.length ? { acceptanceCriteria: criteria } : {}) };
}
