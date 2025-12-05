# Translation Proxy System (TPS) Frontend Specification

## 1. 概述 (Overview)
本文件定義 TPS 前端應用程式的架構與功能需求。前端將提供一個現代化、響應式的介面，供使用者查詢翻譯歷史、執行即時翻譯（文字/文件），並透過儀表板監控系統使用狀況。

### 1.1 技術堆疊 (Tech Stack)
*   **Framework**: SvelteKit (Svelte 5 - Runes syntax preferred)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS
*   **UI Library**: Shadcn-Svelte (or Bits UI + Tailwind)
*   **State Management**: Svelte Stores / Runes (內建狀態管理)
*   **Data Fetching**: TanStack Query (Svelte Query) 或 SvelteKit Load Functions
*   **Charts**: Chart.js 或 Recharts (via wrapper)

---

## 2. 頁面架構 (Sitemap)

| 路徑 | 名稱 | 說明 |
| :--- | :--- | :--- |
| `/` | **儀表板 (Dashboard)** | **[New]** 系統總覽、翻譯總量、各策略使用佔比圖表。 |
| `/history` | **翻譯歷史 (History)** | 檢視所有翻譯紀錄、搜尋、篩選、分頁。 |
| `/translate` | **即時翻譯 (Playground)** | 提供文字輸入與檔案上傳介面，執行翻譯任務。 |

---

## 3. 功能詳細設計 (Detailed Features)

### 3.1 儀表板 (Dashboard) - **[New]**
提供系統運作的宏觀視角，幫助管理者了解成本與策略效益。

*   **關鍵指標卡片 (KPI Cards)**:
    *   **Total Translations**: 總翻譯句數/請求數。
    *   **Total Characters**: 總翻譯字元數。
    *   **Estimated Cost**: 本月預估總花費 (USD)。
    *   **Cache Hit Rate**: 快取命中率 (顯示節省了多少 API Call)。
*   **圖表區 (Charts)**:
    *   **Usage by Provider (Pie Chart)**: 圓餅圖顯示各策略 (`Cache`, `DeepL`, `OpenAI`, `Google`) 的使用比例。
    *   **Daily Volume (Bar Chart)**: 過去 7 天/30 天的每日翻譯量趨勢。

### 3.2 翻譯歷史頁面 (Translation History)
用於稽核與檢索過去的翻譯內容。

*   **搜尋列 (Search Bar)**:
    *   支援全文檢索 (針對 `original_text` 與 `translated_text`)。
*   **篩選器 (Filters)**:
    *   **Provider (複選)**: `DeepL`, `Google`, `OpenAI`, `Cache`。
    *   **Language**: 來源/目標語言篩選。
    *   **Refinement**: 是否經過校稿。
*   **資料列表 (Data Table)**:
    *   **Columns**: 時間、語言對、原文(預覽)、譯文(預覽)、Provider (Badge)、校稿狀態。
    *   **Pagination**: 伺服器端分頁 (Server-side Pagination)。

### 3.3 即時翻譯頁面 (Translation Playground)
*   **控制列**: 語言選擇、AI 校稿開關 (`Enable Refinement`)。
*   **輸入區**: 支援純文字與檔案拖曳。
*   **輸出區**: 顯示結果與 Metadata (耗時、Provider、Cost)。

---

## 4. API 需求規格 (Backend Contract)

### 4.1 儀表板統計 (Dashboard Stats)
*   **Endpoint**: `GET /api/v1/stats/dashboard`
*   **Response**:
    ```json
    {
      "total_requests": 15000,
      "total_chars": 5000000,
      "total_cost_usd": 12.5,
      "cache_hit_rate": 0.45,
      "provider_usage": {
        "cache": 6750,
        "deepl": 5000,
        "openai": 3000,
        "google": 250
      },
      "daily_trend": [
        { "date": "2023-10-01", "count": 1200 },
        { "date": "2023-10-02", "count": 1500 }
      ]
    }
    ```

### 4.2 翻譯歷史查詢 (Pagination API)
*   **Endpoint**: `GET /api/v1/translations`
*   **Query Parameters**: `page`, `page_size`, `q`, `providers`, `source_lang`, `target_lang`.
*   **Response**:
    ```json
    {
      "items": [ ... ],
      "meta": { "total": 100, "page": 1, "page_size": 20 }
    }
    ```

### 4.3 執行翻譯 (Execute Translation)
*   **Endpoint**: `POST /api/v1/translate`

---

## 5. 專案結構建議 (SvelteKit Structure)

```
frontend/
├── src/
│   ├── lib/
│   │   ├── components/     # Shared Components (Button, Card, Table)
│   │   │   ├── ui/         # Shadcn-Svelte components
│   │   │   └── charts/     # Chart components
│   │   ├── stores/         # Global state (if needed)
│   │   ├── api/            # API client wrappers
│   │   └── types/          # TypeScript interfaces
│   ├── routes/
│   │   ├── +layout.svelte  # Main layout (Sidebar, Header)
│   │   ├── +page.svelte    # Dashboard (/)
│   │   ├── history/
│   │   │   └── +page.svelte # History Page
│   │   └── translate/
│   │       └── +page.svelte # Playground Page
│   └── app.html
├── package.json
├── svelte.config.js
└── tailwind.config.js
```

## 6. 開發階段規劃 (Frontend Roadmap)
1.  **初始化**: 建立 SvelteKit 專案，設定 Tailwind CSS 與 Shadcn-Svelte。
2.  **API Client**: 封裝 `fetch` 或 `axios`，處理錯誤與型別。
3.  **Dashboard**: 實作統計卡片與圖表 (需後端 `/stats` API)。
4.  **History**: 實作分頁表格與篩選器。
5.  **Playground**: 實作翻譯介面。
