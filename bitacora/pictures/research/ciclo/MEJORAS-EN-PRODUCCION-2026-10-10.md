# Mejoras visibles en producción — 2026-10-10 (main b3f66d39, VPS e7b7aeaa)

_Respuesta al dueño; verificada por workflow wf_35ff8442-93b (4 lectores + 4 escépticos)._

**Lo más grande:** hoy (10 oct, 11:56) por fin se actualizó el Python del VPS, que seguía con el código del 5 de octubre. Por eso los cambios mayores están en el asistente: cotizaciones y planes desde foto que antes fallaban. En producción solo abren /asistente y /3d. Las direcciones `/` y `/admin` te llevan a /asistente, así que lo del chat clásico se prueba en el chat del asistente.

**1. Lo que ves sin hacer nada**

*Asistente (/asistente)*
- «Cuánto cuesta» de una idea ya da el precio real. Antes fallaba siempre.
  Cómo verlo: responde evento, edad y temática, elige una idea, toca «Cuánto cuesta» y luego «Para uso personal». Debe salir «Materiales para tu decoración» con el «Total con IVA».
- Los planes hechos desde una foto vuelven a salir con precio. Lo que se ve en la foto (cantidad de globos por color, patrón y tamaños) llega al plan.
  Cómo verlo: toca «Tengo una foto de inspiración», sube una foto de columnas y confirma. En «Ajustes que hice» debe decir «… según proporción de la foto».
- La imagen de «Ver cómo quedaría» respeta la forma, el tamaño y los colores del plan. Las columnas orgánicas salen irregulares y la guirnalda ya no cruza toda la pared.
  Cómo verlo: pide «dos columnas orgánicas blanco y dorado y una guirnalda de 2,4 m» y toca «Ver cómo quedaría». No aplica si el plan lleva flores, si subiste una foto del espacio o si es un retoque de una imagen anterior.
- «Tu plan» dibuja semiarcos, arcos orgánicos, paredes, aros, techos y centros de mesa. Antes salía un ícono genérico.
  Cómo verlo: pide «un semiarco y una pared de globos». Luego toca «Ajustar mi plan», elige el semiarco y toca «Cambiar la forma (con el dibujo)».
- «Ajustar mi plan» ya guarda las medidas: «+ 10 %», «− 10 %», o escribir los metros y tocar «Aplicar». Recalcula globos y precio.
- Flores de globo como adorno de cualquier pieza: ponerlas, cambiarlas o quitarlas.
  Cómo verlo: escribe «agrega 3 flores doradas a la columna» y después «quítale las flores».
- El plan avisa cuando los colores no quedan como los pediste.
  Cómo verlo: pide «un arco clásico 70 % blanco, 20 % dorado y 10 % rosado» y mira «Ajustes que hice».
- La nota de «¿Qué tal quedó?» sigue marcada al recargar con F5. También pasa en /3d.

*Taller 3D (/3d)*
- La lista de compra trae helio y cinta (litros, tanques, metros) y el tiempo de bomba, que puedes calibrar. «Por pieza» junta las piezas iguales («Flor colgante × 3»).
  Cómo verlo: abre Plantillas → «Halloween: marco orgánico con mesas» → «Lista de compra». Busca «Helio y cinta» y «Bomba · …» (tócala y verás «Calibrar mi bomba»). Para que un globo vaya con helio: «Editar sola» → «Flota con helio».
- Regla con el alto y el ancho en metros de la pieza elegida. En pantallas de 1024 px o más, también puedes elegir la luz (incluida «UV (luz negra)») y el lente.
  Cómo verlo: toca una pieza y luego el ícono de regla arriba del visor. En el teléfono es un botón redondo junto a «Foto realista».
- Cada idea trae la tarjeta «Receta»: globos por color y tamaño, piezas, medidas y técnica.
  Cómo verlo: Añadir → Ideas → toca una idea → «Receta · N globos».
- La columna orgánica tiene perfiles de tamaño (Champaña, Botella, Lápiz…) y puedes guardar los tuyos.
  Cómo verlo: Añadir → Estructuras → «Columna · orgánica» → «Perfiles de tamaño».
- La IA del Taller cambia el color de los fondos fijos y arma los muebles que ve en una foto (mesa de postres, pedestales, silla…). Acepta grosores de 12 a 160 cm, y sus avisos empiezan con «No pude:» en lenguaje normal.
  Cómo verlo: escribe «pon un panel redondo» y luego «cambia el panel redondo a rosa». Para la foto, súbela con el clip «Adjuntar una foto de la decoración».
- Si fal tarda más de 100 s, la «Foto realista» ya no se pierde ni se paga dos veces. El texto ahora dice «hasta unos 5 min».

**2. Listo pero apagado**
- **Hoja de armado imprimible:** una página por estructura, con capas, helio y flores, y la lista de compra al final; sirve en Carta y A4. Para encenderla, ejecuta esto en Neon:
  `INSERT INTO ajustes_runtime (clave, valor, actualizado_por) VALUES ('taller_hoja_armado','activo','dueño') ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, actualizado_en = now();`
  Tarda hasta 30 s. Después ve a /3d → «Lista de compra» → «Hoja de armado» → «Imprimir». Para apagarla, cambia el valor a 'inactivo'.
- **Motor 3D de la guiada, solo para ti:**
  - **Qué trae:** con «Cambiar algo» encendido, puedes cambiar colores Sempertex, poner los globos de una pieza «Más chicos» o «Más grandes» y quitar piezas, también desde el chat. Entiende mejor los colores. Si la imagen tarda, se retoma sin pagar dos veces. El dorado cromado ya no sale plateado. La columna asimétrica sale con 42 globos y nada atraviesa el techo.
  - **Cómo encenderlo:** entra a /asistente y abre la consola (F12). Ejecuta primero `fetch('/api/feedback-ia/admin/sesion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({clave:'<ADMIN_PASSWORD>'})})`, luego `fetch('/api/guiada/motor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({motor:'3d'})})` y recarga.
  - **Cómo quitarlo:** repite la segunda orden con `motor:'defecto'`.
  - **No lo actives para los clientes:** hoy el 3D cotiza cerca de un 30 % más barato que el motor de siempre.
- **Freno de emergencia del 3D:** es la fila `guiada_motor_corte` = 'activo' en `ajustes_runtime`. Con él, los planes 3D abiertos piden «Recalcular mi plan». Hoy no hace falta.

**3. Cotización: puede cambiar respecto a la semana pasada (Python desplegado hoy)**
- «Cuánto cuesta» y los planes desde foto, que antes fallaban, ahora tienen precio.
- Cada color pedido lleva al menos un globo. Por ejemplo, un centro de mesa pequeño 75/20/5 ahora compra 1 rosado.
- Si un globo de 36″ no existe en esa talla, se compra en 24″ del mismo producto y se avisa. Antes quedaba «sin cobertura».
- Los orgánicos guardados con el editor de forma respetan el reparto de colores: un 70/20/10 ya no sale 47/28/25.
- Las flores suman los pétalos de 5″ y su centro. El «Racimo de pared» ahora se cotiza.
- El catálogo elige el globo liso pedido («Reflex Dorado») antes que los impresos «2 Caras». Burdeos y vinotinto se resuelven como Merlot o Vinotinto.
- En la cotización de negocio aparece la opción «Por paquete | Por unidad (a granel)».

**4. Aún no está en producción:** que la cotización sea la misma en todos lados (D-038), los últimos arreglos del lector de colores del 3D (P-052) y la parte visible del catálogo por repositorios (REQ-013, fase 4).
