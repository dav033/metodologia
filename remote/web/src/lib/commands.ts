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
