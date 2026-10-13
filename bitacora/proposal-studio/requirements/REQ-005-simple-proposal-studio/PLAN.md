---
id: REQ-005
status: done
---
# Plan — REQ-005

1. Simplificar navegación administrativa y retirar correo del flujo visible de GitHub.
2. Quitar campos/estados de notificación del editor y la publicación; conservar captura, importación, comparación y compartir.
3. Revisar el diff y ejecutar typecheck, lint, formato, suites y build.
4. Registrar resultados, límites y pendientes en bitácora y memoria del proyecto.

## Resultado
- Eliminados los campos, pantallas y disparadores de correo; rutas heredadas responden 410 o redirigen al panel.
- Los datos/tablas anteriores se conservan. Se desplegó a producción sin hacer push.
- `npm run check`, `npm run lint`, `npm run format:check`, `npm test` (81), `npm run test:e2e` (11) y `npm run build`: pasan.
- Vercel deployment `dpl_ApXLJr8rTbCW1RNjiFahjNCfwr6R` quedó READY y mantiene el alias `https://proposal-studio-orpin.vercel.app`.
- Smoke HTTP: `/` 200, `/login` 200, `/admin` anónimo 302 y API de correo desactivada 401 anónimo por protección de admin.

No borrar datos ni retirar tablas/servicios existentes en esta reducción.


## Ajuste posterior: editor mínimo
- El formulario de alta/edición exige nombre, URL actual y captura PNG; la URL del prototipo es opcional si se importará desde GitHub. El slug se genera en el cliente.
- Los campos editoriales opcionales dejaron de bloquear el guardado. Propuestas existentes conservan esos datos y su página solo muestra secciones que tengan contenido. La publicación valida que existan captura y prototipo (URL o importación GitHub).
- `npm run check`, `npm run lint`, Prettier y `git diff --check` pasaron. La suite de pruebas no se ejecutó en esta sesión.
