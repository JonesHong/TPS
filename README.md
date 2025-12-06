# Translation Proxy System (TPS)

TPS 是一個高可用、低成本的翻譯中介系統，結合了現代化的 Web 前端介面與強大的後端 API。它整合了 SQLite 本地快取、NMT (DeepL/Google) 與 LLM (OpenAI)，透過智慧路由策略來優化翻譯品質與成本。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![SvelteKit](https://img.shields.io/badge/sveltekit-2.0+-orange.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.109+-green.svg)

## ✨ 主要功能

### 核心系統 (Backend)
- 🚀 **多層次翻譯策略**: 優先順序 Cache → DeepL → OpenAI → Google，確保最佳性價比。
- 💾 **智慧快取**: 使用 SQLite (WAL 模式) 進行本地快取，大幅減少重複 API 呼叫與費用。
- 🤖 **AI 校稿 (Refinement)**: 支援使用 LLM (如 GPT-4o-mini) 對翻譯結果進行潤飾，提升流暢度。
- 💰 **成本控制**: 內建每日預算熔斷機制，防止 API 費用超支。
- 🔄 **高可用性**: 自動 Failover 機制，當某個服務商當機時自動切換至下一個。
- 📂 **檔案翻譯**: 支援批次檔案上傳與翻譯 (透過 API 或 UI)。

### 使用者介面 (Frontend)
- 🖥️ **現代化 Dashboard**: 基於 SvelteKit + Tailwind CSS 打造的響應式介面。
- 📊 **即時統計**: 視覺化顯示 API 使用量、成本估算 (USD/TWD) 與快取命中率。
- 🌍 **多語言支援**: 介面支援繁體中文與英文切換。
- 📝 **即時翻譯**: 類似 Google Translate 的文字輸入與即時預覽。
- 📁 **拖放式檔案翻譯**: 支援拖放上傳檔案進行批次翻譯，並顯示進度條。

## 🏗️ 翻譯優先級架構

| Tier | Provider | 成本 | 說明 |
|------|----------|------|------|
| 1 | **Local Cache** | $0 | 優先查找本地資料庫，完全免費且速度最快 |
| 2 | **DeepL** | 低 | 利用每月免費額度 (500K 字元)，品質優異 |
| 3 | **OpenAI (gpt-4o-mini)** | 極低 | $0.15/1M tokens，比 Google 便宜 90% 以上 |
| 4 | **Google Translate** | 中 | 每月 500K 免費額度，超額後 $20/1M chars |

## 🛠️ 安裝與設定

### 前置需求
- **Python**: 3.12+
- **Node.js**: 18+
- **套件管理器**: `uv` (Python), `pnpm` (Node.js)

### 1. 複製專案與設定環境變數

```bash
git clone <repository-url>
cd TPS

# 設定後端環境變數
cp .env.example .env
```

編輯 `.env` 檔案，填入您的 API Keys：

```env
DEEPL_API_KEY=your_deepl_key
OPENAI_API_KEY=your_openai_key
# GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json (選填)
DAILY_BUDGET_OPENAI=5.0
DAILY_BUDGET_GOOGLE=10.0
```

### 2. 安裝依賴

**後端 (Python):**
```bash
# 安裝 uv (如果尚未安裝)
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Unix: curl -LsSf https://astral.sh/uv/install.sh | sh

uv sync
```

**前端 (SvelteKit):**
```bash
cd frontend
pnpm install
cd ..
```

## 🚀 快速啟動

我們提供了方便的腳本，可以一鍵同時啟動後端 API 與前端開發伺服器。

### Windows
直接雙擊 `scripts/dev.bat`，或在 PowerShell 執行：
```powershell
.\scripts\dev.ps1
```

### macOS / Linux
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

啟動後：
- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📖 API 使用範例

詳細 API 規格請參考 [API_Documentation.md](./API_Documentation.md)。

### 文字翻譯
```bash
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
           "text": "Hello world",
           "source_lang": "en",
           "target_lang": "zh-TW",
           "enable_refinement": true
         }'
```

### 檔案翻譯
```bash
curl -X POST "http://localhost:8000/translate/file" \
     -F "file=@document.txt" \
     -F "target_lang=zh-TW"
```

## 📂 專案結構

```
TPS/
├── src/tps/              # Backend Source Code
│   ├── api/              # API Routes (FastAPI)
│   ├── clients/          # Translation Providers (DeepL, OpenAI, Google)
│   ├── core/             # Core Logic (Cache, Failover)
│   └── db/               # Database Models & Connection
├── frontend/             # Frontend Source Code (SvelteKit)
│   ├── src/routes/       # Pages & Routing
│   └── src/lib/          # Components & Utilities
├── scripts/              # Startup Scripts (dev.bat, dev.sh)
├── tests/                # Python Tests
├── docs/                 # Documentation
├── pyproject.toml        # Python Dependencies (uv)
└── README.md             # This file
```

## 📝 支援語言

系統專注於東亞、東南亞及主要旅遊國家語言支援：

- **核心**: 繁體中文 (zh-TW), 簡體中文 (zh-CN), 英文 (en), 日文 (ja), 韓文 (ko)
- **東南亞**: 馬來文 (ms), 越南文 (vi), 泰文 (th), 印尼文 (id), 菲律賓文 (tl)
- **歐美/其他**: 法文 (fr), 德文 (de), 西班牙文 (es), 義大利文 (it), 俄文 (ru), 葡萄牙文 (pt), 阿拉伯文 (ar), 印地文 (hi)

## 📄 License

MIT License
