def can_read_booking(actor: dict, booking: dict) -> bool:
    return (
        actor["tenant_id"] == booking["tenant_id"]
        and actor["id"] == booking["owner_id"]
        or actor["role"] == "admin"
    )
