---
req: REQ-031
status: draft
created: 2026-11-12
---
# Plan — Tablas de distribuidores y MBP, carrito desde un boceto, pedidos pendientes y correo electrónico de pedidos a distribuidores

Esqueleto (planificación colaborativa, fase Esqueleto). Solo hitos y subplanes; las tareas se definen subplan por subplan.

## Enfoque
Una carpeta de funcionalidad nueva por responsabilidad (`src/features/directory`, `src/features/cart-orders`), tablas de Postgres compartidas por la aplicación de Vercel y el asistente del VPS, y tres puertos para poder cambiar las fuentes más adelante: catálogo de productos (crosswalk ahora, Shopify después), geocodificador (Nominatim ahora) y mensaje saliente (WhatsApp o correo electrónico). El asistente de WhatsApp (`services/telegram-globos`) reutiliza los mismos casos de uso de la aplicación a través de la base de datos; nunca duplica reglas.
Cada subplan se incorpora detrás de su propia bandera, desactivada en producción hasta que el propietario lo apruebe.

## Restricciones globales
AGENTS.md de `pictures`; migraciones aditivas desde 066 con reversión; cada ruta en `MAPA_PERMISOS_RUTAS`; ningún teléfono ni correo electrónico en los registros; datos personales de MBP solo con el permiso del directorio; copia de seguridad de la base de datos de producción antes de migrar; nada llega a `main` antes de que se apruebe su subplan.

## Tareas

### M1 — Directorio: distribuidores y MBP como datos editables
Las dos hojas de cálculo recibidas se almacenan como filas en Postgres y un administrador puede listarlas, buscarlas, crearlas, editarlas y desactivarlas.

- **SP-1 — Tablas e importación de distribuidores y MBP**: Postgres almacena los 670 puntos de venta con coordenadas y los 472 MBP; un comando de importación repetible informa las filas agregadas, actualizadas, omitidas y rechazadas, y nunca sobrescribe una fila editada manualmente.
- **SP-2 — Pantallas de administración del directorio**: un administrador con el permiso del directorio lista, busca, filtra, crea, edita y desactiva distribuidores y MBP desde Administración.

### M2 — Carrito desde un boceto
Un boceto terminado se convierte en un carrito de productos B2B reales con paquetes y precios de referencia, en la web y en WhatsApp; al seleccionar «comprar» se genera un pedido pendiente.

- **SP-3 — Puerto del catálogo, carrito y núcleo de pedidos**: un único puerto del catálogo (adaptador crosswalk, SKU desde `catalog_variants`) convierte las líneas del boceto en líneas de productos; los carritos y pedidos persisten en Postgres con una instantánea inmutable del pedido; comprar es idempotente.
- **SP-4 — Carrito en el boceto web**: en `/boceto`, una persona agrega el boceto al carrito, cambia los paquetes, quita líneas, ve los precios y el total, y compra.
- **SP-5 — Carrito en el asistente de WhatsApp**: después de mostrar el resultado de un boceto, el asistente ofrece el carrito; la persona lo consulta, lo modifica y compra sin salir del chat.

### M3 — Respuesta con un enlace a los pedidos pendientes
Un administrador gestiona los pedidos pendientes y la persona recibe el enlace de Shopify.

- **SP-6 — Panel de pedidos y respuesta con enlace**: un administrador con el permiso de pedidos lista los pedidos, copia los SKU, pega el enlace de Shopify y lo envía (por WhatsApp dentro de las 24 h; de lo contrario, por correo electrónico), y marca los pedidos como pagados o cancelados.

### M4 — Pedido a un distribuidor cercano
Una persona escribe una dirección, elige uno de los distribuidores más cercanos y ese distribuidor (o el buzón fijo) recibe el pedido en PDF.

- **SP-7 — Distribuidores cercanos, PDF del pedido y correo electrónico**: dirección escrita → hasta cinco distribuidores colombianos activos más cercanos; un pedido a un distribuidor genera el PDF diseñado y un correo electrónico con el archivo adjunto, dirigido según la regla del destinatario, y muestra el estado «sin destinatario» cuando no hay nada configurado.
- **SP-8 — Flujo para distribuidores en la web y en WhatsApp**: desde el carrito y en ambas interfaces, la persona escribe la dirección, elige un distribuidor, confirma el aviso sobre el uso compartido de datos y recibe el nombre y la dirección del distribuidor, además de un enlace al mapa.

## Verificación
Por subplan, en SPEC `## Pruebas` (se redacta cuando cada subplan pasa a estar en primer plano).

## Decisiones

## Registro de progreso
