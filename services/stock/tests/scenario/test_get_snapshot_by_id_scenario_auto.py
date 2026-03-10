# テストケース: GET /tenants/{tenant_id}/stores/{store_code}/stock/snapshot/{snapshot_id}
# API: get_snapshot_by_id
# 実装日: 2026-03-10
#
# 【対応する test-review.md 改善方案】
#   P1-4 : 未カバー API のシナリオテスト追加
#   P1-5 : 異常系（4xx/5xx）シナリオテスト追加

import pytest
from httpx import AsyncClient
from fastapi import status


# ─────────────────────────────────────────────
# ヘルパー: スナップショットを作成して ID を取得
# ─────────────────────────────────────────────

async def _create_and_get_snapshot_id(
    http_client: AsyncClient,
    tenant_id: str,
    store_code: str,
    auth_headers: dict,
) -> str:
    """スナップショットを作成し、一覧から ID を取得して返す。"""
    # 1. スナップショット作成
    create_resp = await http_client.post(
        f"/api/v1/tenants/{tenant_id}/stores/{store_code}/stock/snapshot",
        json={"createdBy": "test_get_by_id"},
        headers=auth_headers,
    )
    assert create_resp.status_code == status.HTTP_201_CREATED, (
        f"スナップショット作成に失敗: {create_resp.status_code} {create_resp.text}"
    )

    # 2. 一覧取得で最新スナップショットの ID を取得
    #    (作成レスポンスに id フィールドが含まれる場合はそちらを利用)
    created_data = create_resp.json().get("data", {})

    # camelCase の "id" フィールドを優先確認
    snapshot_id = (
        created_data.get("id")
        or created_data.get("snapshotId")
    )

    if not snapshot_id:
        # 一覧 API から最新の ID を取得
        list_resp = await http_client.get(
            f"/api/v1/tenants/{tenant_id}/stores/{store_code}/stock/snapshots",
            params={"page": 1, "limit": 1},
            headers=auth_headers,
        )
        assert list_resp.status_code == status.HTTP_200_OK
        items = list_resp.json()["data"]["data"]
        assert len(items) > 0, "スナップショット一覧が空です"
        snapshot_id = items[0].get("id") or items[0].get("snapshotId")

    assert snapshot_id, "スナップショット ID を取得できませんでした"
    return snapshot_id


# ─────────────────────────────────────────────
# 正常系テスト（Happy Path）
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_snapshot_by_id_happy_path(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """
    【正常系 | P1-4】
    GET /tenants/{tenant_id}/stores/{store_code}/stock/snapshot/{snapshot_id}
    - スナップショット作成後、その ID で取得できること
    - レスポンスが success=True で 200 を返すこと
    - tenantId / storeCode が一致すること
    - generateDateTime が含まれること
    """
    snapshot_id = await _create_and_get_snapshot_id(
        http_client, test_tenant_id, test_store_code, test_auth_headers
    )

    response = await http_client.get(
        f"/api/v1/tenants/{test_tenant_id}/stores/{test_store_code}/stock/snapshot/{snapshot_id}",
        headers=test_auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["success"] is True
    assert result["code"] == 200

    data = result["data"]
    assert data["tenantId"] == test_tenant_id
    assert data["storeCode"] == test_store_code
    assert "generateDateTime" in data
    assert "stocks" in data
    assert isinstance(data["stocks"], list)
    assert "totalItems" in data
    assert "totalQuantity" in data


# ─────────────────────────────────────────────
# 異常系テスト 4xx（P1-5 対応）
# ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_snapshot_by_id_not_found(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """
    【異常系 | 404 | P1-5】
    存在しない snapshot_id を指定した場合、404 Not Found が返ること。
    レスポンスの success フィールドが False であること。
    """
    nonexistent_id = "000000000000000000000000"  # 存在しない MongoDB ObjectId

    response = await http_client.get(
        f"/api/v1/tenants/{test_tenant_id}/stores/{test_store_code}/stock/snapshot/{nonexistent_id}",
        headers=test_auth_headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    result = response.json()
    assert result["success"] is False


@pytest.mark.asyncio
async def test_get_snapshot_by_id_unauthorized(
    http_client: AsyncClient,
    test_tenant_id: str,
    test_store_code: str,
    test_auth_headers: dict,
):
    """
    【異常系 | 401/403 | P1-5】
    認証ヘッダーなしでリクエストした場合、401 または 403 が返ること。
    """
    snapshot_id = await _create_and_get_snapshot_id(
        http_client, test_tenant_id, test_store_code, test_auth_headers
    )

    # 認証ヘッダーなしでリクエスト
    response = await http_client.get(
        f"/api/v1/tenants/{test_tenant_id}/stores/{test_store_code}/stock/snapshot/{snapshot_id}",
    )

    # 認証必須エンドポイントは 401 または 403 が期待される
    # （サービスの認証設定によって異なる場合があるため、いずれかを許容）
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ), (
        f"認証なしで {response.status_code} が返されました。"
        "401 / 403 のいずれかが期待されます。"
        "認証が任意設定の場合は、このテストを調整してください。"
    )
