# Copyright 2025 masa@kugel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
import os
from fastapi import status

@pytest.mark.asyncio()
async def test_cross_tenant_login_isolation(http_client):
    """test_cross_tenant_login_isolation
    Verify that a user from one tenant cannot login using another tenant's ID.
    """
    tenant_a = "TENANT_A"
    tenant_b = "TENANT_B"

    # 1. Register superuser for Tenant A
    response = await http_client.post(
        "/api/v1/accounts/register", 
        json={"username": "admin_a", "password": "password_a", "tenant_id": tenant_a}
    )
    assert response.status_code == status.HTTP_201_CREATED

    # 2. Register superuser for Tenant B
    response = await http_client.post(
        "/api/v1/accounts/register", 
        json={"username": "admin_b", "password": "password_b", "tenant_id": tenant_b}
    )
    assert response.status_code == status.HTTP_201_CREATED

    # 3. Attempt to login as admin_a but specifying tenant_b
    response = await http_client.post(
        "/api/v1/accounts/token",
        data={"username": "admin_a", "password": "password_a", "client_id": tenant_b},
    )
    # Should fail with 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect username, password or tenant_id"

    # 4. Attempt to login as admin_b but specifying tenant_a
    response = await http_client.post(
        "/api/v1/accounts/token",
        data={"username": "admin_b", "password": "password_b", "client_id": tenant_a},
    )
    # Should fail with 401 Unauthorized
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # 5. Success case: login as admin_a with tenant_a
    response = await http_client.post(
        "/api/v1/accounts/token",
        data={"username": "admin_a", "password": "password_a", "client_id": tenant_a},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
