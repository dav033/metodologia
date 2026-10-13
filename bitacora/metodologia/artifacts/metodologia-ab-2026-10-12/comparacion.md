# Metodología anterior vs. nueva — prueba A/B

## Resultado
La nueva consumió 30,38% menos tokens totales en esta ejecución. Los tokens de salida bajaron 3,03%; la entrada no cacheada bajó 7,24%. No se observó una mejora de concisión de la respuesta final: pasó de 580 a 599 palabras (+3,28%).

| Contador real del runtime | Anterior | Nueva | Reducción |
|---|---:|---:|---:|
| Entrada acumulada | 113.071 | 78.403 | 30,66% |
| Entrada cacheada (subconjunto) | 99.200 | 65.536 | 33,94% |
| Entrada no cacheada | 13.871 | 12.867 | 7,24% |
| Salida, incluidos razonamiento y llamadas | 1.156 | 1.121 | 3,03% |
| Razonamiento (subconjunto de salida) | 84 | 60 | 28,57% |
| Total: entrada + salida | 114.227 | 79.524 | 30,38% |
| Llamadas de herramientas | 3 | 2 | Una menos |

## Método
David pidió dos subagentes: uno con cada versión. Se crearon contextos nuevos con el mismo rol default, modelo gpt-6.1-sol y configuración de esfuerzo heredada. Los mensajes iniciales fueron idénticos salvo la ruta A/B. Ningún participante recibió la etiqueta anterior/nueva ni resultados esperados. La versión anterior es la copia exacta previa a la integración de Caveman/RTK/Grill Me, no Git HEAD. La nueva es el estado integrado actual.

Seis escenarios iguales: informe de tests fallidos; referencia cambiante en React.memo; decisión de pagos antes de proveedor; cierre de entrevista; RTK ausente y recuperación de migración fallida; explicación ordenada de DROP TABLE. Las operaciones eran simuladas. Solo podían leer su paquete de instrucciones; no hubo ejecuciones de tests, migraciones, RTK ni cambios en proyectos.

Los contadores se extrajeron de event_msg/token_count de las dos sesiones después de su finalización. Se verificó que los acumulados coinciden con la suma de los registros por llamada y que entrada + salida = total. La entrada cacheada es un subconjunto de la entrada, no se suma otra vez. Los tokens de salida incluyen razonamiento y llamadas de herramientas; no son solo el texto final visible.

## Calidad
Evaluación manual del coordinador con 18 criterios binarios fijados antes de las respuestas (rubric.json): 18/18 para ambas variantes. Conservaron datos exactos, fallos y comprobaciones no realizadas; identificaron la referencia nueva de React; preguntaron primero por pagos; terminaron la entrevista; recuperaron la salida de la migración sin repetirla y mantuvieron el orden respaldo → eliminación → reemplazo.

La recomendación y consecuencia de alcance se consideraron suficientes para el criterio de trade-off de C3 en ambas variantes. La nueva hizo más explícita la contrapartida de excluir cobros. No se detectó una mejora de corrección en esta muestra.

## Qué cambió y qué explica el ahorro
La anterior hizo tres lecturas: raíz, cuatro referencias y una búsqueda adicional. La nueva hizo dos: raíz y cuatro referencias que incluyen el nuevo documento específico. La anterior leyó documentación de bitácora; la nueva seleccionó la referencia de comunicación/RTK. La llamada extra de la anterior volvió a enviar un contexto grande, mayoritariamente cacheado. Esa diferencia explica buena parte de la reducción total observada; no es un ahorro provocado por compresión real de RTK.

Los textos finales tienen 3.722 frente a 3.939 caracteres y 580 frente a 599 palabras. La nueva no dio una respuesta final más corta, aunque consumió ligeramente menos salida total de la sesión por otras diferencias de herramientas/razonamiento.

## Límites
Una ejecución por variante, seis escenarios empaquetados en una respuesta y revisión manual: resultado exploratorio, sin significancia estadística. Ambos agentes comparten las instrucciones del harness, incluido un estilo conciso; se aisló el contenido leído de metodologia, no todo el sistema. No se ejecutó RTK ni se midió compresión de logs. Los tokens acumulados cuentan contexto reenviado por llamada; gran parte usa caché. La reducción de tokens totales no equivale a una reducción igual de dinero. No se calcularon precios ni consumo de la sesión coordinadora.

## Evidencia
- [Respuesta anterior](anterior-respuestas.md)
- [Respuesta nueva](nueva-respuestas.md)
- [Contadores y trazas de herramientas](metrics.json)
- [Protocolo](protocol.md)
- [Criterios previos](rubric.json)
- [Asignación de variantes](manifest.json)
