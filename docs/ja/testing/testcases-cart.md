---
title: "Cart サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 14
layout: default
---

# Cart サービス テストケース

ビジネスロジックが豊富で、多くのテストが既に実装されています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| CT-U-01 | ヘルスチェックAPIの正常動作 | Health | 🟡 中 | ✅ 実装済 |
| CT-U-02 | アイテム登録（Item Entry）の再開・レジューム機能 | Main | 🔴 高 | ✅ 実装済 |
| CT-U-03 | キャッシュレス決済時のエラーハンドリング | Payment | 🔴 高 | ✅ 実装済 |
| CT-U-04 | 小計（Subtotal）ロジックの計算精度検証 | Calc | 🔴 高 | ✅ 実装済 |
| CT-U-05 | ターミナルキャッシュの取得と更新 | Cache | 🟡 中 | ✅ 実装済 |
| CT-U-06 | トランザクション状態（Tran Service Status）検証 | Status | 🟠 高 | ✅ 実装済 |
| CT-U-07 | 既に取り消し済みの取引に対する再取消（二重Void）の防止 | Void | 🔴 高 | ✅ 実装済 |
| CT-U-08 | 既に返品済みの取引に対する再返品（二重Return）の防止 | Return | 🔴 高 | ✅ 実装済 |
| CT-U-09 | 二重Void/Return防止に伴うリスト状態と単一取得時の整合性 | Void/Return | 🔴 高 | ✅ 実装済 |
| CT-U-10 | Dapr Statestore セッション作成、再利用、タイムアウト処理 | Session | 🟠 高 | ✅ 実装済 |
| CT-U-11 | gRPC チャンネル（モジュールレベルスタブ）の生成・再利用 | gRPC | 🟠 高 | ✅ 実装済 |
| CT-U-12 | 単一商品の税計算、複数商品の税計算（内税・外税混在） | Tax | 🔴 高 | ❌ 推奨 |
| CT-U-13 | 割引計算（単品割引、カート全体割引） | Discount | 🟠 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| CT-I-01 | Cart から Master-data への gRPC 直接通信による商品情報取得 | Integration | 🔴 高 | ✅ 実装済 |
| CT-I-02 | 購入完了時の Stock サービスへの在庫引当 (Pub/Sub) | Integration | 🔴 高 | ❌ 推奨 |
| CT-I-03 | Transaction完了時の Journal サービスへの履歴保存 (Pub/Sub) | Integration | 🔴 高 | ❌ 推奨 |
| CT-S-01 | item-book シナリオ（商品スキャン → 数量変更 → 割引 → 支払） | Scenario | 🔴 高 | ❌ 推奨 |
