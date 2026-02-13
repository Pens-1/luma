# Phase 1: The Scheduler 詳細設計書

## 概要

毎朝自動で Google カレンダーと Notion からデータを取得し、OR-Tools で最適なスケジュールを計算してカレンダーに登録、Discord に通知するシステム。

---

## データソース分離設計

### 基本方針

| 種類         | マスタ          | 作成・変更 | GCal での扱い            |
| ------------ | --------------- | ---------- | ------------------------ |
| **イベント** | Google Calendar | 手動       | 変更なし（読み取りのみ） |
| **タスク**   | Notion          | 手動       | LUMA が自動登録          |

### 責任分離

```
┌─────────────────┐                  ┌─────────────────┐
│     Notion      │                  │ Google Calendar │
│   (タスクDB)     │                  │   (イベント)     │
├─────────────────┤                  ├─────────────────┤
│ 「何をやるか」   │                  │ 「いつ・どこで」 │
│ 可変・調整可能  │                  │ 確定・変更不可   │
└────────┬────────┘                  └────────┬────────┘
         │ タスク                             │ イベント
         ▼                                   ▼
┌─────────────────────────────────────────────────────┐
│                  LUMA (FastAPI)                     │
│  • イベントを「避けるべき時間」として取得            │
│  • タスクを「配置する対象」として取得                │
│  • OR-Toolsで最適配置を計算                         │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Google Calendar [LUMA Tasks カレンダー]            │
│  • 最適化されたタスクを予定として登録                │
│  • 既存イベントには触らない                         │
└─────────────────────────────────────────────────────┘
```

---

## Notion タスク DB スキーマ

### データベース名

`📋 LUMA Tasks` （推奨）

### プロパティ定義

| プロパティ名      | 型         | 必須 | 説明                              | 例                     |
| ----------------- | ---------- | ---- | --------------------------------- | ---------------------- |
| **Name**          | タイトル   | ✅   | タスク名                          | "設計レビュー"         |
| **Priority**      | セレクト   | ❌   | 優先度（未設定時は「中」）        | 高 / 中 / 低           |
| **Duration**      | 数値       | ✅   | 所要時間（分）                    | 60                     |
| **Deadline**      | 日付       | ❌   | 期限（日時）                      | 2024-12-12 18:00       |
| **Category**      | セレクト   | ❌   | カテゴリ                          | 開発 / 学習 / 事務     |
| **Status**        | ステータス | ✅   | 進捗状態                          | 未着手 / 進行中 / 完了 |
| **Scheduled**     | 日付       | ❌   | 割り当て済み日時（LUMA 書き込み） | 2024-12-12 09:00-10:00 |
| **GCal Event ID** | テキスト   | ❌   | GCal 同期用 ID（LUMA 書き込み）   | "abc123xyz"            |
| **Notes**         | テキスト   | ❌   | 備考                              | "〇〇さんと一緒に"     |

### セレクト選択肢

#### Priority（優先度）

| 値  | 色    | 説明         | GCal 色 ID |
| --- | ----- | ------------ | ---------- |
| 高  | 🔴 赤 | 今日中に必須 | 11         |
| 中  | 🟡 黄 | 今週中に完了 | 5          |
| 低  | 🔵 青 | 余裕があれば | 9          |

#### Category（カテゴリ）

| 値       | 絵文字 | 説明             |
| -------- | ------ | ---------------- |
| 学習     | 📚     | 読書、勉強       |
| 開発     | 💼     | 業務開発         |
| 趣味開発 | 🎮     | 個人プロジェクト |
| 事務     | 📝     | 書類、メール対応 |

#### Status（ステータス）

| 値     | 説明               | LUMA での扱い |
| ------ | ------------------ | ------------- |
| 未着手 | まだ着手していない | ✅ 最適化対象 |
| 進行中 | 作業中             | ✅ 最適化対象 |
| 完了   | 完了済み           | ❌ 対象外     |

---

## Notion API データ取得

### クエリ条件（再割り当て対応）

未完了 かつ (未割当 または 過去に割当済み) のタスクを取得。

