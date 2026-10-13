---
id: REQ-005
status: approved
created: 2026-10-11
track: standard
---
# REQ-005 — Alcance sencillo de Proposal Studio

## Objetivo
Mantener una herramienta pequeña para preparar propuestas visuales de desarrollo: comparar el sitio actual con el prototipo, guardar capturas del sitio, importar el prototipo ya construido desde GitHub, compartir temporalmente por URL y administrar el espacio con Google OAuth.

## Incluye
- Comparación interactiva y navegable entre captura original y prototipo.
- Captura del sitio público para usar como estado original, con opción de cargar una captura manual.
- Importación de un prototipo estático ya construido desde un repositorio GitHub autorizado.
- Enlaces públicos temporales, revocables y con caducidad.
- Inicio/cierre de sesión con Google para el administrador allowlisted.
- Panel privado breve para propuestas y conexión GitHub.
- Interfaz en español con patrones Material, animaciones sutiles y respeto por `prefers-reduced-motion`.

## Aclaración de alcance: editor mínimo
El formulario de alta y edición solo exige tres datos: nombre del negocio, URL actual y captura PNG. La URL del prototipo es opcional cuando se importará desde GitHub; el slug se genera automáticamente a partir del nombre. Los textos de venta, entregables, precio, video y contacto dejan de ser obligatorios y no aparecen en propuestas nuevas; los valores opcionales de propuestas existentes se conservan y solo se muestran cuando ya están cargados. No se puede publicar sin captura y prototipo.

## Fuera del alcance actual
Notificaciones de correo, panel de ajustes de correo, historial/reintentos de correo y funcionalidades administrativas que no sean necesarias para preparar o compartir la propuesta. La infraestructura y datos existentes se conservan en esta reducción; no se realizan borrados ni migraciones destructivas.

## Criterios de aceptación
1. El panel permite abrir/crear propuestas y acceder a GitHub sin navegación de correo/configuración.
2. El editor centra el flujo en captura original, prototipo, comparación y enlace temporal.
3. Publicación informa su resultado sin exponer estados de correo.
4. El prospecto puede mover la división y navegar ambos sitios en una URL temporal.
5. Login Google, restricciones del prototipo aislado, expiración y revocación conservan su comportamiento.
6. Componentes Material y animaciones existentes se mantienen accesibles.
