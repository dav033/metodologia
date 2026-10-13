# Access contract v1
A booking is readable only if actor.tenant_id equals booking.tenant_id AND the actor is either its owner or an admin of that same tenant. An admin from another tenant must be denied. No global-admin role exists. Inputs shown are already validated at the boundary. No new dependencies or broader access are requested.
