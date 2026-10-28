"use client";

import { useEffect, useState } from "react";
import type { FailureReview } from "../contract.generated";
import { parseFailureReview } from "./remote-contract";

export function FailureReviewPanel({ attemptId, target }: { attemptId: string; target: string }) {
  const [review, setReview] = useState<FailureReview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    void fetch(`/api/remote/v1/attempts/${encodeURIComponent(attemptId)}/review?target=${encodeURIComponent(target)}`, { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("No se pudo cargar la revisión del intento.");
        return parseFailureReview(await response.json() as unknown);
      })
      .then((result) => { if (active) setReview(result); })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "No se pudo cargar la revisión del intento.");
      });
    return () => { active = false; };
  }, [attemptId, target]);

  useEffect(() => {
    const target = `#attempt-${encodeURIComponent(attemptId)}`;
    if (window.location.hash === target) document.getElementById(target.slice(1))?.scrollIntoView({ block: "start" });
  }, [attemptId, review]);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!review) return <p className="empty">Cargando revisión del intento…</p>;
  return <section id={`attempt-${encodeURIComponent(review.attemptId)}`} className="failure-review" aria-label={`Revisión del intento ${review.attemptId}`}>
    <h4>Revisión del intento {review.attemptId}</h4>
    <section className="failure-section"><h5>Causa</h5><p>{review.cause}</p></section>
    <section className="failure-section"><h5>Verificación</h5>{review.verification.command && <p className="review-command">{review.verification.command}</p>}<pre className="review-scroll">{review.verification.output || "Sin salida de verificación."}</pre></section>
    <section className="failure-section"><h5>Diff stat</h5><p>{review.diff.stat ?? "Sin diff disponible."}</p>{review.diff.files.length > 0 && <ul>{review.diff.files.map((file, index) => <li key={`${file}-${index}`}>{file}</li>)}</ul>}</section>
    <section className="failure-section"><h5>Log del agente</h5><pre className="review-scroll">{review.logTail || "Sin log disponible."}</pre></section>
  </section>;
}
