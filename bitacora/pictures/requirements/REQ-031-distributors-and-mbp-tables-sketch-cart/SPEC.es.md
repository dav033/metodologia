---
id: REQ-031
status: clarifying
created: 2026-11-12
track: deep
---
# REQ-031 — Tablas de distribuidores y MBP, carrito de boceto con Shopify simulado, pedidos pendientes respondidos por WhatsApp, correo electrónico de pedido al distribuidor más cercano con PDF

## Problema y objetivo
Una persona que recibe un boceto de globos (web `/boceto` o asistente de WhatsApp) recibe una lista de globos y nada
más: no hay forma de comprarlos. Sempertex no tiene conexión con Shopify para este canal y no la tendrá pronto.
Los directorios de distribuidores y MBP solo existen como hojas de cálculo; la aplicación contiene 69 registros de ejemplo.

Objetivo: el boceto termina en un carrito. La persona compra (el pedido queda registrado en una tabla; un administrador crea manualmente el
carrito real de Shopify y envía su enlace por WhatsApp) o envía el pedido a un distribuidor cercano (quien lo recibe
por correo electrónico como PDF diseñado). Actualmente, la fuente de productos es el JSON de equivalencias B2B y debe poder reemplazarse por una
conexión real con Shopify sin modificar el carrito.

**El resultado esperado es:** a partir de un boceto terminado, en la web y en WhatsApp, una persona llega a «pedido recibido» en
menos de un minuto; todos los pedidos son visibles para un administrador, con sus SKU; el enlace del administrador llega a la
persona; un pedido a un distribuidor genera un correo electrónico con PDF; los distribuidores y MBP son filas que un administrador puede editar.

## Usuarios / actores / partes interesadas
- **Persona con un boceto** — cuenta web (permiso `taller_3d` en `/boceto`) o contacto registrado de WhatsApp
  (`whatsapp_contactos`: nombre, correo electrónico, número).
- **Administrador de pedidos** — personal de Sempertex con el nuevo permiso de pedidos: consulta los pedidos pendientes, crea el carrito de Shopify
  fuera de este sistema, pega el enlace y cierra el pedido.
- **Administrador del directorio** — edita distribuidores y MBP.
- **Distribuidor** — recibe un correo electrónico con el pedido como PDF. No tiene cuenta.
- **Propietario** — David; aprueba cada subplan.

## Alcance (incluido)
### US-1 (P1, Obligatorio) — Distribuidores y MBP en la base de datos
Como administrador del directorio, quiero que las dos hojas de cálculo recibidas estén disponibles como tablas que pueda listar, buscar, crear, editar y
desactivar, para que el directorio contenga datos reales y los contactos puedan completarse con el tiempo.

### US-2 (P1, Obligatorio) — Carrito a partir de un boceto
Como persona con un boceto, quiero que su lista de globos aparezca como un carrito de productos reales, con cantidades de paquetes y precios que pueda
cambiar, para poder pedir lo que necesita el boceto.

### US-3 (P1, Obligatorio) — Comprar: responder al pedido pendiente con un enlace de Shopify
Como persona, quiero presionar «comprar» y recibir luego un enlace de pago por WhatsApp; como administrador de pedidos, quiero
ver los pedidos pendientes con sus SKU y un campo para pegar el enlace que se enviará.

### US-4 (P1, Obligatorio) — Enviar el pedido a un distribuidor cercano
Como persona, quiero escribir mi dirección, ver los distribuidores más cercanos y elegir uno, para que el distribuidor
reciba mi pedido por correo electrónico como PDF.

## Fuera de alcance
- Una conexión real con Shopify (catálogo, carrito, finalización de compra, webhooks de pago). Solo se implementa el punto de integración.
- Pagos, inventario, costo de envío, impuestos, facturas.
- Mensajes de plantilla de Meta (necesarios para escribir después de la ventana de 24 h de WhatsApp): propuesta, no se implementa.
- Enviar contenido a un distribuidor por WhatsApp; cuentas de distribuidor o un portal para distribuidores.
- Incluir MBP en la búsqueda de cercanía o en el flujo de pedidos; solo se listan y editan los registros de MBP.
- Obtener los correos electrónicos y teléfonos de los distribuidores colombianos (el propietario los proporcionará más adelante).
- El bot de Telegram, la ruta del webhook de WhatsApp en Vercel y la carpeta sin seguimiento `services/whatsapp-globos`.
- Reemplazar el directorio de ejemplo `proveedores.json` que usa el chat guiado.

