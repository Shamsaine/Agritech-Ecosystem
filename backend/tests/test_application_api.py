import pytest

pytestmark = pytest.mark.asyncio


async def test_list_applications(client, imported_pilot_data):
    response = await client.get("/api/v1/applications")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "pagination" in body
    assert body["pagination"]["total_items"] == 38


async def test_page_must_be_positive(client):
    response = await client.get("/api/v1/applications?page=0")
    assert response.status_code == 422


async def test_page_size_has_limit(client):
    response = await client.get("/api/v1/applications?page_size=101")
    assert response.status_code == 422


async def test_unknown_application_is_404(client):
    response = await client.get("/api/v1/applications/not-real")
    assert response.status_code == 404
