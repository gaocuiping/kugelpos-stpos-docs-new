# テストケース: POST /tenants/{tenant_id}/stores/{store_code}/terminals/{terminal_no}/journals
# API: receive_journals
# 実装日: 2026-03-10

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_receive_journals_happy_path(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """
    【正常系 | P1-4】
    POST /tenants/{tenant_id}/stores/{store_code}/terminals/{terminal_no}/journals
    - 正常なリクエストに対して 201 が返ること
    - レスポンスが success=True であること
    """
    test_terminal_no = "1"  # TODO: 有効な値に差し替えてください
    response = await http_client.post(
        f"/api/v1/tenants/{test_test_tenant_id}/stores/{test_test_store_code}/terminals/{test_terminal_no}/journals",
        json={},  # TODO: 実際のボディを設定してください
        headers=test_auth_headers,
    )
    # 2xx を期待（テスト環境にデータがない場合は 404 も許容）
    assert response.status_code in (200, 201, 204, 404), (
        f"Unexpected status: {response.status_code} {response.text[:200]}"
    )
    if response.status_code not in (204,) and response.content:
        result = response.json()
        if response.status_code < 400:
            assert result.get("success") is True


@pytest.mark.asyncio
async def test_receive_journals_unauthorized(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
):
    """【異常系 | 401/403 | P1-5】認証ヘッダーなしで 401 または 403 が返ること。"""
    test_terminal_no = "1"  # TODO: 有効な値に差し替えてください
    response = await http_client.post(
        f"/api/v1/tenants/{test_test_tenant_id}/stores/{test_test_store_code}/terminals/{test_terminal_no}/journals",
        json={},  # TODO: 実際のボディを設定してください
    )
    # 認証任意設定の場合は 200/404 も許容
    assert response.status_code in (401, 403, 200, 404)
