---
title: "テスト"
parent: 日本語
nav_order: 10
has_children: true
layout: default
---

# テスト

Kugelpos POS バックエンドシステムの全テスト関連ドキュメント。

## ドキュメント一覧

| ドキュメント | 説明 |
|-------------|------|
| [テスト評審](test-review.html) | 総合テスト評審 — 現状・メトリクス・改善提案 |
| [テスト戦略](test-strategy.html) | 全サービスのテスト戦略・方針 |
| [ユニットテストガイド](unit-test-guide.html) | ユニットテスト作成ガイドライン |
| [統合テストガイド](integration-test-guide.html) | Dapr・サービス間統合テストガイドライン |

## テストカバレッジ概要

| サービス | ユニットテスト | 統合テスト | シナリオテスト |
|---------|-------------|-----------|--------------|
| Account | ✅ | ⚠️ 一部 | ❌ |
| Terminal | ⚠️ 一部 | ❌ | ❌ |
| Master-data | ⚠️ 一部 | ❌ | ❌ |
| Cart | ✅ | ⚠️ 一部 | ⚠️ 一部 |
| Report | ✅ | ❌ | ❌ |
| Journal | ✅ | ❌ | ❌ |
| Stock | ✅ | ⚠️ 一部 | ❌ |
| Commons | ✅ | N/A | N/A |

## サービス別テストケース

| ドキュメント | 説明 |
|-------------|------|
| [Account](testcases-account.html) | Account サービス テストケース |
| [Terminal](testcases-terminal.html) | Terminal サービス テストケース |
| [Master Data](testcases-master-data.html) | Master Data サービス テストケース |
| [Cart](testcases-cart.html) | Cart サービス テストケース |
| [Report](testcases-report.html) | Report サービス テストケース |
| [Journal](testcases-journal.html) | Journal サービス テストケース |
| [Stock](testcases-stock.html) | Stock サービス テストケース |
