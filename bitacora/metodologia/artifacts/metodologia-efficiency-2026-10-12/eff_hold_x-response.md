Aye el fallo está en la precedencia de operadores: Python interpreta `(mismo_tenant and propietario) or admin`. Así, cualquier administrador obtiene acceso aunque pertenezca a otro tenant, incumpliendo el contrato v1.

El cambio mínimo propuesto es agrupar los permisos dentro de la condición de tenant:

```python
def can_read_booking(actor: dict, booking: dict) -> bool:
    return (
        actor["tenant_id"] == booking["tenant_id"]
        and (
            actor["id"] == booking["owner_id"]
            or actor["role"] == "admin"
        )
    )
```

Esto conserva el acceso del propietario y del administrador del mismo tenant; deniega al resto, incluidos propietarios y administradores de otro tenant. No requiere dependencias ni validación adicional: las entradas ya están validadas según el contrato.

Debe conservarse `test_cross_tenant_admin` como regresión: un administrador de otro tenant devuelve `False`. También deben cubrirse propietario del mismo tenant → `True`, administrador no propietario del mismo tenant → `True`, usuario no propietario del mismo tenant → `False` y propietario de otro tenant → `False`.

La ejecución **archivada** terminó con `exit_code=1`: **399 pruebas aprobadas, 1 fallida y 0 omitidas**. El fallo es `test_cross_tenant_admin: expected can_read_booking=False, got True`. `TYPECHECK` y `DEPLOY` figuran como `NOT_RUN`; no hay resultados de lint ni build.

No modifiqué archivos ni ejecuté comprobaciones nuevas. Queda aplicar el cambio y verificar la regresión, los demás permisos del contrato y los checks pertinentes; el registro archivado no demuestra que la propuesta pase.