## Requisitos
- R1. El sistema almacenará los distribuidores en una tabla de Postgres con name, status, country, region, city, address,
  postcode, latitude, longitude, phone, e-mail, WhatsApp number, website, social links, map groups, tags, source y
  timestamps, e importará las 670 filas de la exportación de ubicaciones recibida, conservando todos los países y las coordenadas.
- R2. El sistema almacenará MBP en una tabla separada de Postgres con name, distributor name, optional link to a
  distributor row, continent, country, city, social links, e-mail, address, phone, event city, event date, year,
  juror, shirt size, birthday, identification number, publication note y timestamps, e importará las 472 filas
  del archivo de MBP recibido (Latin-1, separado por `;`, con celdas multilínea).
- R3. Cuando se vuelva a ejecutar una importación, el sistema agregará filas nuevas y actualizará las que no hayan cambiado sin sobrescribir una fila
  que un administrador haya editado manualmente, e informará las filas agregadas, actualizadas, omitidas y rechazadas con el motivo.
- R4. Al iniciar sesión con el permiso de directorio, un administrador podrá listar con paginación, buscar por
  texto, filtrar (por país, ciudad, estado, si tiene correo electrónico; para MBP también por distribuidor y año), crear, editar y desactivar
  distribuidores y registros de MBP; sin ese permiso, las páginas y API denegarán el acceso.
- R5. El sistema leerá los productos únicamente a través de un puerto de catálogo; el primer adaptador resolverá una línea del boceto
  (formato, código de color Sempertex, cantidad de globos) a una variante de producto B2B del archivo de equivalencias, con su título, tamaño del paquete, paquetes necesarios, precio unitario en COP y, cuando `catalog_variants` lo tenga, su SKU. Una línea sin producto se devolverá como no disponible, con el motivo; nunca se omitirá silenciosamente.
- R6. Cuando una persona agregue un boceto al carrito, el sistema creará o ampliará el carrito de esa persona con una línea
  por cada variante resuelta; la persona podrá cambiar las cantidades de paquetes, quitar líneas, vaciar el carrito y ver
  el precio de cada línea y el total, etiquetados como precios de referencia. El carrito persistirá en el servidor y estará asociado a la cuenta web o al contacto de WhatsApp.
- R7. Después de mostrar el resultado de un boceto en WhatsApp, el asistente ofrecerá agregarlo al carrito y permitirá que la persona vea
  el carrito, cambie una cantidad, quite una línea, lo vacíe, compre o lo envíe a un distribuidor, dentro de los límites de WhatsApp
  (3 botones, 10 filas en la lista).
- R8. Cuando una persona compre, el sistema creará un pedido en estado `pending` con una instantánea inmutable de las líneas (id de variante, SKU, título, paquetes, unidades, precio unitario, total), el canal, la referencia al boceto y el contacto (nombre, correo electrónico, número de WhatsApp cuando se conozca), vaciará el carrito e informará a la persona que un asesor le enviará el enlace.
- R9. Al iniciar sesión con el permiso de pedidos, un administrador podrá listar pedidos por estado, abrir uno,
  copiar sus SKU y cantidades, pegar un enlace de Shopify y enviarlo. Si el último mensaje de WhatsApp de la persona al
  asistente tiene menos de 24 h, el enlace se enviará por WhatsApp desde el número del asistente; en caso contrario, se enviará al
  correo electrónico de la persona. El panel mostrará qué canal se usó y cualquier fallo de entrega.
- R10. El administrador podrá marcar un pedido como pagado o cancelado; un pedido pagado o cancelado queda cerrado
  y no admite más envíos. Cada cambio de estado registrará quién lo hizo y cuándo.
- R11. Cuando una persona elija enviar el carrito a un distribuidor y escriba una dirección, el sistema geocodificará la dirección
  mediante un puerto de geocodificación (primer adaptador: OpenStreetMap Nominatim) y devolverá hasta cinco distribuidores colombianos activos,
  ordenados por distancia en línea recta, con nombre, dirección, ciudad y distancia. Si no se encuentra la dirección, el sistema preguntará por la ciudad y mostrará los distribuidores de esa ciudad.
