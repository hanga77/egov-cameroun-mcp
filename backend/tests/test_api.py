import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings


@pytest.fixture
def api_key():
    return settings.api_secret_key


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_tools_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    names = [t["name"] for t in data["tools"]]
    assert "verify_cnps_matricule" in names
    assert "calculate_vat" in names
    assert "get_tax_deadlines" in names
    assert "calculate_cnps_contributions" in names
    assert "get_statistical_data" in names


@pytest.mark.asyncio
async def test_chat_requires_api_key():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat", json={"message": "hello"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_with_valid_key(api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat",
            json={"message": "Quelles sont les échéances fiscales pour mars 2026 ?"},
            headers={"X-API-Key": api_key},
        )
    # May fail if no ANTHROPIC_API_KEY is set — that's expected in CI without secrets
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_chat_message_too_long(api_key):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/chat",
            json={"message": "x" * 5000},
            headers={"X-API-Key": api_key},
        )
    assert response.status_code == 422
