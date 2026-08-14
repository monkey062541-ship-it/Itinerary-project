# 行程 LINE Bot

用 LINE 查詢自己的行程。傳「今天行程」就回覆當天有哪些安排。

## 支援指令

| 輸入 | 回覆 |
|---|---|
| `今天行程` | 今天的所有安排 |
| `明天行程` / `後天行程` | 隔天 / 兩天後 |
| `本週行程` / `下週行程` | 該週（週一～週日） |
| `最近行程` | 未來七天 |
| `全部行程` | 所有已登錄的行程 |
| `8/20`、`8月20日`、`2026-08-20` | 指定日期 |
| `說明` | 指令一覽 |

語助詞會自動忽略，所以「今天有什麼行程？」一樣看得懂。

## 怎麼改行程

編輯 `data/events.json`，push 到 GitHub 後 Render 會自動重新部署。

```json
{
  "date": "2026-08-20",
  "start": "08:00",
  "end": "21:00",
  "title": "台中出差",
  "location": "台中",
  "note": "高鐵 0812 班次"
}
```

`start` 留空 = 全天行程。`end`、`location`、`note` 都可以留空。

## 本機開發

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt
cp .env.example .env   # 填入 LINE 憑證
.venv/Scripts/python run.py
```

測試：`.venv/Scripts/pytest`

## 部署（Render）

| 設定 | 值 |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Python 版本 | 由 `.python-version` 指定為 3.12.8 |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| 環境變數 | `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET` |

LINE Webhook URL 填 `https://<你的服務>.onrender.com/callback`

## 檔案結構

```
app/schedule.py   行程資料層（讀 data/events.json，之後可換成 Google Calendar）
app/handlers.py   訊息理解與回覆組裝（純函式，不依賴 LINE SDK）
app/main.py       FastAPI webhook，含 LINE 簽章驗證
app/config.py     環境變數讀取與啟動檢查
```
