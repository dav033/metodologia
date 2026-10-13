# Ronda 2 (escena de la boda: 6 mesas redondas x 4 sillas, centro por mesa, marco organico, panel «Boda Real»)

Entrada: captura-3d-escena.jpg (vista oblicua con la pared izquierda). Instruccion: promptFotoDeLayout (prompt-ronda2.txt).
Gasto ronda 2: US$0,336 de 0,40 (gasto.json: ronda2Total). Total del experimento (ronda 1 + 2): US$0,597.

| Imagen | Fotorrealismo (1-5) | Cuentas (6 mesas / 4 sillas c.u. / 6 centros) | Rotulo «Boda Real» | Camara y encuadre |
|---|---|---|---|---|
| g-s11 FLUX.2 /edit (render_3d_base) | 4 | NO: 4 mesas visibles, 4 centros | si, bien escrito (plateado, no dorado) | NO: primer plano frontal, sala recortada |
| g-s22 FLUX.2 /edit | 4,5 | NO: 3 mesas, 3 centros (flor) | si, bien escrito | NO: vista frontal simetrica, otra distancia |
| k-s11 Kontext pro | 4 | si 6 mesas; sillas 4-5; centros = ramos de flores con platos | si, bien escrito | parcial: mas ancho y alto, pero el panel paso a la pared derecha y el marco es un arco |
| k-s22 Kontext pro | 4 | si 6 mesas, 6 centros (flores) | si, bien escrito | parcial: frontal alto; el marco paso a arco redondo |
| m-s11 Kontext max | 4,5 | si 6 mesas (3x2), 4 sillas, 6 centros de globos | casi: «Boda Real» con la «o» dudosa | si: misma vista oblicua, pared izquierda, marco rectangular y panel en su sitio |
| m-s22 Kontext max | 4,5 | si 6 mesas (3x2), 4 sillas, 6 centros de globos (solo rosados) | si, legible | si: igual que m-s11 |

Ronda 1 (referencia): a) FLUX.2 /edit texto antiguo: 4,5 / 6 mesas pero sillas y rotulo cambiados («Boda Kat») / camara frontal.
b) FLUX.2 texto nuevo: 4,5 / 6 mesas / sin rotulo / camara cambiada. c,e,f) FLUX.1 i2i: 2 (es el render) / todo se conserva. d) ControlNet: 1,5.

Ganador: FLUX.1 Kontext max (m). Unico que da foto real Y conserva camara, 6 mesas, sillas, centros, marco y panel.
No se probo la variante de tamano/proporcion (la camara ya se conserva): quedaban US$0,064, menos que una Kontext max (0,08).
