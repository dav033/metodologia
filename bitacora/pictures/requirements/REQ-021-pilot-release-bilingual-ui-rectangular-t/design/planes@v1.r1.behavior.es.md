# Brief de interfaz — SP-14 · Sección de planes: los cuatro planes de acceso, pública e informativa

Fuente de comportamiento compartida para el Designer. Lo que no está aquí no es alcance de diseño.

## Resultado esperado

Cualquier persona, con sesión iniciada o no, abre la sección de planes desde la pantalla de inicio de sesión o el menú de cuenta y compara Entusiasta, Designer, Designer Plus y Master Designer con su precio mensual (COP en español, USD en inglés) y las herramientas incluidas, obtenidos del catálogo de planes, con las herramientas aún no desarrolladas marcadas como «aún no disponible»; nada en esta sección permite comprar, solicitar ni cambiar de plan.

## Requisitos que cubre

- R17: El sistema debe mantener los cuatro planes de acceso en un único catálogo de planes —nombre, precio mensual en COP y USD (Entusiasta gratis; Designer COP 20,000 / USD 7; Designer Plus COP 45,000 / USD 14; Master Designer COP 70,000 / USD 25), herramientas incluidas en orden acumulativo y disponibilidad de cada herramienta— y todas las pantallas y permisos que mencionen un plan deben leerlo de ese catálogo.
- R18: Cuando cualquier persona, con sesión iniciada o no, abre la sección de planes, el sistema debe mostrar los cuatro planes en orden con su nombre, precio mensual y herramientas incluidas, y marcar el chat extendido, la detección de estructuras y la detección avanzada de globos como «aún no disponible», sin permitir compras, solicitudes ni cambios de acceso.
- R19: La pantalla de inicio de sesión y el menú de cuenta deben incluir, cada uno, un enlace a la sección de planes.
- R20: Mientras la interfaz esté en español, la sección de planes debe mostrar los precios en COP; mientras esté en inglés, debe mostrarlos en USD.

## Criterios de producto

- La página /planes muestra Entusiasta, Designer, Designer Plus y Master Designer en ese orden, cada uno con su nombre, precio mensual y herramientas incluidas tomadas del catálogo de planes; cualquier valor modificado en el catálogo aparece en la página sin editarla.
- Con el idioma del navegador en español, la página muestra todos los precios en COP por mes; con el idioma en inglés, los muestra en USD por mes, nunca ambos. Entusiasta aparece como gratis en cada idioma y se llama Enthusiast en inglés.
- El chat extendido, la detección de estructuras y la detección avanzada de globos aparecen bajo Designer Plus y Master Designer con la marca «aún no disponible» en español y «not available yet» en inglés; el chat de Entusiasta dice «con límites» / «with limits» y el de Designer, «con límites más altos» / «with higher limits». La página no tiene controles para comprar, solicitar o registrarse, ni muestra valores de límites.
- La pantalla de inicio de sesión y el menú de cuenta muestran, cada uno, un enlace a la sección de planes que abre /planes: desde la pantalla de inicio de sesión sin sesión iniciada y desde el menú con sesión iniciada.

## Flujos de usuario

1. Visitante sin sesión compara los planes
   1. Abre la pantalla de inicio de sesión
   2. Sigue el enlace a los planes
   3. Lee los cuatro planes en orden con su nombre, precio mensual y herramientas incluidas
   4. Regresa a la pantalla de inicio de sesión
2. Persona con sesión iniciada consulta los planes
   1. Abre el menú de cuenta en cualquier página con sesión iniciada
   2. Sigue la opción de planes
   3. Lee los cuatro planes
   4. Regresa a la página desde la que llegó
3. Visitante en inglés
   1. Abre /planes con el navegador en inglés
   2. Ve los mismos cuatro planes y herramientas en inglés, con los precios en USD por mes

## Pantallas y estados

- /planes en español: Entusiasta, Designer, Designer Plus y Master Designer en ese orden, precios en COP por mes, Entusiasta gratis
- /planes en inglés: Enthusiast, Designer, Designer Plus y Master Designer con precios en USD por mes
- Planes acumulativos: cada plan incluye todo lo del plan anterior; el contrato define si un plan enumera todas sus herramientas o solo lo que agrega
- Líneas de chat sin números: Entusiasta «Chat con límites» / «Chat con límites»; Designer «Chat con límites más altos» / «Chat con límites más altos»
- Herramientas aún no desarrolladas (chat extendido, detección de estructuras, detección avanzada de globos) mostradas bajo Designer Plus y Master Designer como «aún no disponible» / «aún no disponible»
- Página con sesión cerrada (sin menú de cuenta) y página con sesión iniciada (con menú de cuenta)
- Teléfono de 390 px y escritorio de 1280 px sin desplazamiento horizontal; orden del foco del teclado
- Enlace a Planes en la pantalla de inicio de sesión y acceso a Planes en el menú de cuenta

