---
title: "Stock サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 16
layout: default
---

# Stock サービス テストケース

在庫管理、スナップショットスケジューラー、WebSocketアラートなどがカバーされています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| SK-U-01 | 在庫（Stock）の取得・更新・履歴の検証 | Basic | 🔴 高 | ✅ 実装済 |
| SK-U-02 | 発注アラート（条件、更新トリガー、最小在庫）の検証 | Alert | 🔴 高 | ✅ 実装済 |
| SK-U-03 | スナップショットスケジューラー（CRON設定、テナント更新）の検証 | Schedule | 🟠 高 | ✅ 実装済 |
| SK-U-04 | スナップショットデータの期間指定（Date Range）による取得検証 | Snapshot | 🟠 高 | ✅ 実装済 |
| SK-U-05 | マイナス在庫許可フラグの動作検証 | Edge | 🟡 中 | ✅ 実装済 |
| SK-U-06 | 複数店舗の在庫一覧取得検証 | Store | 🟡 中 | ✅ 実装済 |
| SK-U-07 | WebSocket接続とアラート（再発注・最小在庫）の受信検証 | WS | 🔴 高 | ✅ 実装済 |
| SK-U-08 | WebSocketマルチクライアントおよび未承認アクセス検証 | WS | 🟠 高 | ✅ 実装済 |
| SK-U-09 | 手動在庫調整時のバリデーション | CRUD | 🔴 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| SK-I-01 | Dapr Subscribe 経由の他サービスからの在庫引当要求の処理 | Integration | 🔴 高 | ✅ 実装済 |
| SK-I-02 | MongoDB への在庫更新アトミック操作検証 | Integration | 🔴 高 | ❌ 推奨 |
| SK-S-01 | 在庫更新 → 発注アラート起動 → WebSocket通知のE2Eフロー | Scenario | 🔴 高 | ❌ 推奨 |
