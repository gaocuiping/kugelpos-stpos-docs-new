---
title: "Account サービス Testingケース"
parent: Testing
grand_parent: English
nav_order: 11
layout: default
---

# Account サービス Testing設計書

本ドキュメントは、Account サービスのTesting網羅性と品質担保のための詳細なTesting設計書です。

## 1. サービスの概要とTesting戦略

**Account サービス**は、システムの入り口となる「認証・認可」と「テナント設定」を管理する最重要コンポーネントです。
セキュリティに関わるため、正常系だけでなく**異常系（パスワード間違い、トークン期限切れ、不正アクセス）**のTestingカバレッジを 100% に近づける必要があります。

### 1.1 前提条件・Testingデータ
- **依存サービス**: MongoDB, Dapr StateStore (Redis)
- **Testing用テナント**: `tenant-test-01`
- **モック設定**: DBアクセスは `AsyncMock` 等でモック化し、外部依存を排除した高速なTestingを実現すること。

---

## 2. ユニットTesting (API・ロジック単位)

機能ドメインやAPIエンドポイントごとの詳細なTestingケースです。

### 2.1 認証プロセス (Authentication)

| ID | ターゲットAPI | Testingシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **AC-U-001** | `POST /login` | 登録済みの正しいID・パスワードでログインする | `200 OK`、有効な JWT トークン (access/refresh) が返却されること | ✅ Implemented |
| **AC-U-002** | `POST /login` | 登録されていないユーザーIDでログインを試みる | `401 Unauthorized` が返却されること | ❌ Recommended |
| **AC-U-003** | `POST /login` | 正しいIDだが、誤ったパスワードでログインを試みる | `401 Unauthorized` が返却されること | ❌ Recommended |
| **AC-U-004** | `POST /login` | パスワードが空、またはリクエスト形式が不正な場合 | `422 Validation Error` が返却されること | ❌ Recommended |
| **AC-U-005** | `POST /refresh` | 有効なリフレッシュトークンで新しいトークンを要求する | `200 OK`、新しいアクセストークンが返却されること | ❌ Recommended |
| **AC-U-006** | `POST /refresh` | 期限切れ、または無効なリフレッシュトークンを使用する | `401 Unauthorized` が返却されること | ❌ Recommended |

### 2.2 マルチテナント検証 (Tenant Context)

| ID | ターゲットAPI | Testingシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **AC-U-010** | Any (Auth API) | `Tenant-ID` ヘッダーを付けてリクエストする | リクエストが正常に処理され、指定テナント用のDBコンテキストにアクセスすること | ❌ Recommended |
| **AC-U-011** | Any (Auth API) | `Tenant-ID` ヘッダー**なし**でリクエストする | `400 Bad Request` (テナントID必須) が返却されること | ❌ Recommended |

### 2.3 ユーザー管理 (User Management)

| ID | ターゲットAPI | Testingシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **AC-U-020** | `GET /me` | 有効な Bearer トークンを指定してプロフィール取得 | `200 OK`、パスワードを含まないユーザー情報が返却されること | ❌ Recommended |
| **AC-U-021** | `POST /users` | 新規管理ユーザー（ユニークなID）の作成 | `201 Created`、DBにパスワードがハッシュ化されて保存されること | ❌ Recommended |
| **AC-U-022** | `POST /users` | 既に存在するユーザーIDで作成を試みる | `409 Conflict` が返却されること | ❌ Recommended |

---

## 3. インテグレーションTesting (統合検証)

| ID | コンポーネント | Testingシナリオ | 確認ポイント | 状態 |
|----|--------------|--------------|------------|------|
| **AC-I-001** | MongoDB | JWT ペイロードのユーザーIDから MongoDB への実クエリ（Read/Write） | TestingDBに実データが保存され、正しく取得できること | 🟠 一部 |
| **AC-I-002** | JWT Engine | サードパーティライブラリとの連携（PyJWT） | トークンの署名、検証、期限チェックが設計通りに動作すること | ❌ Recommended |

---

## 4. エンドツーエンド (E2E) シナリオTesting

| ID | シナリオフロー | 期待される結果とアサーション | 状態 |
|----|--------------|--------------------------|------|
| **AC-S-001** | **正常ログインフロー** <br>1. `/login` で認証<br>2. 取得したトークンで `/me` アクセス<br>3. トークンの有効性を確認 | 全て200系で成功し、トークンデコード結果とDBデータが一致すること | ❌ Recommended |
| **AC-S-002** | **タイムアウトフロー** <br>1. ログイン後、Token期限の15分を待機（※時刻操作モック）<br>2. `/me` アクセス (結果: 401)<br>3. `/refresh` 実行 | アクセストークンの期限切れが検知され、リフレッシュ処理が機能すること | ❌ Recommended |

---

## 5. エラーハンドリング・セキュリティマトリクス

| エラー種別 | トリガー条件 | 期待される HTTP ステータス | 期待される内部処理 |
|-----------|------------|------------------------|-------------------|
| パスワード漏洩耐性 | プレーンテキストでの保存試行 | `500` / `400` | BCrypt 非適用での保存はアプリケーション側でブロックされること |
| XSS / Injection | IDや名前フィールドに `<script>` 等を含む | `422` / サニタイズ | Pydantic によるサニタイズ、または拒否 |
| 不正署名トークン | `alg` ヘッダーを変更、または署名偽装 | `401 Unauthorized` | Signature Verification Failed がログに記録される |

## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **AC-E-001** | `Security` | 50 `POST /login` requests in 1 second from same IP (Brute-force) | Rate limiter triggers, returning `429 Too Many Requests` | ❌ Recommended |
| **AC-E-002** | `Security` | Requesting with a valid JWT immediately after logout | Token is blacklisted/revoked, rejected with `401` (Anti-replay) | ❌ Recommended |