## Superficie existente a modificar

El mockup es un CAMBIO sobre una superficie existente del producto, nunca una página nueva ni una landing: reproduce el shell, la navegación y la cabecera existentes y cambia solo lo que exigen los requisitos.

Superficie indicada por el Planner (léela en el repositorio, solo lectura, antes de diseñar):
- routes: `/login`, `/planes (new)`
- paths: `src/app/login/page.tsx`, `src/app/login/LoginForm.tsx`, `src/app/globals.css`, `src/app/layout.tsx`, `src/components/ui/shell/CabeceraApp.tsx`, `src/components/ui/shell/MenuApp.tsx`
- components: `LoginForm`, `CabeceraApp`, `MenuApp`, `MenuCuenta (planned by SP-2 T2.4, not on main yet)`
- repo t12: `/home/david/dev/pictures-wt/t12`
- repo pictures: `/home/david/dev/pictures-wt/asesor`
- Notas: SP-2 rediseña la pantalla de inicio de sesión y el menú de cuenta (cuentas-admin@v1, dirección elegida por el propietario «Parte de acceso»); planes@v1 solo agrega un enlace a planes en cada uno y sigue esa dirección y los tokens de src/app/globals.css. Los datos de la página provienen únicamente del catálogo de planes (src/lib/planes/catalogo.ts, SP-1 T1.2).

## No debe cambiar

- El diseño, el texto y el comportamiento de la pantalla de inicio de sesión y del menú de cuenta definidos por cuentas-admin@v1, excepto un enlace a planes en cada uno
- Ninguna acción de compra, suscripción, solicitud, contacto o registro en ninguna parte de la sección
- Ningún valor de límites, contador ni mensaje de límites
- Los roles personalizados, los roles del personal y las claves de permisos nunca se muestran en la sección

## Reglas de copy

- Los nombres de planes, precios y herramientas provienen únicamente del catálogo de planes; no se agregan afirmaciones de marketing, testimonios, descuentos ni beneficios inventados
- Nombres de planes: Entusiasta (en inglés: Enthusiast), Designer, Designer Plus, Master Designer
- El español muestra precios en COP por mes y el inglés en USD por mes; nunca ambas monedas
- Entusiasta es gratis («Gratis» / «Gratis»)
- Las herramientas aún no desarrolladas indican «aún no disponible» (español) y «aún no disponible» (inglés)
- Los límites del chat se nombran sin números: Entusiasta «con límites» / «con límites», Designer «con límites más altos» / «con límites más altos» (propietario, 2026-10-27)
- La línea Taller 3D de Master Designer representa todo el editor 3D de globos, incluido el explorador de decoraciones prediseñadas; no se agrega una línea separada para el explorador (confirmado por el propietario, 2026-10-27)
- Si la sección explica cómo se obtiene un plan, indica únicamente que un administrador lo asigna
- Sin nombres, fechas, eslóganes, titulares ni copy de marketing inventados: usa el copy de los requisitos o de la interfaz existente; los datos de ejemplo son neutrales, realistas, claramente de ejemplo y solo los que necesitan los flujos.

## Tareas de interfaz

- T14.1 — Copiar al repositorio el contrato planes@v1 aprobado por el propietario
  - Objetivo: El repositorio contiene el contrato visual exacto, aprobado por el propietario, de la sección de planes y sus dos puntos de entrada antes de que se construya cualquiera de ellos.
- T14.2 — Página pública de planes: los cuatro planes del catálogo, con precios según el idioma
  - Objetivo: Una página pública /planes muestra únicamente los cuatro planes de acceso del catálogo, en el idioma del visitante y con su moneda, sin acciones para comprar, solicitar ni cambiar de plan.
- T14.3 — Enlaces a Planes en la pantalla de inicio de sesión y en el menú de cuenta
  - Objetivo: La pantalla de inicio de sesión y el menú de cuenta conducen cada uno a la sección de planes sin cambiar nada más de lo que hacen las pantallas de cuentas-admin@v1.
- T14.5 — Revisión visual de SP-14 según el contrato planes@v1
  - Objetivo: Un revisor nuevo compara la sección de planes renderizada y sus dos puntos de entrada con el contrato aprobado en tres anchos y dos idiomas, y registra cada discrepancia junto con la tarea que debe rehacerse.

## Omitido a propósito

Campos del subplan que no se pasan al Designer: tareas fuera de la interfaz (ui:false, tareas que no son de diseño ni revisión), verificación, expected_paths, shared_resources, clasificación y estimaciones, digest, criterios de aceptación solo de ingeniería. Tareas omitidas: T14.4, T14.6.
