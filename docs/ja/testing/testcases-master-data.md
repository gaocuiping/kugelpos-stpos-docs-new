---
title: "Master Data サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 13
layout: default
---

# Master Data サービス テストケース

現在のテストコードから抽出したテストケースと、不足している推奨シナリオのリストです。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| MD-U-01 | ヘルスチェックAPIとレスポンス時間の検証 | Health | 🟡 中 | ✅ 実装済 |
| MD-U-02 | 基本的なオペレーションの動作検証 | Basic | 🟡 中 | ✅ 実装済 |
| MD-U-03 | 商品（Item）マスターの取得（全件・個別） | Item | 🔴 高 | ❌ 推奨 |
| MD-U-04 | カテゴリマスターの取得と階層構造の検証 | Category | 🟠 高 | ❌ 推奨 |
| MD-U-05 | 税率（Tax）マスターの取得検証 | Tax | 🔴 高 | ❌ 推奨 |
| MD-U-06 | 支払方法（Payment）マスターの取得検証 | Payment | 🟠 高 | ❌ 推奨 |
| MD-U-07 | Dapr Statestore (Redis) からのマスターキャッシュ取得 | Cache | 🔴 高 | ❌ 推奨 |
| MD-U-08 | 存在しないマスターデータ要求時の 404 エラー処理 | Error | 🟡 中 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| MD-I-01 | マスターデータ更新時の Dapr pub/sub 経由でのキャッシュ破棄通知 | Integration | 🔴 高 | ❌ 推奨 |
| MD-I-02 | MongoDBからの商品データ読み込みとRedisへのキャッシュ保存処理 | Integration | 🔴 高 | ❌ 推奨 |
| MD-S-01 | カートサービスなどの他サービスから、gRPC経由での商品情報取得フロー | Scenario | 🟠 高 | ❌ 推奨 |