```json
{
  "filter": {
    "and": [
      {
        "property": "Status",
        "status": {
          "does_not_equal": "完了"
        }
      },
      {
        "or": [
          {
            "property": "Scheduled",
            "date": { "is_empty": true }
          },
          {
            "property": "Scheduled",
            "date": { "before": "{{$today}}" }
          }
        ]
      }
    ]
  },
  "sorts": [
    {
      "property": "Priority",
      "direction": "ascending"
    },
    {
      "property": "Deadline",
      "direction": "ascending"
    }
  ]
}
```

### 再割り当て時の処理

過去に割り当てられたタスクを再割り当てする場合、既存の GCal イベントを削除してから新規作成。

```javascript
// n8n Codeノード: 再割り当て時の既存イベント削除
for (const task of tasksToSchedule) {
  if (task.gcalEventId) {
    // 既存のGCalイベントを削除
    await $http.delete({
      url: `https://www.googleapis.com/calendar/v3/calendars/${calendarId}/events/${task.gcalEventId}`,
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  }
}
```

### レスポンス例

```json
{
  "results": [
    {
      "id": "page-id-123",
      "properties": {
        "Name": {
          "title": [{ "plain_text": "設計レビュー" }]
        },
        "Priority": {
          "select": { "name": "高" }
        },
        "Duration": {
          "number": 60
        },
        "Deadline": {
          "date": { "start": "2024-12-12T18:00:00" }
        },
        "Category": {
          "select": { "name": "開発" }
        },
        "Status": {
          "status": { "name": "未着手" }
        },
        "Scheduled": {
          "date": null
        },
        "GCal Event ID": {
          "rich_text": []
        }
      }
    }
  ]
}
```

### n8n での変換コード

```javascript
// Notion API レスポンスを FastAPI リクエスト形式に変換
const tasks = $input.all().map((item) => {
  const props = item.json.properties;

  const priorityMap = { 高: 1, 中: 2, 低: 3 };

  return {
    id: item.json.id,
    title: props.Name.title[0]?.plain_text ?? "",
    priority: priorityMap[props.Priority.select?.name] ?? 2,
    duration_minutes: props.Duration.number ?? 30,
    deadline: props.Deadline.date?.start ?? null,
    category: props.Category.select?.name ?? null,
  };
});

return tasks.map((t) => ({ json: t }));
```

---

## LUMA → Notion 書き戻し

最適化完了後、Notion タスクに結果を書き戻します。

### 更新対象プロパティ

| プロパティ    | 更新内容                      |
| ------------- | ----------------------------- |
| Scheduled     | 割り当てられた日時            |
| GCal Event ID | 作成された GCal イベントの ID |

### Notion API リクエスト

```json
{
  "properties": {
    "Scheduled": {
      "date": {
        "start": "2024-12-12T09:00:00",
        "end": "2024-12-12T10:00:00",
        "time_zone": "Asia/Tokyo"
      }
    },
    "GCal Event ID": {
      "rich_text": [
        {
          "text": { "content": "gcal-event-id-xyz" }
        }
      ]
    }
  }
}
```

---

## Google Calendar 連携

### 読み取り（イベント取得）

**対象カレンダー**: メインカレンダー + 指定カレンダー

**取得条件**:

- 今日の予定のみ
- 終日イベントは除外（オプション）

```javascript
// GCal Events List API パラメータ
{
  calendarId: "primary",
  timeMin: "2024-12-12T00:00:00+09:00",
  timeMax: "2024-12-12T23:59:59+09:00",
  singleEvents: true,
  orderBy: "startTime"
}
```

### 書き込み（タスク登録）

**対象カレンダー**: `LUMA Tasks`（専用カレンダー）

```javascript
// GCal Events Insert API リクエスト
{
  calendarId: "luma-tasks@group.calendar.google.com",
  resource: {
    summary: "🔧 設計レビュー",  // カテゴリ絵文字 + タスク名
    description: "LUMA自動スケジュール\n優先度: 高\nNotion: https://notion.so/page-id",
    start: {
      dateTime: "2024-12-12T09:00:00",
      timeZone: "Asia/Tokyo"
    },
    end: {
      dateTime: "2024-12-12T10:00:00",
      timeZone: "Asia/Tokyo"
    },
    colorId: "11",  // 赤（高優先度）
    extendedProperties: {
      private: {
        lumaTaskId: "notion-page-id-123",  // 紐付け用
        lumaGenerated: "true"
      }
    }
  }
}
```

### GCal 色マッピング（4 色でシンプルに）

| 種別         | colorId | 色       | 用途                      |
| ------------ | ------- | -------- | ------------------------- |
| タスク       | 9       | 🔵 青    | LUMA が配置するタスク全般 |
| 仕事         | 10      | 🟢 緑    | 仕事のイベント            |
| 大学         | 3       | 🟣 紫    | 授業、ゼミ                |
| プライベート | 4       | 🩷 ピンク | 遊び、個人の予定          |

> **ルール**: タスクは全て青、イベントは手動で 3 色から選ぶ

---

### 2. n8n ↔ Google Calendar 連携

#### GCal から取得するデータ（Events List API）

```typescript
// GCal APIレスポンスから抽出するフィールド
interface GCalEvent {
  id: string;
  summary: string; // タイトル
  start: {
    dateTime: string; // ISO 8601
  };
  end: {
    dateTime: string; // ISO 8601
  };
}

