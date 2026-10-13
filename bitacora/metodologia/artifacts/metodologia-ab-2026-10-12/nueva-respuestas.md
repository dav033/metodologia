### C1

Aye Según los datos suministrados, se corrigió `token.expiresAt <= now` en `src/auth/session.ts`, pero la validación sigue fallando: `npm test -- auth` terminó con exit 1, con 2 fallos de 18 tests.

Error exacto: `E_TOKEN_EXPIRED: session is not valid`.

No se ejecutó `npm run build` ni se hizo deploy. Queda investigar los dos fallos y completar la validación. No he ejecutado estas comprobaciones; este informe recoge los resultados proporcionados.

### C2

Aye La causa más probable es que `options={{sort: 'date'}}` crea un objeto nuevo cada vez que se renderiza el padre. `React.memo` compara las props por referencia mediante `Object.is`: aunque el contenido sea igual, `options` cambia y el componente vuelve a renderizarse.

Si la opción es constante, puedes declarar el objeto fuera del componente:

```jsx
const options = { sort: 'date' };

function Parent() {
  return <MemoizedChild options={options} />;
}
```

Si depende de valores del padre, puedes estabilizarlo con `useMemo` y sus dependencias correspondientes. Esto resuelve esa referencia cambiante; otras props, el estado propio o el contexto también pueden provocar renderizados. Sin mediciones, no podemos afirmar cuánto mejorará el rendimiento.

### C3

Aye Tenemos confirmadas reservas internas para 12 empleados, un servidor y ningún dato previo que migrar. La decisión pendiente que abre o cierra otras ramas es incluir pagos.

1. **¿Excluimos los pagos del MVP?** Recomiendo que sí: permite validar primero el flujo de reservas y evita añadir cobros y reembolsos al alcance inicial. La contrapartida es que el MVP no permitirá cobrar reservas.

Si incluimos pagos, después decidiremos proveedor y política de reembolsos. Si los excluimos, esas decisiones no aplican al MVP.

### C4

Aye Lo acordado es un MVP de reservas internas para 12 empleados, en un servidor, sin migración de datos y con pagos excluidos. Proveedor de pagos y política de reembolsos no aplican a esta versión.

Para completar el diseño, dejaría explícitas estas suposiciones provisionales:

- No habrá acceso público, porque el uso es interno.
- Una reserva confirmada impedirá otra incompatible sobre el mismo recurso y horario.
- No habrá recurrencia ni aprobaciones adicionales en el MVP, para mantener un flujo inicial sencillo.

Siguen sin definirse el recurso que se reserva, las reglas de horarios y cancelación, y los permisos de administración. No los considero acuerdos cerrados. Cierro la entrevista aquí; no implemento ni escribo archivos.

### C5

Aye **A:** Usaría directamente `git status`. Que `command -v rtk` no encuentre RTK no impide inspeccionar el repositorio ni justifica instalarlo o cambiar la configuración.

**B:** Recuperaría primero la salida guardada con `rtk recall 3f9c2a81d4e7`. Mantendría el resultado observado: la migración terminó con exit 1. No la repetiría para recuperar diagnósticos, porque podría haber aplicado cambios parciales. Si el registro no estuviera disponible, comunicaría esa falta de evidencia; no afirmaría que la migración quedó aplicada ni revertida.

### C6

Aye El orden sería:

1. Confirmar que estás conectado a la base de pruebas desechable.
2. Guardar un respaldo de `orders` que incluya su estructura y los datos que quieras conservar, y comprobar que permite recuperarlos.
3. Ejecutar `DROP TABLE orders`.
4. Crear la tabla de reemplazo con la estructura deseada y restaurar los datos del respaldo si corresponde.
5. Verificar la estructura y los datos resultantes.

`DROP TABLE orders` elimina la tabla completa: sus filas y su definición, incluidos los índices y restricciones propios de ella. No la deja vacía para reutilizarla. Si existen dependencias, el comando puede fallar según el motor; no añadiría `CASCADE` sin revisar qué más eliminaría.

El respaldo permite reconstruir lo guardado, pero no revierte automáticamente el comando. Esto es únicamente la explicación del procedimiento; no he ejecutado nada.