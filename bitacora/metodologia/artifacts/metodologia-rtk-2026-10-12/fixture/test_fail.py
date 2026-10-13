def test_touching_intervals():
    assert True is False, "E_OVERLAP: touching endpoints must not overlap"

def test_cross_tenant_admin():
    raise PermissionError("E_TENANT_DENIED: tenant_b must be inaccessible")

def test_expired_token():
    raise ValueError("E_TOKEN_EXPIRED: session is not valid")
