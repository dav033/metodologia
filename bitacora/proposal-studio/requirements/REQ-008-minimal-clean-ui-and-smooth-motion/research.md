# Guías de usabilidad y diseño para Proposal Studio

**Consultadas:** 11 de octubre de 2026. Fuentes primarias: estándares W3C/WAI y documentación oficial de Material Design, GOV.UK, Carbon, Apple y Motion. Las recomendaciones de implementación al final son juicio aplicado al producto, no requisitos normativos.

## Hallazgos documentados

### Accesibilidad, contraste y foco

- **WCAG 2.2 AA, texto:** el contraste mínimo es 4.5:1 para texto normal y 3:1 para texto grande; el criterio también cubre texto de controles y estados hover/focus. [W3C: Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- **WCAG 2.2 AA, elementos no textuales:** revisar bordes/estados de controles e indicadores gráficos, no solo texto. [W3C: Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
- Los controles operables por teclado requieren un indicador de foco visible; no debe desaparecer mientras el control siga enfocado. [W3C: Focus Visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)
- El foco no puede quedar completamente oculto por contenido creado por el autor; headers/footers fijos y overlays son causas típicas. [W3C: Focus Not Obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum)
- WCAG 2.2 AA establece 24×24 CSS px como tamaño mínimo para targets de puntero, con excepciones definidas (entre ellas separación suficiente); W3C recomienda considerar tamaños mayores para controles importantes. [W3C: Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum)

### Motion

- WCAG 2.2, criterio AAA 2.3.3: la animación no esencial iniciada por interacción debe poder desactivarse. W3C propone evitar movimiento innecesario, una preferencia del usuario o respetar la preferencia del sistema (`prefers-reduced-motion`). [W3C: Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions)
- Motion for React documenta una estrategia práctica: cuando hay reducción de movimiento, desactivar transformaciones y animaciones de layout, pudiendo conservar cambios de opacidad/color; recomienda quitar parallax y autoplay. [Motion: Accessibility](https://motion.dev/docs/react-accessibility)
- Material distingue movimiento espacial de efectos: overshoot puede ser expresivo, pero para aplicaciones utilitarias recomienda su esquema “Standard”, con movimiento funcional y mínimo rebote; efectos como opacidad no deberían rebotar. La página describe el sistema M3 Expressive anunciado en mayo de 2025. [Material 3: Motion](https://m3.material.io/styles/motion)
- Apple indica que componentes pueden adaptar motion según ajustes de accesibilidad y método de entrada. [Apple HIG: Motion](https://developer.apple.com/design/human-interface-guidelines/motion)

### Jerarquía, densidad y estructuras

- Material propone usar patrones de layout conocidos (feed, list-detail, supporting pane) según tarea y adaptarlos a breakpoints. Para supporting pane, el área principal ocupa típicamente cerca de dos tercios y el panel secundario el resto. [Material 3: Canonical layout examples](https://m3.material.io/foundations/layout/canonical-examples/overview)
- GOV.UK trata tipografía y espaciado como escalas coherentes, con tipografía adaptable entre móvil y escritorio; aconseja alinear estilos nuevos con la escala existente. [GOV.UK: Type scale](https://design-system.service.gov.uk/styles/type-scale/) · [Spacing](https://design-system.service.gov.uk/styles/spacing/)
- Para tablas, GOV.UK las recomienda cuando ayudan a comparar y escanear; usa encabezados semánticos y caption. [GOV.UK: Table](https://design-system.service.gov.uk/components/table/)
- Carbon recomienda títulos/columnas claros y breves, hover de fila para facilitar escaneo, acciones globales concentradas en toolbar y limitar el número de iconos allí. Su guía actual describe tablas para organizar datos y localizar recursos; documentación consultada actualizada el 30 de septiembre de 2026. [Carbon: Data table guidelines](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) · [Usage](https://v10.carbondesignsystem.com/components/data-table/usage/)
- GOV.UK aconseja probar primero el contenido sin tabs; considerar simplificar, separar páginas o dejar secciones visibles con encabezados. Las tabs sirven cuando el usuario necesita alternar rápidamente y ver una sección a la vez. [GOV.UK: Tabs](https://design-system.service.gov.uk/components/tabs/)

### Control de comparación con divisor arrastrable

- El patrón WAI-ARIA slider requiere foco en el thumb, rol/valores accesibles (`aria-valuenow/min/max`) y nombre accesible visible o `aria-label`. Teclas: flechas incrementan/decrementan; Home/End llevan al inicio/fin; Page Up/Down son opcionales. WAI advierte que algunas tecnologías táctiles asistivas pueden tener dificultades y recomienda probarlas con lectores/tecnologías relevantes. [W3C APG: Slider Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/slider/)
- WCAG define gestos de arrastre como una posible barrera; el criterio 2.5.7 exige una alternativa de puntero simple cuando una función usa dragging, salvo excepciones. [W3C: Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html)
- W3C APG describe el slider como un control para elegir un valor en un rango; el teclado y el valor textual accesible deben comunicar el valor actual de forma útil. [W3C APG: Slider Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/slider/)

## Recomendaciones verificables para este producto (juicio aplicado)

1. **Jerarquía:** cada pantalla debe tener un título inequívoco, una acción primaria, y luego contenido de apoyo. En admin, priorizar la lista/tabla de propuestas y estados sobre tarjetas métricas decorativas; mantener una toolbar pequeña. En propuesta pública, poner negocio/prototipo y el comparador como foco principal; mover contexto, hallazgos y contacto a secciones posteriores.
2. **Densidad:** mantener una sola escala de espacios y tipos; colapsar adornos, no información necesaria. Comprobar que en móvil no haya scroll horizontal involuntario y que encabezados/acciones sigan legibles. Para vistas multi-página, usar pestañas solo si se cambia entre páginas de prototipo con frecuencia; nombrarlas con rutas/páginas concretas.
3. **Estilo minimalista:** reducir glow, gradientes decorativos, blur, elevaciones y bordes muy redondeados. Separar grupos principalmente mediante espacio, tipografía y bordes discretos; reservar color de acento para acción/estado/selección. Medir contraste numéricamente: ≥4.5:1 texto normal, ≥3:1 texto grande y controles/gráficos donde aplique.
4. **Motion:** usar movimiento estándar corto y sobrio solo para comunicar cambios/continuidad (p. ej. fade o un desplazamiento pequeño al revelar contenido); evitar rebotes, parallax, loops y animaciones que retrasen una acción. Bajo `prefers-reduced-motion: reduce`, quitar transformaciones/animación espacial no esencial y dejar cambio instantáneo o fade mínimo.
5. **Comparador:** mantener el arrastre directo, pero también soportar click/tap para fijar posición, teclado (flechas, Home/End) y un nombre/valor anunciado por AT. Asegurar un área de agarre cómoda, foco de alto contraste y que el thumb/foco no quede tapado por controles flotantes. Probar lector de pantalla y touch con AT porque WAI señala soporte variable.
6. **Pruebas de revisión para auditores:** (a) recorrer toda la UI solo con Tab/Shift+Tab/Enter/Escape/flechas; (b) activar reduce-motion del sistema y verificar que no haya desplazamientos/bounce no esenciales; (c) probar el comparador con mouse, touch, teclado y lector de pantalla; (d) medir colores reales de texto, bordes y foco; (e) a 320–375 px de ancho, comprobar jerarquía, targets y ausencia de solapamientos; (f) escanear la vista admin durante unos segundos y comprobar que título, estado y siguiente acción de cada propuesta se identifican sin leer adornos.

## Límites de la investigación

- Estas guías no prescriben una estética universal “minimalista”, valores exactos de duración/espaciado para Proposal Studio, ni demuestran qué versión visual convertirá mejor. Esos juicios requieren inspección del producto y, de ser posible, pruebas con usuarios.
- La guía de Carbon v10 es heredada; se incluye como evidencia operativa de patrones (título, columnas, tabla/toolbar), contrastada con la documentación Carbon Core actualizada el 30-09-2026.
- El patrón WAI-ARIA es guía de autoría, no garantía de soporte uniforme de lectores o touch; validar en navegadores/dispositivos objetivo.
