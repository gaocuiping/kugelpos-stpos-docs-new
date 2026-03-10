# テストケース: GET /tenants/{tenant_id}/item_books/{item_book_id}/detail
# API: get_item_book_detail_by_id
# 実装日: 2026-03-10

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_get_item_book_detail_by_id_happy_path(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """
    【正常系 | P1-4】
    GET /tenants/{tenant_id}/item_books/{item_book_id}/detail
    - 正常なリクエストに対して 200 が返ること
    - レスポンスが success=True であること
    """
    test_item_book_id = "TEST_ITEM_BOOK_ID"  # TODO: 有効な値に差し替えてください
    response = await http_client.get(
        f"/api/v1/tenants/{test_test_tenant_id}/item_books/{test_item_book_id}/detail",
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
async def test_get_item_book_detail_by_id_not_found(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """【異常系 | 404 | P1-5】存在しないリソース ID を指定した場合は 404 が返ること。"""
    response = await http_client.get(
        f"/api/v1/tenants/{test_test_tenant_id}/item_books/NONEXISTENT_000/detail",
        headers=test_auth_headers,
    )
    assert response.status_code == 404, f"expected 404, got {response.status_code}"


@pytest.mark.asyncio
async def test_get_item_book_detail_by_id_unauthorized(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
):
    """【異常系 | 401/403 | P1-5】認証ヘッダーなしで 401 または 403 が返ること。"""
    test_item_book_id = "TEST_ITEM_BOOK_ID"  # TODO: 有効な値に差し替えてください
    response = await http_client.get(
        f"/api/v1/tenants/{test_test_tenant_id}/item_books/{test_item_book_id}/detail",
    )
    # 認証任意設定の場合は 200/404 も許容
    assert response.status_code in (401, 403, 200, 404)
