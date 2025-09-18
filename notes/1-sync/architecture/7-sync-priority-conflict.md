# Sync Service Architecture

## 7. Data Sync Priority and Conflict Resolution

このセクションでは、同期処理における優先度管理と競合解決のメカニズムを説明します。効率的なデータ同期を実現するため、データの重要度に応じた優先度付けと、競合発生時の解決戦略を実装しています。

### 同期優先度キュー（将来実装）

**注**: 優先度制御は将来の実装予定です。現在はFIFO（先入先出）方式で処理されます。

データの種類に応じた優先度管理の将来計画：

#### すべてのデータ（現在の実装）
- **処理方式**: FIFO（先入先出）
- **同期間隔**: 30秒〜1分（すべてのデータタイプで統一）
- **特別な優先度なし**

### キュープロセッサー（現在の実装）
- FIFOベースでキューから順次取り出し
- シンプルな順次処理
- 将来的に優先度ベースの処理に拡張予定

### 競合解決戦略

データ競合が発生した場合の解決方法：

#### Last Write Wins (LWW) - 現在の実装
**タイムスタンプベースの解決**
- 最も新しいタイムスタンプのデータを採用
- シンプルで高速な解決方法
- すべてのデータタイプに適用

**実装詳細：**
- 各レコードに`updated_at`タイムスタンプを付与
- 同期時にタイムスタンプを比較
- 新しいデータで上書き

### 競合検出メカニズム

**Conflict Detector**が以下を監視：
- 同一レコードへの同時更新
- バージョン番号の不整合
- ビジネスルール違反
- データ整合性の問題

現在はシンプルなFIFO処理とLast Write Winsによる競合解決を実装しており、将来的により高度な優先度管理と競合解決戦略への拡張を予定しています。

```mermaid
flowchart TD
    subgraph "Sync Queue (Current: FIFO)"
        FIFO[FIFO Queue - All Data Types]
        FIFO --> QP[Queue Processor]
    end
    
    subgraph "Future Priority Queue (Planned)"
        P1[Priority Levels - Future Implementation]
        P1 --> FQP[Future Queue Processor]
    end
    
    subgraph "Conflict Resolution"
        CR[Conflict Detector]
        CR --> LWW[Last Write Wins - Current]
        CR --> Future[Future Strategies - Planned]
        
        LWW --> R1[Timestamp Based]
        Future --> R2[Field Merge / Manual - Future]
    end
    
    QP --> CR
```