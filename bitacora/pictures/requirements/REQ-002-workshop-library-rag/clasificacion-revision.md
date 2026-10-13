# REQ-002 — Classification review sheet (rules vs Sonnet 5.5)

131 factory items where the subagents rejected at least one rule tag. Final tags = the model's (in the repo JSON).
Owner: skim and flag anything wrong; corrections go into src/lib/taller/datos/clasificacion-biblioteca.json.

## Most rejected rule tags

- Cumpleaños (`cumpleanos`): 37
- Fiesta infantil (`fiesta-infantil`): 30
- Flores / jardín (`flores-jardin`): 18
- Boda (`boda`): 11
- Aniversario de pareja (`aniversario`): 9
- Graduación (`graduacion`): 9
- Baby shower (`baby-shower`): 6
- Bautizo (`bautizo`): 5
- Año nuevo (`ano-nuevo`): 5
- Princesas (`princesas`): 4
- Primera comunión (`primera-comunion`): 4
- fiesta-infantil:0.6 (`fiesta-infantil:0.6`): 3
- Primer cumpleaños (`primer-cumpleanos`): 3
- Tropical / hawaiana (luau) (`tropical-hawaiana`): 3
- Halloween (`halloween`): 3

## Items

| Item | Rejected (rules) | Final celebrations | Final themes |
|---|---|---|---|
| Columna por bloques de 4 colores | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Piratas |
| Abeja (insecto) | Mariposas | general | — |
| Amiguito con sombrero · #9 | Flores / jardín | general | — |
| Mariquita · #734 | Mariposas | Cumpleaños infantil | — |
| Arco Mis 15 años | Fiesta infantil | Quince años (quinceañera), Cumpleaños | — |
| Centro de mesa Filigree | Aniversario de pareja | Boda | Elegante / lujo |
| Ramo confetti, blanco, palo de rosa y arena | Aniversario de pareja | Boda, Navidad | Lunares / confeti |
| Ramo corazones modernos, plata y graffiti | Invierno / nieve, Minimalista | San Valentín / amor y amistad, Día de la Madre | Corazones |
| Ramo corazones modernos, rosado y violeta | Minimalista | San Valentín / amor y amistad | Corazones |
| Ramo Dorado, Cristal Rojo, Verde Lima, Chocolate y Arena | Aniversario de pareja | Boda | — |
| Dulce corazón: varitas de corazón | Dulces / candy | San Valentín / amor y amistad | Corazones |
| Farol encantado | Fantasía / hadas | San Valentín / amor y amistad | Oriental / asiática, Corazones |
| Feliz Navidad: R-24 de estrellas con cuartetos | Flores / jardín | Navidad | Estrellas / noche |
| Malla flor fucsia y verde | despedida-soltera:0.85, fiesta-infantil:0.6 | Boda | Flores / jardín |
| Bautizo unisex: mesa de postres con dos ramos | dulces-candy:0.6 | Bautizo | Pastel / macaron |
| Calabazas Reflex (centro de mesa) | flores-jardin:0.6 | Halloween | Otoño |
| Centro de mesa para mamá | san-valentin:0.95, corazones:0.6 | Día de la Madre | — |
| Columna espiral fútbol | mundial-futbol:0.7 | Cumpleaños, Fiesta infantil | Deportes |
| Columna foil luna | fiesta-infantil:0.6 | Baby shower | Estrellas / noche |
| Columna romana con burbuja | fiesta-infantil:0.6 | Baby shower | — |
| Columna Mi Primera Comunión | Bautizo | Primera comunión | — |
| Columna Mis Quince Años | Cumpleaños | Quince años (quinceañera) | — |
| Columna orgánica Encanto Dorado | Aniversario de pareja | Boda, Baby shower, Bautizo, Primera comunión | Glam dorado |
| Columna orgánica reloj de arena | Aniversario de pareja | Boda | — |
| Corona navideña con moño | Princesas | Navidad | — |
| Corporativo: colgantes de supermercado | Vitrina / escaparate | general | — |
| Cumpleaños violeta y plata: mesa de postres | Primera comunión, Bautizo | Cumpleaños | Metálico / cromado |
| Aro pastel melón Feliz Cumpleaños | Flores / jardín | Cumpleaños | Pastel / macaron |
| Desayuno sorpresa: M de mamá | San Valentín / amor y amistad | Día de la Madre, Brunch | — |
| Aro Encanto orgánico | Navidad, Primera comunión, Aniversario de pareja | Boda, Baby shower, Bautizo | Glam dorado |
| Flor de corazones dorados (columna con flor y helio) | Fiesta infantil | San Valentín / amor y amistad, Cumpleaños | Corazones, Flores / jardín, Glam dorado |
| Corona navideña verde con moño dorado | Princesas | Navidad | — |
| Corona navideña roja con moño amarillo | Princesas, Safari / jungla | Navidad | — |
| Huevos de Pascua polka con ramos de helio | Flores / jardín | Pascua | — |
| Malla marina en franjas con ramos de mármol | Primer cumpleaños | Cumpleaños | Náutico / marino |
| Mural bandera de Australia | Independencia / fiestas patrias | general | — |
| Palmera amarilla de cuartetos | Flores / jardín | Cumpleaños | Tropical / hawaiana (luau) |
| Árbol esfera verde | Flores / jardín | Cumpleaños | Orgánico natural (verdes y hojas) |
| Árbol de manzanas | Flores / jardín | Cumpleaños | Frutas (cítricos, sandía) |
| Celebra con mamá: malla plata y violeta con mesa | Corazones | Día de la Madre | Metálico / cromado |
| Centro de mesa Feliz Día Mami | Cumpleaños | Día de la Madre | — |
| Christmas: arco orgánico Merlot, coral y crema | Tropical / hawaiana (luau), Rústico | Navidad | — |
| Colorful Vibes: orgánico multicolor con panel Happy Birthday | Cactus / desierto | Cumpleaños | Arcoíris |
| Feliz Año Nuevo: guirnalda negra y plata con ramo | Navidad | Año nuevo | Metálico / cromado |
| Día del Árbol: árbol de globos | Flores / jardín | general | Orgánico natural (verdes y hojas) |
| Pinturas: pared de franjas arcoíris | Dulces / candy | general | Arcoíris |
| Ramo de flores de tubito en reflex | Aniversario de pareja, Bautizo | Día de la Madre, San Valentín / amor y amistad, Boda | Flores / jardín |
| Escenario Halloween: malla, guirnalda cromada y calderos | Flores / jardín | Halloween | Metálico / cromado, Monstruos amistosos |
| Feliz día bigotes y padres: aro dorado y ramos | Cumpleaños | Día del Padre | Elegante / lujo |
| Arco bebito: cadena de R-12 celestes con nudos de R-5 azul rey | Fiesta infantil | Baby shower | — |
| Bouquet Feliz Día con estrella verde y base de números | Boda | Cumpleaños, San Valentín / amor y amistad, Aniversario de pareja | Estrellas / noche |
| Algas marinas de tubitos con burbujas | Flores / jardín | general | Náutico / marino |
| Árbol de corazones rosado | Bosque encantado | San Valentín / amor y amistad, Cumpleaños | Corazones, Flores / jardín |
| Árbol de Navidad de cuartetos con estrella | Estrellas / noche | Navidad | — |
| Arco feliz día de columnas en espiral y cima de eslabones | Flores / jardín | Cumpleaños | — |
| Arco orgánico rosa con impresos Feliz Día Mami | Flores / jardín | Día de la Madre | — |
| Base I love you: letras plata y corazones rojos sobre cuartetos dorado rosa | Flores / jardín | San Valentín / amor y amistad | Corazones |
| Bebé 1 año: columna lila con el 1 rosado | Fiesta infantil | Primer cumpleaños | — |
| Bouquet baby shower: tríos de helio con tetero «It's a boy» | Fiesta infantil | Baby shower | — |
| Bouquet Feliz Día con animal print y flor verde lima | Primer cumpleaños | general | Safari / jungla, Flores / jardín |
| Bouquet sombrero Día del Padre: ramo de helio sobre sombrero de copa | Fiesta infantil | Día del Padre | — |
| Centro de mesa momento inolvidable: tres flores y rizos | San Valentín / amor y amistad | general | Flores / jardín |
| Centro de mesa niño con biberones | Fiesta infantil | Baby shower, Bienvenida de bebé / nacimiento | — |
| Colgante Nemo: racimo de colores sobre globo naranja | Fiesta infantil | Cumpleaños, Cumpleaños infantil | Náutico / marino |
| Columna 15 años en reloj de arena con el 15 | Cumpleaños | Quince años (quinceañera) | — |
| Columna Angry Birds | Fiesta infantil | Cumpleaños, Cumpleaños infantil | — |
| Columna Baby Shower niña con luna | Fiesta infantil | Baby shower | Estrellas / noche |
| Columna Baby Shower niño con luna | Fiesta infantil | Baby shower | Estrellas / noche, Mariposas |
| Columna cebra en espiral | Fiesta infantil | general | Safari / jungla, Bicolor (dos colores) |
| Columna Happy Birthday Princess | Fiesta infantil | Cumpleaños, Cumpleaños infantil | Princesas |
| Columna Huellita | Primer cumpleaños, Fiesta infantil | Cumpleaños, Cumpleaños infantil | Mascotas (perros y gatos) |
| Columna Niño | Fiesta infantil | Baby shower, Bienvenida de bebé / nacimiento | — |
| Columna Toy Story | Fiesta infantil | Cumpleaños, Cumpleaños infantil | Arcoíris |
| El duende: columna de personaje con cara y sombrero de copa | Fiesta infantil | Cumpleaños, Cumpleaños infantil | Fantasía / hadas |
| Feliz cumpleaños neón: columna apilada con coronas de rizos | Princesas | Cumpleaños | Neón |
| Malla «Es una niña»: pared blanca con centros rosados y marco fucsia | Fiesta infantil | Baby shower, Bienvenida de bebé / nacimiento | — |
| Mar: aro azul con algas de tubito y peces payaso | Circo / carpa | Cumpleaños, Cumpleaños infantil | Náutico / marino |
| Mi boda: torre dorada con margaritas y globos de helio | Aniversario de pareja | Boda | Flores / jardín, Glam dorado |
| Mural animal print: malla negra con corazón rosado | Despedida de soltera | general | Corazones, Safari / jungla |
| Primaveral: malla blanca con pasto, flores y metalizados | Cumpleaños | general | Flores / jardín, Mariposas |
| Revelación de género: globo «?» con collar sobre base orgánica | Fiesta infantil | Revelación de género, Baby shower | — |
| Semiarco orgánico rosado, fucsia y Reflex | Cumpleaños, Fiesta infantil | general | — |
| Sorpresa neón: tres regalos de cuartetos con cintas y helio | Flores / jardín | Cumpleaños | Neón |
| Tazmania: columna café rosado con Taz metalizado | Fiesta infantil | Cumpleaños infantil | — |
| Topiario Reflex dorado rosa y plata: bola de 12 R-12 sobre un nido de rizos | Aniversario de pareja, Boda, Cumpleaños | general | Metálico / cromado, Elegante / lujo |
| Wedding shower: pared de R-12 perla y ramo de helio con letreros | Cumpleaños | Bridal shower / lluvia de regalos | — |
| Árbol de Navidad de Chris Horne: cono verde con esferas de colores y flor de pascua | Pascua, Flores / jardín | Navidad | — |
| Arbolito de Navidad con Link-O-Loon 660: pisos de lazos verdes y estrella | Estrellas / noche | Navidad | — |
| Arco acuático: arco de Link-O-Loon azul con peces y caracolas | Cumpleaños | general | Náutico / marino |
| Arco orgánico aguamarina: dorado rosa, perla y champaña con burbujas y rizos | Cumpleaños, Fiesta infantil | general | Metálico / cromado |
| Arco sirenita: tiras de Link-O-Loon en degradé de azules con espuma y Sirenita | Cumpleaños | general | Sirenas, Náutico / marino |
| Arco teteros: columnas lila rematadas en tetero y arco de eslabones rosados | Fiesta infantil | Baby shower | Pastel / macaron |
| Aurora Mist Nacional 2025: pared Reflex Violeta entre columnas orgánicas caribe y orquídea | Cumpleaños | general | Flores / jardín |
| Baby shower dorado y rosado: pared rosada con letra cursiva dorada y columnas con estrella | Cumpleaños | Baby shower | Glam dorado, Estrellas / noche |
| Bonsái cerezo: tronco dorado enrollado y copa orgánica rosada y roja | Rústico | San Valentín / amor y amistad | Orgánico natural (verdes y hojas), Oriental / asiática |
| Cartera fashion: cartera de globitos fucsia con asa negra y ramo de helio | Despedida de soltera | general | — |
| Castillo Enredados: torre gris con la trenza amarilla de Rapunzel y ramo de helio | Cumpleaños | general | Princesas |
| Catrina: falda de cuartetos blancos, cabeza de calavera, corona de flores y rosa roja | Halloween | Día de Muertos | Flores / jardín |
| Centro de mesa unicornio: cabeza blanca con cuerno dorado y corona de flores y ramo de helio | Fiesta infantil | Cumpleaños infantil | Unicornio, Flores / jardín |
| Columna Hello Kitty: cuartetos lila, fucsia y rosado de corazones con Hello Kitty de globos encima | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Corazones |
| Columna mariquita: espiral blanca, negra y roja de lunares con mariquitas y ramo de helio | Cumpleaños | Fiesta infantil, Cumpleaños infantil | Lunares / confeti |
| Columna unicornio: espiral pastel con cuartetos de nubes y cabeza de unicornio con cuerno dorado | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Unicornio, Pastel / macaron |
| Conejo de Pascua: salón rosado con la cenefa de globos en la viga, conejos, letras y carretillas | Cumpleaños, Fiesta infantil | Pascua | Pastel / macaron |
| 2012 en columna | Flores / jardín | general | — |
| Árbol de corazones mini | Cumpleaños, Flores / jardín | San Valentín / amor y amistad | Corazones |
| Centro de mesa estrella | Día del Padre | general | Estrellas / noche |
| Semiarco orgánico fucsia, rosa y plata en J | Cumpleaños, Quince años (quinceañera) | general | — |
| Arco orgánico de racimos naranja y azul naval | Cumpleaños, Graduación, Halloween | general | Bicolor (dos colores) |
| Arco en L cromado negro, oro y plata | Cumpleaños, Graduación | Año nuevo | Metálico / cromado, Glam dorado |
| Guirnalda sobre aro dorado nude, palo de rosa y champaña | Baby shower, Boda, Día de la Madre | general | Elegante / lujo, Glam dorado |
| Guirnalda en S lila y plata cromada | Boda, Cumpleaños, Quince años (quinceañera) | general | Flores / jardín, Metálico / cromado |
| Arco orgánico cromado negro, oro y plata | Boda, Graduación | Año nuevo | Metálico / cromado, Glam dorado |
| Arco asimétrico dorado perlado de un solo color | Año nuevo, Boda, Graduación | general | Monocromático, Glam dorado, Elegante / lujo |
| Arco asimétrico en degradé de coral a menta | Baby shower, Cumpleaños, Monocromático | general | Pastel / macaron |
| Guirnalda sobre marco blanco de rojo a durazno con flores | Boda, Cumpleaños, Día de la Madre | general | Flores / jardín |
| Arco orgánico menta, azul empolvado y blanco | Baby shower, Bautizo, Cumpleaños, Primera comunión, Tropical / hawaiana (luau) | general | Pastel / macaron |
| Columna orgánica recta multicolor rosa, café y naranja | Cumpleaños, Fiesta infantil, Arcoíris | general | — |
| Columna orgánica de cuatro franjas de color | Cumpleaños, Graduación, Fiesta infantil | general | — |
| Columna orgánica pastel de seis colores | Baby shower, Cumpleaños, Fiesta infantil, Tropical / hawaiana (luau), Flores / jardín | Pascua | Pastel / macaron |
| Columna orgánica negra, roja y oro con remate dorado | Año nuevo, Cumpleaños, Graduación | general | Hollywood / cine, Glam dorado |
| Par de columnas blanco, negro y oro con remate blanco | Año nuevo, Boda, Graduación | general | Elegante / lujo, Glam dorado |
| Par de columnas otoñales naranja y oro con espiral y girasoles | Cumpleaños, Halloween | general | Otoño, Flores / jardín |
| Columna de bienvenida crema, negro y oro por franjas con remate | Año nuevo, Boda, Graduación | Bienvenida / regreso a casa | Elegante / lujo, Glam dorado |
| Columna pastel con flores de globo y remate durazno | Baby shower, Cumpleaños, Fiesta infantil | general | Pastel / macaron, Flores / jardín |
| Columna champaña inclinada blanco perla y oro | Año nuevo, Boda, Cumpleaños, Graduación | general | Elegante / lujo, Glam dorado |
| Columna bastón en degradé de rosa palo a blanco con moños | Baby shower, Bautizo, Día de la Madre, Primera comunión, Monocromático | general | Pastel / macaron |
| Mesa de dinosaurios con guirnalda verde y dorada | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Dinosaurios, Safari / jungla |
| Portal rojo de columnas clásicas con orbes dorados y flecos | Fiesta infantil | Cumpleaños | Glam dorado |
| Medio arco menta, blanco y verde con letrero sobre la mesa | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Dinosaurios, Pastel / macaron |
| Guirnalda Frozen azul, lila y plata con «LET IT GO» | Cumpleaños | Cumpleaños infantil, Fiesta infantil | Invierno / nieve, Princesas |
| Medio arco dorado, rosa y confeti que baja por la izquierda | Boda | Despedida de soltera, Bridal shower / lluvia de regalos | Glam dorado, Lunares / confeti |
