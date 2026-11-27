"""Fixtures compartidas de las pruebas (§17).

Cada prueba obtiene su propio engine con NullPool: pytest-asyncio crea un bucle
nuevo por prueba y las conexiones no deben viajar entre bucles.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core import security
from app.core.config import settings
from app.database.session import get_session
from app.main import app


def _make_engine():
    return create_async_engine(settings.database_url, poolclass=NullPool)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http


@pytest.fixture(autouse=True)
async def app_session() -> AsyncIterator[None]:
    """Sustituye la sesión de la app por una ligada al bucle de la prueba."""
    engine = _make_engine()
    maker = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_session():
        async with maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = _get_session
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)
        await engine.dispose()


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Sesión real; se omite si no hay PostgreSQL accesible."""
    engine = _make_engine()
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        await engine.dispose()
        pytest.skip(f"PostgreSQL no disponible: {exc}")

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


@pytest.fixture
def fake_firebase(monkeypatch) -> str:
    """Sustituye la verificación de Firebase solo dentro de la prueba."""
    uid = f"test-{uuid.uuid4()}"

    def _verify(token: str) -> dict:
        if token == "token-invalido":
            raise security.InvalidToken("Token de prueba inválido")
        return {"uid": uid, "email": f"{uid}@example.com", "name": "Prueba LexIA"}

    monkeypatch.setattr(security, "verify_firebase_token", _verify)
    return uid


@pytest.fixture
async def cleanup_user(db, fake_firebase) -> AsyncIterator[str]:
    """Usuario de prueba creado por la API; se elimina al terminar."""
    yield fake_firebase
    parametros = {"uid": fake_firebase}
    await db.execute(
        text(
            "DELETE FROM consultas WHERE usuario_id IN "
            "(SELECT id FROM usuarios WHERE firebase_uid = :uid)"
        ),
        parametros,
    )
    await db.execute(
        text(
            "DELETE FROM auditoria WHERE usuario_id IN "
            "(SELECT id FROM usuarios WHERE firebase_uid = :uid)"
        ),
        parametros,
    )
    await db.execute(text("DELETE FROM usuarios WHERE firebase_uid = :uid"), parametros)
    await db.commit()