// n8nでの変換ロジック
const toFixedEvent = (gcalEvent: GCalEvent): FixedEvent => ({
  id: gcalEvent.id,
  title: gcalEvent.summary,
  start: gcalEvent.start.dateTime,
  end: gcalEvent.end.dateTime,
});
```

#### GCal へ登録するデータ（Events Insert API）

```typescript
// FastAPIの結果をGCalイベント形式に変換
interface GCalEventCreate {
  summary: string; // タスク名
  description: string; // "LUMA Auto-scheduled | Priority: 1"
  start: {
    dateTime: string;
    timeZone: "Asia/Tokyo";
  };
  end: {
    dateTime: string;
    timeZone: "Asia/Tokyo";
  };
  colorId?: string; // 優先度に応じた色
}

// 優先度→カラーID変換
const priorityColors = {
  1: "11", // 赤（高優先度）
  2: "5", // 黄（中優先度）
  3: "9", // 青（低優先度）
};
```

---

### 3. n8n ↔ Notion 連携

#### Notion から取得するデータ（Database Query API）

```typescript
// Notion DBのプロパティマッピング
interface NotionTaskPage {
  id: string; // ページID
  properties: {
    Name: {
      title: [{ plain_text: string }];
    };
    Priority: {
      select: {
        name: "高" | "中" | "低";
      };
    };
    "Duration (min)": {
      number: number;
    };
    Deadline: {
      date: {
        start: string; // ISO 8601
      } | null;
    };
    Status: {
      status: {
        name: "未着手" | "進行中" | "完了";
      };
    };
  };
}

// Notion→Task変換ロジック
const toTask = (page: NotionTaskPage): Task => ({
  id: page.id,
  title: page.properties.Name.title[0]?.plain_text ?? "",
  priority:
    {
      高: 1,
      中: 2,
      低: 3,
    }[page.properties.Priority.select.name] ?? 2,
  duration_minutes: page.properties["Duration (min)"].number ?? 30,
  deadline: page.properties.Deadline.date?.start,
});
```

#### Notion フィルター条件

```json
{
  "filter": {
    "and": [
      {
        "property": "Status",
        "status": {
          "does_not_equal": "完了"
        }
      },
      {
        "or": [
          {
            "property": "Deadline",
            "date": {
              "on_or_before": "{{$today}}"
            }
          },
          {
            "property": "Deadline",
            "date": {
              "is_empty": true
            }
          }
        ]
      }
    ]
  },
  "sorts": [
    {
      "property": "Priority",
      "direction": "ascending"
    }
  ]
}
```

---

### 4. n8n ↔ Discord 連携

#### Discord Webhook ペイロード

```typescript
interface DiscordWebhookPayload {
  content?: string;
  embeds: DiscordEmbed[];
}

interface DiscordEmbed {
  title: string;
  description: string;
  color: number; // 10進数のカラーコード
  fields: {
    name: string;
    value: string;
    inline?: boolean;
  }[];
  footer?: {
    text: string;
  };
  timestamp?: string; // ISO 8601
}

