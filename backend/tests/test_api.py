import pytest

from app.services.citaciones import CONTINGENCIA


async def test_health_expone_dependencias(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert set(body["dependencias"]) == {"postgres", "redis", "firebase", "openai"}
    assert body["status"] in {"ok", "degradado"}


async def test_perfil_sin_token_es_401(client):
    response = await client.get("/api/profile")
    assert response.status_code == 401
    assert "Bearer" in response.json()["detail"]


async def test_token_invalido_es_401(client, fake_firebase):
    response = await client.post(
        "/api/auth/session", headers={"Authorization": "Bearer token-invalido"}
    )
    assert response.status_code == 401


async def test_sesion_vincula_perfil_y_roles(client, cleanup_user):
    response = await client.post(
        "/api/auth/session", headers={"Authorization": "Bearer token-valido"}
    )
    assert response.status_code == 200
    perfil = response.json()["perfil"]
    assert perfil["roles"] == ["usuario"]
    assert "chat.usar" in perfil["permisos"]
    assert "admin.usuarios" not in perfil["permisos"]


async def test_endpoint_admin_exige_permiso(client, cleanup_user):
    response = await client.get(
        "/api/admin/users", headers={"Authorization": "Bearer token-valido"}
    )
    assert response.status_code == 403
    assert "admin.usuarios" in response.json()["detail"]


@pytest.mark.parametrize("ruta", ["/api/documentos", "/api/leyes", "/api/fuentes"])
async def test_catalogo_publico_sin_token(client, ruta):
    response = await client.get(ruta)
    assert response.status_code == 200


async def test_consultas_exige_token(client):
    response = await client.get("/api/consultas")
    assert response.status_code == 401


async def test_chat_sin_fundamento_devuelve_contingencia(client, cleanup_user):
    response = await client.post(
        "/api/chat",
        json={"pregunta": "¿Qué dice la ley sobre honorarios?"},
        headers={"Authorization": "Bearer token-valido"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["fundamento_suficiente"] is False
    assert body["respuesta"] == CONTINGENCIA
    assert body["fuentes"] == []