- R12. Cuando la persona elija un distribuidor, el sistema creará un pedido de tipo `distributor`, generará un
  PDF y lo enviará por correo electrónico: al correo del distribuidor si la fila tiene uno, con el buzón fijo configurado en copia;
  solo al buzón fijo si no tiene correo. Si no hay un buzón fijo configurado y el distribuidor tampoco tiene correo,
  el pedido se registrará como `not sent: no recipient`, se mostrará así a los administradores y se podrá reenviar.
- R13. El PDF incluirá la marca Sempertex, el número y la fecha del pedido, el nombre y los datos de contacto de la persona,
  el nombre y la dirección del distribuidor, una tabla de productos (muestra de color y nombre, formato, SKU, paquetes, unidades, precio de referencia) con el total y la imagen del boceto, si existe.
- R14. El adaptador de correo electrónico aceptará archivos adjuntos.
- R15. Después de un pedido a un distribuidor, la persona recibirá el nombre y la dirección del distribuidor, además de un enlace al mapa, y se le
  informará que su nombre y datos de contacto se compartieron con ese distribuidor; antes del envío, verá ese aviso y deberá confirmarlo.
- R16. Los números de teléfono y las direcciones de correo electrónico no se escribirán en los registros; cada llamada externa (geocodificador, correo electrónico, WhatsApp)
  tendrá un plazo límite y un estado de fallo registrado; cada parte estará detrás de una bandera que, en producción, estará desactivada de forma predeterminada.

## Contrato de interfaz / diseño
- Alcance de la interfaz / usuarios: (a) administración de distribuidores y MBP; (b) carrito en `/boceto`; (c) panel de pedidos;
  (d) dirección, selección de distribuidor y confirmación en la web; (e) PDF del pedido. En WhatsApp solo se define el texto.
- Dirección visual / sistema existente: estructura de la aplicación y `@bitacora/ui` (el proyecto está habilitado); las páginas de administración
  siguen el patrón de `/admin/roles` y `/admin/subidas`. Español e inglés, como en el resto del piloto.
- Requisitos de accesibilidad e interacción: diseño para móviles en el carrito y el flujo con distribuidores; etiquetas para teclado y lectores de pantalla en tablas y diálogos.

## Casos límite y errores
- Línea del boceto sin producto (39 casos conocidos) → se muestra como no disponible en el carrito; se permite comprar el resto.
- Carrito vacío → se desactivan las opciones de comprar y enviar. Dos bocetos en un carrito → se suman las líneas de la misma variante.
- Cambio del precio o producto en el archivo de equivalencias después del pedido → el pedido conserva su instantánea.
- Persona en la web sin número de WhatsApp → se le solicita al comprar; el enlace se envía por correo electrónico, salvo que ese número haya escrito al
  asistente en las últimas 24 h.
- Meta rechaza el envío por WhatsApp (la ventana se cierra entre la comprobación y el envío) → se recurre al correo electrónico y se registra el resultado.
- Geocodificador caído, lento o con resultados ambiguos → se pregunta la ciudad; si se desconoce, se buscan los distribuidores más cercanos usando las propias coordenadas de la ciudad cuando el directorio las tenga; en caso contrario, se muestra «no encontramos puntos cerca» con la opción de comprar.
- Fila de distribuidor sin coordenadas (1 de 670) o inactiva → nunca se ofrece.
- Doble toque en comprar/enviar → un solo pedido (clave de idempotencia).
- Importación: filas duplicadas, filas sin nombre o codificación dañada → se rechazan y se informa; la importación continúa.

## Restricciones
- Repositorio `pictures` (Next 16 en Vercel, Postgres mediante `pg`, SQL directo, migraciones `scripts/migrations/NNN_*.sql`,
  siguiente número libre 066); el asistente de WhatsApp activo es `services/telegram-globos` en el VPS `advin`, con su propio rol `whatsapp_bot`.
- AGENTS.md: las funcionalidades van en `src/features/<name>/{domain,application,infrastructure,presentation}`; los controladores solo autentican, autorizan, validan y llaman a un caso de uso; zod en los límites; los datos del catálogo son la fuente de verdad para los precios; migraciones aditivas con reversión; interfaz de `@bitacora/ui`; todas las rutas en `MAPA_PERMISOS_RUTAS`.
- Las filas de MBP contienen datos personales (fecha de nacimiento, número de identificación, dirección): solo permiso de directorio, nunca se envían a un modelo ni se registran.
- Política de uso de Nominatim: una solicitud por segundo, cliente identificado, resultados en caché.
- Los cambios en producción requieren primero una copia de seguridad de la base de datos; nada llega a `main` antes de que se apruebe su subplan.