// 朝ブリーフィングの例
const morningBriefing: DiscordWebhookPayload = {
  embeds: [
    {
      title: "📋 今日の戦略",
      description: "LUMA Schedulerが最適なスケジュールを作成しました",
      color: 0x00ff00, // 緑
      fields: [
        {
          name: "📊 タスク数",
          value: "5件",
          inline: true,
        },
        {
          name: "⏱️ 総作業時間",
          value: "4時間30分",
          inline: true,
        },
        {
          name: "🎯 本日のスケジュール",
          value: `
09:00-10:00 設計レビュー ⭐ 高優先度
11:00-11:30 コードレビュー
11:30-12:15 ドキュメント作成
14:00-15:00 実装作業
16:00-17:00 テスト
        `.trim(),
        },
      ],
      footer: {
        text: "LUMA Scheduler v0.1.0",
      },
      timestamp: new Date().toISOString(),
    },
  ],
};
```

---

## n8n ワークフロー実装詳細

### ノード構成

```
┌─────────────────┐
│ Schedule Trigger │  毎朝 7:00 JST
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Set Variables   │  TODAY = $now.format('YYYY-MM-DD')
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌───────┐
│ GCal  │  │Notion │   並列実行
│ Get   │  │ Query │
└───┬───┘  └───┬───┘
    │          │
    └────┬─────┘
         ▼
┌─────────────────┐
│     Merge       │  両方のデータを結合
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Code: Transform │  GCal/Notionのデータをリクエスト形式に変換
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │  POST fastapi:8000/api/v1/optimize/schedule
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ IF: status ==   │
│   "success"     │
└────────┬────────┘
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌───────┐
│ GCal  │  │Discord│
│ Create│  │Notify │
│ Loop  │  │Error  │
└───┬───┘  └───────┘
    │
    ▼
┌─────────────────┐
│ Discord: Brief  │  朝ブリーフィング送信
└─────────────────┘
```

---

## 環境変数

### n8n 用（Credentials）

| 変数名                    | 説明                     | 設定場所           |
| ------------------------- | ------------------------ | ------------------ |
| `GOOGLE_CLIENT_ID`        | GCal OAuth Client ID     | n8n Credentials    |
| `GOOGLE_CLIENT_SECRET`    | GCal OAuth Secret        | n8n Credentials    |
| `NOTION_API_KEY`          | Notion Integration Token | n8n Credentials    |
| `NOTION_TASK_DATABASE_ID` | タスク DB の ID          | Workflow Variables |
| `DISCORD_WEBHOOK_URL`     | Discord Webhook URL      | n8n Credentials    |

### FastAPI 用

| 変数名             | 説明                | デフォルト |
| ------------------ | ------------------- | ---------- |
| `DATABASE_URL`     | PostgreSQL 接続 URL | -          |
| `PYTHONUNBUFFERED` | ログ出力設定        | 1          |

---

## API エンドポイント

### POST /api/v1/optimize/schedule

| 項目         | 値                                             |
| ------------ | ---------------------------------------------- |
| URL          | `http://fastapi:8000/api/v1/optimize/schedule` |
| Method       | POST                                           |
| Content-Type | application/json                               |
| 認証         | なし（内部ネットワーク）                       |

#### サンプルリクエスト

```bash
curl -X POST http://localhost:8001/api/v1/optimize/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {"id": "1", "title": "設計レビュー", "priority": 1, "duration_minutes": 60},
      {"id": "2", "title": "コードレビュー", "priority": 2, "duration_minutes": 30}
    ],
    "fixed_events": [
      {"id": "e1", "title": "定例MTG", "start": "2024-12-12T10:00:00", "end": "2024-12-12T11:00:00"}
    ],
    "work_start": "09:00",
    "work_end": "18:00"
  }'
```

#### サンプルレスポンス

```json
{
  "status": "success",
  "schedule": [
    {
      "task_id": "1",
      "title": "設計レビュー",
      "start": "2024-12-12T09:00:00",
      "end": "2024-12-12T10:00:00",
      "priority": 1
    },
    {
      "task_id": "2",
      "title": "コードレビュー",
      "start": "2024-12-12T11:00:00",
      "end": "2024-12-12T11:30:00",
      "priority": 2
    }
  ],
  "unscheduled": [],
  "summary": "2件のタスクを配置しました（総作業時間: 90分）",
  "total_work_minutes": 90
}
```

---

## ファイル構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリ
│   ├── models/
│   │   ├── __init__.py
│   │   └── schedule.py            # Pydanticモデル
│   └── services/
│       ├── __init__.py
│       └── scheduler.py           # OR-Tools最適化ロジック
├── tests/
│   ├── __init__.py
│   ├── test_api.py                # APIテスト
│   └── test_scheduler.py          # ユニットテスト
├── Dockerfile
└── requirements.txt
```
