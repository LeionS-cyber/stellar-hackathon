"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "email": "john@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    assert "tokens" in response.json()
    assert "user" in response.json()


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login"""
    # First register a user
    await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "username": "janedoe",
            "email": "jane@example.com",
            "password": "SecurePassword123!",
            "password_confirm": "SecurePassword123!",
        },
    )

    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "jane@example.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 200
    assert "tokens" in response.json()