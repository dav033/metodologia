import Link from "next/link";
import { reviewFixture } from "./review-fixture";
import { redactReviewText } from "./review-text.mjs";
import styles from "./review.module.css";

function ReviewSection({ title, children }: { title: string; children: string }) {
  return (
    <section className={styles.section} aria-label={title}>
      <h2>{title}</h2>
      <pre className={styles.output}>{redactReviewText(children)}</pre>
    </section>
  );
}

export default function ReviewPage() {
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
        <p className="eyebrow">DATOS DE MUESTRA · {redactReviewText(reviewFixture.run)} · {redactReviewText(reviewFixture.task)}</p>
        <h1 id="review-title">Intento fallido</h1>
        <p className={styles.attempt}>{redactReviewText(reviewFixture.attempt)}</p>
        <div className={styles.sections}>
          <ReviewSection title="Causa">{reviewFixture.cause}</ReviewSection>
          <ReviewSection title="Salida de verificación">{reviewFixture.verificationOutput}</ReviewSection>
          <ReviewSection title="Estadística del diff">{reviewFixture.diffStat}</ReviewSection>
          <ReviewSection title="Final del log">{reviewFixture.logTail}</ReviewSection>
        </div>
      </article>
      <footer className="footer"><span>FLOW REMOTE</span><span>REVISIÓN DE INTENTO</span></footer>
    </main>
  );
}
