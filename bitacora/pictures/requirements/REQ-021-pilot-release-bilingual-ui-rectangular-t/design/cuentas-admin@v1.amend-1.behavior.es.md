# Brief de interfaz — SP-2 · Pantallas de inicio de sesión, invitación y administración

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Una persona inicia sesión con correo electrónico y contraseña, activa un enlace de invitación y acepta el aviso sobre el tratamiento de datos; un administrador invita a personas, les asigna uno de los cuatro planes de acceso u otro rol, crea roles seleccionando permisos y desactiva o elimina cuentas.

## Requisitos que cubre

- R1: Cuando un administrador invita una dirección de correo electrónico, el sistema debe permitir que esa persona cree una contraseña e inicie sesión; no debe haber registro abierto.
- R3: Cuando un administrador crea un rol, el sistema debe permitirle elegir sus permisos de una lista definida; deben existir los tres roles iniciales.
- R16: Cuando un administrador asigna uno de los cuatro planes de acceso a una cuenta de Usuario, el sistema debe otorgar en el servidor exactamente las herramientas de ese plan, de forma acumulativa: Entusiasta, el chat asistido y el contador de globos; Designer, las mismas herramientas (sus límites de chat superiores quedan pendientes hasta definir los valores de los límites); Designer Plus agrega la calculadora de costos; Master Designer agrega el Taller 3D; Empleado interno y Administrador deben contar con todas las herramientas de los planes (enmienda del 2026-10-27, ronda 10).
- R17: El sistema debe mantener los cuatro planes de acceso en un único catálogo de planes —nombre, precio mensual en COP y USD (Entusiasta gratis; Designer COP 20,000 / USD 7; Designer Plus COP 45,000 / USD 14; Master Designer COP 70,000 / USD 25), herramientas incluidas en orden acumulativo e indicación de si cada herramienta ya está disponible— y todas las pantallas y permisos que mencionen un plan deben leerlo de ese catálogo.

Secciones de SPEC.md que nombran este subplan (léelas): «Aviso sobre el tratamiento de datos (v1, SP-2)»

## Criterios de producto

- En /login, una persona inicia sesión con correo electrónico y contraseña; una contraseña incorrecta, un correo desconocido, una cuenta desactivada y un correo bloqueado muestran el mismo mensaje, que siempre indica que después de varios intentos fallidos se debe esperar quince minutos; si el inicio de sesión es correcto, la persona vuelve a la página solicitada o a la primera sección permitida por su rol, o a Mi cuenta si no tiene acceso a ninguna.
- Al abrir un enlace de invitación, se muestra el nombre y el correo electrónico de la persona invitada, se solicita dos veces una contraseña de al menos ocho caracteres y se muestra el aviso sobre el tratamiento de datos en el idioma del navegador con una casilla de aceptación; no se puede activar la cuenta sin aceptar el aviso y, tras activarla, la persona inicia sesión y llega a la primera herramienta permitida por su rol; un enlace usado o vencido muestra un mensaje que solicita pedir un enlace nuevo al administrador.
- Cuando cambia la versión del aviso, la persona con sesión debe aceptar la nueva versión antes de que se abra cualquier otra página.
- Cada página con sesión muestra un menú de cuenta con el nombre y el rol de la persona, Mi cuenta y cerrar sesión; Mi cuenta permite cambiar la contraseña solicitando la actual.
- Un administrador invita a una persona con su nombre, correo electrónico, empresa opcional y rol, y obtiene una sola vez el enlace de un solo uso con un botón para copiarlo; se rechaza un correo electrónico ya registrado con un mensaje claro.
- Un administrador cambia el rol de una cuenta, la desactiva y la reactiva, genera un enlace para restablecer la contraseña y elimina una cuenta sin trabajo guardado después de escribir su correo electrónico; la pantalla explica por qué no se puede eliminar al último administrador ni una cuenta con trabajo guardado.
- Un administrador crea y edita un rol personalizado por nombre y casillas de permisos agrupadas por herramienta, ve los seis roles del sistema (Usuario · Entusiasta, Usuario · Designer, Usuario · Designer Plus, Usuario · Master Designer, Empleado interno y Administrador) en modo de solo lectura con sus permisos, y no puede eliminar un rol que todavía tenga cuentas asignadas.
- Las pantallas renderizadas de inicio de sesión, activación, cuenta y administración coinciden con el contrato aprobado cuentas-admin@v1 en anchos de teléfono, tableta y escritorio; cada hallazgo queda registrado con la tarea que debe rehacerlo en el registro visual de SP-2.
- El selector de roles de las pantallas de invitación y cuenta ofrece los cuatro planes de acceso con los nombres del catálogo de planes en el orden de los planes, seguidos de Empleado interno, Administrador y los roles personalizados.

## Flujos de usuario

- El Planner no los escribió: derívalos de los requisitos y de la superficie existente, sin inventar flujos.

## Pantallas y estados

- El Planner no los escribió: lista en el contrato las pantallas y estados que exigen los requisitos.

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

El Planner no nombró las pantallas actuales. No las adivines: localízalas en solo lectura en estos repositorios y basa el mockup en ellas; si no las encuentras, dilo en CONCERNS.
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`

## No debe cambiar

- El resto de la superficie existente: shell, navegación, cabecera, tokens, fuentes y componentes.

## Reglas de copy

- No inventes nombres, fechas, eslóganes, titulares ni textos de marketing: usa los textos de los requisitos o de la interfaz existente; los datos de ejemplo deben ser neutrales, realistas, claramente identificados como ejemplos y limitarse a los necesarios para los flujos.

## Tareas de interfaz

- T2.1 — Copiar el contrato cuentas-admin@v1 aprobado por el propietario al repositorio
  - Objetivo: El repositorio contiene el contrato visual exacto aprobado por el propietario para las pantallas de inicio de sesión, activación, cuenta y administración antes de construir cualquiera de ellas.
- T2.3 — Pantallas de inicio de sesión, activación de invitaciones, restablecimiento de contraseña y nueva aceptación del aviso
  - Objetivo: Una persona inicia sesión, activa una invitación aceptando el aviso de tratamiento de datos, restablece una contraseña desde un enlace del administrador y vuelve a aceptar una nueva versión del aviso, con los estados definidos en el contrato.
- T2.4 — Menú de cuenta en cada página con sesión iniciada y página Mi cuenta
  - Objetivo: Cada persona con sesión iniciada ve quién es y cuál es su rol, cierra sesión y cambia su propia contraseña desde Mi cuenta.
- T2.5 — Pantallas de administración: lista de cuentas, invitaciones, acciones de cuenta y editor de roles
  - Objetivo: Un administrador gestiona todas las cuentas y los roles personalizados desde dos pantallas que muestran exactamente qué hará cada acción y por qué se rechaza alguna.
- T2.7 — Revisión visual de SP-2 según el contrato cuentas-admin@v1
  - Objetivo: Un revisor nuevo compara las pantallas renderizadas con el contrato aprobado en tres anchos y registra cada discrepancia junto con la tarea que se debe rehacer.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, no relacionadas con diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest y criterios de aceptación solo de ingeniería. Tareas omitidas: T2.2, T2.6, T2.8.
