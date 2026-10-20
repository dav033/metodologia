import Link from "next/link";

export default function HomePage() {
  return (
    <main className="shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Flow Remote, inicio">
          <span className="brand-mark" aria-hidden="true">F</span>
          <span>flow<span className="brand-muted">/remote</span></span>
        </Link>
        <span className="environment">PANEL REMOTO</span>
      </header>
      <section className="intro" aria-labelledby="welcome-title">
        <p className="eyebrow">OPERACIONES · EN VIVO</p>
        <h1 id="welcome-title">Tus ejecuciones,<br /><span>siempre a mano.</span></h1>
        <p className="lede">El panel remoto está listo. Inicia sesión para ver el estado de tus ejecuciones.</p>
        <a className="sign-in" href="/api/auth/github">
          <svg aria-hidden="true" viewBox="0 0 24 24" width="19" height="19" fill="currentColor">
            <path d="M12 .9a11.1 11.1 0 0 0-3.51 21.63c.56.1.76-.24.76-.54v-2.08c-3.1.68-3.76-1.32-3.76-1.32-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 .1.85 2.06 3.42 1.45.1-.72.4-1.2.71-1.48-2.47-.28-5.07-1.24-5.07-5.51 0-1.22.44-2.21 1.16-2.99-.12-.28-.5-1.42.11-2.95 0 0 .95-.3 3.06 1.14a10.66 10.66 0 0 1 5.57 0c2.12-1.44 3.06-1.14 3.06-1.14.61 1.53.23 2.67.11 2.95.72.78 1.16 1.77 1.16 2.99 0 4.28-2.6 5.23-5.08 5.5.4.35.76 1.02.76 2.07v3.06c0 .3.2.65.77.54A11.1 11.1 0 0 0 12 .9Z" />
          </svg>
          Continuar con GitHub
        </a>
        <p className="security-note"><span aria-hidden="true">●</span> Acceso privado para el propietario</p>
      </section>
      <footer className="footer"><span>FLOW REMOTE</span><span>CONTROL PLANE · V1</span></footer>
    </main>
  );
}
