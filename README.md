# Translation Proxy System (TPS)

高可用、低成本的翻譯中介層 API。整合 SQLite 本地快取、NMT (DeepL/Google) 與 LLM (OpenAI)，實現多層次翻譯策略。

## 功能特點

- 🚀 **多層次翻譯策略**: Cache → DeepL → OpenAI → Google
- 💾 **智慧快取**: SQLite WAL 模式本地快取，大幅減少 API 呼叫
- 🤖 **AI 校稿**: 可選的 LLM 翻譯品質提升 (Refinement)
- 💰 **成本控制**: 每日預算熔斷機制，避免超支
- 🔄 **高可用性**: 自動 Failover 機制，確保服務不中斷

## 翻譯優先級

| Tier | Provider | 成本 | 說明 |
|------|----------|------|------|
| 1 | Local Cache | $0 | 優先查找本地快取 |
| 2 | DeepL | 低 | 利用每月免費額度 500K 字元 |
| 3 | OpenAI (gpt-4o-mini) | 極低 | $0.15/1M tokens，比 Google 便宜 90% |
| 4 | Google Translate | 高 | 最後防線，$20/1M chars |

## 快速開始

### 1. 安裝依賴

```bash
# 安裝 uv (如果尚未安裝)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安裝專案依賴
uv sync
```

### 2. 設定環境變數

```bash
# 複製範例設定檔
cp .env.example .env

# 編輯 .env 填入你的 API Keys
```

需要設定的環境變數：

```env
DEEPL_API_KEY=your_deepl_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-credentials.json
DAILY_BUDGET_GOOGLE=10.0
DAILY_BUDGET_OPENAI=5.0
```

### 3. 啟動服務

```bash
# 使用 uv 執行
uv run tps

# 或直接執行
uv run python -m tps.app
```

服務將在 `http://localhost:8000` 啟動。

### 4. 測試 API

```bash
# 基本翻譯
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, world!", "source_lang": "en", "target_lang": "zh-tw"}'

# 帶 AI 校稿的翻譯
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, world!", "source_lang": "en", "target_lang": "zh-tw", "enable_refinement": true}'

# 健康檢查
curl http://localhost:8000/health

# 查看使用統計
curl http://localhost:8000/stats
```

## API 文檔

啟動服務後，訪問 `http://localhost:8000/docs` 查看 Swagger UI 互動式文檔。

### POST /translate

翻譯文字。

**Request Body:**
```json
{
  "text": "要翻譯的文字",
  "source_lang": "en",
  "target_lang": "zh-tw",
  "format": "plain",
  "enable_refinement": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "text": "翻譯結果",
    "provider": "deepl",
    "is_refined": false,
    "is_cached": false
  },
  "error": null
}
```

## 開發

### 執行測試

```bash
# 安裝開發依賴
uv sync --group dev

# 執行測試
uv run pytest

# 帶詳細輸出
uv run pytest -v
```

### 維護腳本

```bash
# 清理 90 天前的快取（預設）
uv run python scripts/cleanup_cache.py

# 清理 30 天前的快取
uv run python scripts/cleanup_cache.py --days 30

# 預覽要清理的項目（不實際刪除）
uv run python scripts/cleanup_cache.py --dry-run

# 執行資料庫 VACUUM
uv run python scripts/vacuum_db.py
```

### 排程建議

```bash
# Cron 範例：每週日 3:00 AM 清理快取
0 3 * * 0 cd /path/to/tps && uv run python scripts/cleanup_cache.py

# 每月 1 日 4:00 AM 執行 VACUUM
0 4 1 * * cd /path/to/tps && uv run python scripts/vacuum_db.py
```

## 專案結構

```
TPS/
├── src/tps/
│   ├── api/          # REST API 路由
│   ├── clients/      # 翻譯 API 客戶端
│   │   ├── deepl_client.py
│   │   ├── openai_client.py
│   │   └── google_client.py
│   ├── core/         # 核心業務邏輯
│   │   ├── workflow.py      # 主流程
│   │   ├── cost_control.py  # 成本控制
│   │   └── key_generator.py # 快取 Key 生成
│   ├── db/           # 資料庫層
│   │   ├── connection.py    # 連線管理
│   │   └── dao.py           # 資料存取
│   ├── app.py        # FastAPI 應用
│   └── config.py     # 設定管理
├── scripts/          # 維護腳本
├── tests/            # 測試
└── pyproject.toml    # 專案設定
```

## 授權

MIT License
