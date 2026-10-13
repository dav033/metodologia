C1

Aye Según los hechos suministrados, se corrigió la condición `token.expiresAt <= now` en `src/auth/session.ts`.

La comprobación reportada `npm test -- auth` terminó con código de salida 1: fallaron 2 de 18 tests. El error exacto fue:

```text
E_TOKEN_EXPIRED: session is not valid
```

No se ejecutó `npm run build` ni se hizo deploy. La corrección queda pendiente de validar: hay que investigar los dos fallos y completar las comprobaciones. No he ejecutado estas verificaciones.

C2

Aye La causa más probable es que `options={{sort: 'date'}}` crea un objeto nuevo cada vez que se renderiza el padre. `React.memo` compara las props por referencia; aunque el contenido sea igual, `options` cambia.

Si esas opciones son constantes, puedes declararlas fuera del componente:

```tsx
const OPTIONS = { sort: 'date' } as const;

function Parent() {
  return <MemoizedChild options={OPTIONS} />;
}
```

Si dependen de valores del padre, una alternativa es `useMemo` con las dependencias correspondientes. También puedes pasar `sort="date"` si el hijo solo necesita ese valor.

Esto explica el caso descrito; no demuestra una mejora de rendimiento ni descarta que otras props, el contexto o el estado del hijo provoquen renders.

C3

Aye Tenemos confirmadas reservas internas para 12 empleados, un servidor y ningún dato previo que migrar. La decisión de alcance que podemos resolver ahora es si el MVP incluye pagos; proveedor y reembolsos dependen de esa respuesta.

**¿Dejamos los pagos fuera del MVP?** Recomiendo **sí**, porque todavía no hay una necesidad de cobro confirmada y excluirlos reduce las decisiones necesarias para entregar las reservas.

Si decides incluirlos, la siguiente ronda abordará proveedor y política de reembolsos.

C4

Aye Lo acordado es un MVP de reservas internas para 12 empleados, alojado en un servidor, sin migración de datos y sin pagos. Por tanto, proveedor de pagos y política de reembolsos no aplican al MVP.

Quedan estas suposiciones de trabajo, todavía sin confirmar:

- Se reserva un recurso durante un intervalo de tiempo; falta concretar cuál.
- Cada empleado puede crear, consultar y cancelar sus propias reservas.
- No se permiten reservas solapadas para un mismo recurso.
- No habrá aprobación previa, lista de espera ni notificaciones en esta primera versión.

Las propongo para mantener un flujo inicial sencillo; no son requisitos ya acordados. No he implementado nada ni escrito archivos.

C5

Aye **A:** si `command -v rtk` no encuentra RTK, inspeccionaría el estado directamente con `git status`. No hace falta instalar RTK para esa lectura.

**B:** recuperaría primero la salida completa con:

```sh
rtk recall 3f9c2a81d4e7
```

Después revisaría el error y el estado real de la migración mediante comprobaciones de lectura. No repetiría la migración a ciegas: el código de salida 1 no demuestra que ningún cambio se haya aplicado.

Son los siguientes pasos propuestos; no he ejecutado nada ni puedo afirmar el resultado de la migración.

C6

Aye El orden sería:

1. Confirmar que estás conectado a la base de pruebas desechable.
2. Guardar un respaldo del esquema y de los datos de `orders`, y comprobar que permite restaurarlos.
3. Ejecutar `DROP TABLE orders`.
4. Crear la tabla de reemplazo con el esquema deseado.
5. Restaurar los datos que quieras conservar, adaptándolos al nuevo esquema si corresponde, y verificar el resultado.

`DROP TABLE orders` elimina la tabla completa: su definición y todas sus filas. El respaldo no se restaura automáticamente. Si otras tablas dependen de ella mediante claves foráneas, el comando puede fallar; habría que revisar esas dependencias antes de proceder.

Esto describe el procedimiento; no he ejecutado ningún comando.