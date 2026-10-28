"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { reviewFixture } from "./review-fixture";
import { redactReviewText } from "./review-text.mjs";
import styles from "./review.module.css";
import { parseFailureReview, parseSnapshot } from "../remote-contract";

type FailureReview = { run: string; task: string; attempt: string; cause: string; verificationOutput: string; diffStat: string; logTail: string };

/** The run task's latest failed attempt, from the gateway snapshot contract. */
function attemptFromSnapshot(value: unknown, project: string, req: string, taskId: string): string | null {
  const run = parseSnapshot(value).runs.find((item) => item.project === project && item.req === req);
  return run?.tasks.find((item) => item.id === taskId)?.reviewAttempt?.id ?? null;
}

function reviewFromResponse(value: unknown, run: string, task: string): FailureReview {
  const review = parseFailureReview(value);
  const verificationOutput = [review.verification.command, review.verification.output].filter(Boolean).join("\n")
    || "Sin salida de verificación disponible.";
  return { run, task, attempt: review.attemptId, cause: review.cause, verificationOutput,
    diffStat: review.diff.stat || "Sin estadística del diff disponible.", logTail: review.logTail || "Sin líneas de log disponibles." };
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
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const legacyAttempt = window.location.hash.startsWith("#attempt-")
      ? decodeURIComponent(window.location.hash.slice("#attempt-".length))
      : null;
    const fragmentAttempt = fragment.get("attempt") ?? fragment.get("attemptId") ?? legacyAttempt;
    if (!fragmentAttempt && (!project || !req || !taskId)) return;
    let active = true;
    setLoading(true);
    const attemptIdPromise = fragmentAttempt
      ? Promise.resolve(fragmentAttempt)
      : fetch("/api/remote/v1/snapshot", { cache: "no-store" }).then(async (response) => {
        if (!response.ok) throw new Error("Snapshot unavailable");
        return attemptFromSnapshot(await response.json() as unknown, project!, req!, taskId!);
      });
    void attemptIdPromise.then(async (attemptId) => {
        if (!attemptId || !project || !req) return null;
        const target = `${project}/${req}`;
        const detailResponse = await fetch(`/api/remote/v1/attempts/${encodeURIComponent(attemptId)}/review?target=${encodeURIComponent(target)}`, { cache: "no-store" });
        if (!detailResponse.ok) throw new Error("Review unavailable");
        return reviewFromResponse(await detailResponse.json() as unknown, req, taskId ?? "");
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
          <ReviewSection title="Causa">{review.cause}</ReviewSection>
          <ReviewSection title="Salida de verificación">{review.verificationOutput}</ReviewSection>
          <ReviewSection title="Estadística del diff">{review.diffStat}</ReviewSection>
          <ReviewSection title="Final del log">{review.logTail}</ReviewSection>
        </div>
      </article>
      <footer className="footer"><span>FLOW REMOTE</span><span>REVISIÓN DE INTENTO</span></footer>
    </main>
  );
}
