"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { reviewFixture } from "./review-fixture";
import { redactReviewText } from "./review-text.mjs";
import styles from "./review.module.css";

type FailureReview = { run: string; task: string; attempt: string; cause: string; verificationOutput: string; diffStat: string; logTail: string };

function object(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null;
}

function stringField(value: Record<string, unknown>, camel: string, snake: string): string | undefined {
  const field = value[camel] ?? value[snake];
  return typeof field === "string" ? field : undefined;
}

function attemptFromSnapshot(value: unknown, project: string, req: string, taskId: string): string | null {
  const snapshot = object(value);
  if (!snapshot || !Array.isArray(snapshot.runs)) return null;
  const run = snapshot.runs.map(object).find((item) => item?.project === project && item.req === req);
  const tasks = run && Array.isArray(run.tasks) ? run.tasks.map(object) : [];
  const task = tasks.find((item) => item?.id === taskId);
  const attempt = task && object(task.reviewAttempt ?? task.review_attempt);
  return attempt ? stringField(attempt, "id", "attempt_id") ?? stringField(attempt, "attemptId", "attempt_id") ?? null : null;
}

function reviewFromResponse(value: unknown, run: string, task: string): FailureReview | null {
  const response = object(value);
  const verification = object(response?.verification);
  const diff = object(response?.diff);
  const attempt = response && stringField(response, "attemptId", "attempt_id");
  const cause = response && stringField(response, "cause", "cause");
  const verificationOutput = verification
    ? [stringField(verification, "command", "command"), stringField(verification, "output", "output")].filter(Boolean).join("\n") || "Sin salida de verificación disponible."
    : "Sin salida de verificación disponible.";
  const diffStat = (diff && stringField(diff, "stat", "stat")) || "Sin estadística del diff disponible.";
  const logTail = (response && stringField(response, "logTail", "log_tail")) || "Sin líneas de log disponibles.";
  if (!attempt || !cause) return null;
  return { run, task, attempt, cause, verificationOutput, diffStat, logTail };
}

function ReviewSection({ title, children }: { title: string; children: string }) {
  return (
    <section className={styles.section} aria-label={title}>
      <h2>{title}</h2>
      <pre className={styles.output}>{redactReviewText(children)}</pre>
    </section>
  );
}

export default function ReviewPage() {
  const [review, setReview] = useState<FailureReview>({ ...reviewFixture, run: reviewFixture.run, task: reviewFixture.task });
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const project = params.get("project");
    const req = params.get("req");
    const taskId = params.get("taskId");
    if (!project || !req || !taskId) return;
    let active = true;
    setLoading(true);
    void fetch("/api/remote/v1/snapshot", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Snapshot unavailable");
        const attemptId = attemptFromSnapshot(await response.json() as unknown, project, req, taskId);
        if (!attemptId) return null;
        const detailResponse = await fetch(`/api/remote/v1/attempts/${encodeURIComponent(attemptId)}/review`, { cache: "no-store" });
        if (!detailResponse.ok) throw new Error("Review unavailable");
        return reviewFromResponse(await detailResponse.json() as unknown, req, taskId);
      })
      .then((value) => {
        if (!active) return;
        if (value) setReview(value);
        else setUnavailable(true);
      })
      .catch(() => { if (active) setUnavailable(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Flow Remote, inicio">
          <span className="brand-mark" aria-hidden="true">F</span>
          <span>flow<span className="brand-muted">/remote</span></span>
        </Link>
        <Link className={styles.back} href="/">Volver a ejecuciones</Link>
      </header>
      <article className={styles.content} aria-labelledby="review-title">
        <p className="eyebrow">{review.run === reviewFixture.run ? "DATOS DE MUESTRA" : redactReviewText(review.run)} · {redactReviewText(review.task)}</p>
        <h1 id="review-title">Intento fallido</h1>
        <p className={styles.attempt}>{redactReviewText(review.attempt)}</p>
        {loading && <p role="status">Cargando revisión…</p>}
        {unavailable && <p className="error" role="status">La revisión de este intento no está disponible.</p>}
        <div className={styles.sections}>
          <ReviewSection title="CAUSA">{review.cause}</ReviewSection>
          <ReviewSection title="SALIDA DE VERIFICACIÓN">{review.verificationOutput}</ReviewSection>
          <ReviewSection title="ESTADÍSTICA DEL DIFF">{review.diffStat}</ReviewSection>
          <ReviewSection title="FINAL DEL LOG">{review.logTail}</ReviewSection>
        </div>
      </article>
      <footer className="footer"><span>FLOW REMOTE</span><span>REVISIÓN DE INTENTO</span></footer>
    </main>
  );
}