## Prioridades y fases
Obligatorio: US-1 a US-4. Orden del MVP: directorio (M1) → carrito y compra (M2, M3) → distribuidores (M4). Más adelante (propuestas): plantillas de Meta,
adaptador real de Shopify, WhatsApp para distribuidores, inclusión de MBP en el flujo.

## Cronograma y dependencias
- No se indicó una fecha. Depende del propietario para: la dirección del buzón fijo (R12), los datos de contacto de los distribuidores colombianos,
el dominio de remitente de Resend ya verificado.

## Supuestos
- A1. «JSON BTB» es `src/lib/globos3d/motor/datos/crosswalk-vigente.json` (propietario, ronda 1).
- A2. Los precios mostrados son los precios B2B del archivo de equivalencias en COP, etiquetados como «precio de referencia» (el propietario eligió los precios; la etiqueta es mía: el carrito real se crea manualmente y puede variar).
- A3. El buzón fijo es un valor de entorno que se dejará vacío hasta que lo proporcione el propietario (propietario: «haz la
  configuración, luego conseguimos los correos»); R12 cubre el caso vacío.
- A4. La dirección se escribe manualmente (propietario, ronda 1); no se implementan el pin de ubicación de WhatsApp ni la geolocalización del navegador.
- A5. La búsqueda de cercanía abarca solo Colombia: las 596 filas colombianas; las filas internacionales se almacenan y se pueden editar.
- A6. El carrito web requiere una cuenta con sesión iniciada (la página ya lo requiere); no hay carrito anónimo.
- A7. «Cuando se haga efectiva la compra, muere» = el administrador marca el pedido como pagado y este se cierra; nada detecta automáticamente el pago.
- A8. Los pedidos y carritos se almacenan en Postgres para que el panel de Vercel y el asistente en el VPS los compartan; `whatsapp_bot` recibe permisos solo en las tablas de carritos y pedidos que necesita.

## Datos de entrada
Solo ubicaciones, nunca valores. Subplan vacío = todo el plan.

| Elemento | Subplan | Ubicación | Proveedor | Estado |
|---|---|---|---|---|
| Archivo CSV de ubicaciones | SP-1 | `~/recibidos/distribuidores/locations-export-1793894386941.csv` | Propietario | disponible |
| Archivo CSV de MBP | SP-1 | `~/recibidos/distribuidores/MBP BASE DE DATOS -educacion(OK).csv` | Propietario | disponible |
| Buzón fijo para pedidos a distribuidores (puede quedar vacío: R12 lo contempla) | SP-7 | env `PEDIDOS_DISTRIBUIDOR_CORREO` (Vercel y `/etc/pictures-whatsapp/whatsapp.env`) | Propietario | disponible |
| Clave y remitente de Resend | SP-6, SP-7 | env `RESEND_API_KEY`, `CORREO_REMITENTE` (ya están en Vercel) | Operador | disponible |
| Token de Meta para envíos desde el panel | SP-6 | env del asistente en el VPS; el panel llama al asistente mediante `BOT_SERVICE_SECRET` | Operador | disponible |

## Cobertura
| Tema | Estado |
|---|---|
| Objetivo y problema | Claro |
| Usuarios / actores | Claro |
| Alcance | Claro |
| Fuera de alcance | Claro |
| Flujos y comportamiento | Parcial (por subplan) |
| Casos límite | Parcial (por subplan) |
| Criterios de aceptación | Parcial (por subplan) |
| Restricciones | Claro |
| Interfaz / dirección de diseño | Parcial (por subplan) |
| Prioridades y fases | Claro |
| Cronograma | Pospuesto (sin fecha) |

## Aclaraciones
### Ronda 1 — 2026-11-12
- P: ¿Qué JSON es «BTB»? → R: el crosswalk.
- P: ¿El carrito muestra precios? → R: sí.
- P: ¿Adónde se envía un pedido a un distribuidor, dado que los distribuidores colombianos no tienen correo electrónico ni teléfono? → R: crear la configuración ahora; los correos electrónicos llegan después.
- P: ¿Cómo se convierten las direcciones en coordenadas? → R: la persona escribe la dirección (geocodificación de OpenStreetMap).
- P: ¿Cómo responde el administrador con el enlace? → R: desde el panel, mediante el número del asistente, dentro de las 24 h; de lo contrario, por correo electrónico.
