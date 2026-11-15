def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "priya.nair@northwind.io",
        "password": "Password123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "priya.nair@northwind.io"
    assert data["user"]["role"] == "admin"

def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "priya.nair@northwind.io",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "INVALID_CREDENTIALS"

def test_get_me(client, admin_headers):
    res = client.get("/api/v1/auth/me", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "priya.nair@northwind.io"

def test_get_me_unauthorized(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "error" in res.json()
