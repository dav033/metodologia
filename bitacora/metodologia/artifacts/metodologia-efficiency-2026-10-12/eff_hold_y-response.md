Aye el fallo permite que un administrador lea reservas de otro tenant. En Python, `and` tiene mayor precedencia que `or`: la expresión actual equivale a `(same_tenant and is_owner) or is_admin`, dejando al administrador fuera de la restricción de tenant.

El cambio mínimo propuesto en `access.py` es agrupar propietario y administrador:

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

Esto conserva el contrato v1: propietario o administrador del mismo tenant pueden leer; cualquier actor de otro tenant queda rechazado, incluso si coincide con `owner_id`. Las entradas ya están validadas; no hacen falta dependencias ni validaciones nuevas.

Debe mantenerse `test_cross_tenant_admin` como regresión: administrador del tenant A ante una reserva del tenant B → `False`. También debe comprobarse esta matriz para preservar todos los permisos:

| Actor | Mismo tenant | Otro tenant |
|---|---|---|
| Propietario | `True` | `False` |
| Administrador no propietario | `True` | `False` |
| Usuario no propietario | `False` | `False` |

La ejecución **archivada** registra 400 tests: 399 pasan, 1 falla y 0 se omiten; código de salida `1`. El fallo es `test_cross_tenant_admin: expected can_read_booking=False, got True`. `TYPECHECK` y `DEPLOY` figuran como `NOT_RUN`; no hay evidencia de lint ni build.

No modifiqué archivos ni ejecuté checks nuevos. Falta aplicar el cambio, verificar la regresión y la matriz, ejecutar la suite y los checks aplicables; el registro archivado no demuestra el resultado de la corrección.