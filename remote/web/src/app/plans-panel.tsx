"use client";

import { useState } from "react";
import { answerDecisionCommand, answerRoundCommand, planCommand, runAction, type Command } from "../lib/commands";
import type { Decision, Plan, Round } from "../lib/snapshot";

type Send = (command: Command, key: string) => Promise<boolean>;
type Props = { plans: Plan[]; working: string; send: Send; prettyTime: (value?: string) => string };
type Answers = Record<string, { choice?: string; text?: string; note?: string }>;
const uuid = () => crypto.randomUUID();

function RoundForm({ plan, round, working, send }: { plan: Plan; round: Round; working: string; send: Send }) {
  const [answers, setAnswers] = useState<Answers>({});
  const complete = round.questions.every((question) => question.type === "choice" ? !!answers[question.id]?.choice : !!answers[question.id]?.text?.trim());
  const patch = (id: string, value: Answers[string]) => setAnswers((current) => ({ ...current, [id]: { ...current[id], ...value } }));
  return <form className="round-form" aria-label={`Ronda ${round.round}`} onSubmit={(event) => { event.preventDefault(); void send(answerRoundCommand(plan, round, answers, uuid()), `${plan.req}-round-${round.round}`); }}>
    <h4>Ronda {round.round} · {round.title}</h4>{round.intro && <p>{round.intro}</p>}
    {round.questions.map((question) => <fieldset key={question.id}><legend>{question.text}</legend>
      {question.why && <p className="last-seen">{question.why}</p>}
      {question.type === "choice" ? question.options.map((option) => <label key={option.key} className="choice"><input type="radio" name={`${plan.req}-${round.round}-${question.id}`} checked={answers[question.id]?.choice === option.key} onChange={() => patch(question.id, { choice: option.key })} />{option.label}{question.recommended === option.key ? " · recomendada" : ""}</label>)
        : <textarea aria-label={question.text} placeholder={question.suggested} value={answers[question.id]?.text ?? ""} onChange={(event) => patch(question.id, { text: event.target.value })} />}
      {question.type === "choice" && <input aria-label={`Nota para ${question.id}`} placeholder="Nota (opcional)" value={answers[question.id]?.note ?? ""} onChange={(event) => patch(question.id, { note: event.target.value })} />}
    </fieldset>)}
    <button disabled={!!working || !complete}>Enviar respuestas</button>
  </form>;
}

function DecisionCard({ plan, decision, working, send }: { plan: Plan; decision: Decision; working: string; send: Send }) {
  const [reason, setReason] = useState("");
  const needsReason = (option: string) => ["retry_with_note", "review_pass", "review_fail"].includes(option);
  return <article className="decision" aria-label={`Decisión ${decision.id}`}>
    <h4>{decision.title}</h4><p>{decision.what}</p>
    {decision.evidence.length > 0 && <ul>{decision.evidence.map((line) => <li key={line}>{line}</li>)}</ul>}
    <label>Razón (obligatoria en algunas opciones) <input value={reason} maxLength={2000} onChange={(event) => setReason(event.target.value)} /></label>
    <ul className="options">{decision.options.map((option) => <li key={option.id}><strong>{option.label}{decision.recommended === option.id ? " · recomendada" : ""}</strong><p>{option.consequence}</p>
      <button disabled={!!working || (needsReason(option.id) && !reason.trim())} onClick={() => void send(answerDecisionCommand(plan, decision, option.id, reason, uuid()), `${plan.req}-decision-${decision.id}`)}>{option.label}</button></li>)}</ul>
  </article>;
}

export function PlansPanel({ plans, working, send, prettyTime }: Props) {
  const [typed, setTyped] = useState<Record<string, string>>({});
  if (!plans.length) return null;
  return <section className="runs plans" aria-labelledby="plans-title"><div className="section-heading"><div><p className="eyebrow">REVISIÓN</p><h2 id="plans-title">Planes</h2></div></div>
    <div className="run-list">{plans.map((plan) => {
      const id = `${plan.project}/${plan.req}`;
      const value = typed[id] ?? "";
      const matches = value === plan.req;
      const action = runAction(plan);
      const confirmed = (type: "approve" | "launch" | "cancel-plan" | "delete-plan") => (event: React.FormEvent) => { event.preventDefault(); if (matches) void send(planCommand(type, plan, value, uuid()), `${plan.req}-${type}`); };
      return <article className="run-card" key={id}>
        <div className="run-top"><div><p className="eyebrow">{plan.project}</p><h3>{plan.req} · Plan{plan.title ? ` · ${plan.title}` : ""}</h3></div><span className="state">{plan.state}</span></div>
        <p className="last-seen">Última actividad · {prettyTime(plan.updatedAt)}{plan.progress ? ` · ${plan.progress.done}/${plan.progress.total} tareas` : ""}</p>
        {plan.rounds.map((round) => <RoundForm key={round.round} plan={plan} round={round} working={working} send={send} />)}
        {plan.decisions.map((decision) => <DecisionCard key={decision.id} plan={plan} decision={decision} working={working} send={send} />)}
        <div className="actions"><label>Escribe {plan.req} para confirmar <input aria-label={`Escribe ${plan.req} para confirmar`} value={value} onChange={(event) => setTyped((current) => ({ ...current, [id]: event.target.value }))} /></label>
          {action && <form onSubmit={confirmed(action)}><button className="primary" disabled={!!working || !matches}>{action === "approve" ? "Aprobar y ejecutar" : "Ejecutar"}</button></form>}
          <form onSubmit={confirmed("cancel-plan")}><button disabled={!!working || !matches}>Cancelar plan</button></form>
          <form onSubmit={confirmed("delete-plan")}><button className="danger" disabled={!!working || !matches}>Eliminar plan</button></form></div>
      </article>;
    })}</div></section>;
}
