# TPS Frontend Implementation Todo List

Based on `FrontendSpecification.md`.

---

## Phase 1: Project Initialization & Setup

### 1.1 SvelteKit 專案建立
- [ ] 執行 `npm create svelte@latest frontend` 建立 SvelteKit 專案
- [ ] 選擇 TypeScript 模板
- [ ] 進入 `frontend/` 資料夾

### 1.2 Tailwind CSS 設定
- [ ] 安裝 Tailwind CSS: `npm install -D tailwindcss postcss autoprefixer`
- [ ] 執行 `npx tailwindcss init -p` 產生設定檔
- [ ] 設定 `tailwind.config.js` 的 `content` 路徑
- [ ] 建立 `src/app.css` 並加入 Tailwind directives
- [ ] 在 `+layout.svelte` 中 import `app.css`

### 1.3 UI Library 設定 (Shadcn-Svelte)
- [ ] 安裝 shadcn-svelte CLI: `npx shadcn-svelte@latest init`
- [ ] 設定 `components.json` (路徑、別名)
- [ ] 安裝常用元件:
    - [ ] Button: `npx shadcn-svelte@latest add button`
    - [ ] Card: `npx shadcn-svelte@latest add card`
    - [ ] Input: `npx shadcn-svelte@latest add input`
    - [ ] Select: `npx shadcn-svelte@latest add select`
    - [ ] Table: `npx shadcn-svelte@latest add table`
    - [ ] Badge: `npx shadcn-svelte@latest add badge`
    - [ ] Tabs: `npx shadcn-svelte@latest add tabs`
    - [ ] Switch: `npx shadcn-svelte@latest add switch`

### 1.4 圖表套件設定
- [ ] 安裝 Chart.js: `npm install chart.js svelte-chartjs`
- [ ] 或使用 Layerchart (Svelte-native): `npm install layerchart`

### 1.5 開發工具設定
- [ ] 設定 ESLint & Prettier
- [ ] 設定路徑別名 (`$lib`, `$components`)

---

## Phase 2: Layout & Navigation

### 2.1 共用 Layout
- [ ] 建立 `src/routes/+layout.svelte`
- [ ] 實作 Sidebar 導航:
    - [ ] Dashboard 連結 (`/`)
    - [ ] History 連結 (`/history`)
    - [ ] Translate 連結 (`/translate`)
- [ ] 實作 Header (顯示標題、可選: 使用者資訊)
- [ ] 設定響應式設計 (Mobile: Hamburger Menu)

### 2.2 Theme 設定
- [ ] 設定主色調 (建議: 藍/綠色系)
- [ ] (Optional) 實作 Dark Mode 切換

---

## Phase 3: API Client Layer

### 3.1 API Client 封裝
- [ ] 建立 `src/lib/api/client.ts`
    - [ ] 設定 Base URL (從環境變數讀取)
    - [ ] 封裝 `fetch` 或使用 `ky`/`axios`
    - [ ] 統一錯誤處理

### 3.2 API Types 定義
- [ ] 建立 `src/lib/types/api.ts`
    - [ ] `TranslationItem` interface
    - [ ] `PaginationMeta` interface
    - [ ] `DashboardStats` interface
    - [ ] `TranslateRequest` / `TranslateResponse` interface

### 3.3 API Functions
- [ ] 建立 `src/lib/api/translations.ts`
    - [ ] `getTranslations(params)` - 分頁查詢
    - [ ] `translate(request)` - 執行翻譯
- [ ] 建立 `src/lib/api/stats.ts`
    - [ ] `getDashboardStats()` - 取得儀表板數據

---

## Phase 4: Dashboard Page (/)

### 4.1 頁面結構
- [ ] 建立 `src/routes/+page.svelte` (Dashboard)
- [ ] 建立 `src/routes/+page.server.ts` (Load Function - Optional)

### 4.2 KPI Cards 實作
- [ ] 建立 `src/lib/components/dashboard/KpiCard.svelte`
- [ ] 實作四個指標卡片:
    - [ ] Total Translations (總句數)
    - [ ] Total Characters (總字元數)
    - [ ] Estimated Cost (預估花費)
    - [ ] Cache Hit Rate (快取命中率)

### 4.3 圖表實作
- [ ] 建立 `src/lib/components/charts/ProviderPieChart.svelte`
    - [ ] 顯示各 Provider 使用比例 (Cache, DeepL, OpenAI, Google)
- [ ] 建立 `src/lib/components/charts/DailyVolumeChart.svelte`
    - [ ] 顯示過去 7/30 天每日翻譯量 (Bar Chart)

### 4.4 資料串接
- [ ] 呼叫 `GET /api/v1/stats/dashboard`
- [ ] 處理 Loading 狀態
- [ ] 處理 Error 狀態

---

## Phase 5: History Page (/history)

### 5.1 頁面結構
- [ ] 建立 `src/routes/history/+page.svelte`

### 5.2 搜尋列
- [ ] 建立 Search Input 元件
- [ ] 實作 Debounce 機制 (500ms)

### 5.3 篩選器
- [ ] 建立 `src/lib/components/history/FilterBar.svelte`
- [ ] Provider 複選 (Checkbox Group / Toggle Buttons)
    - [ ] DeepL, Google, OpenAI, Cache
- [ ] Source Language 下拉選單
- [ ] Target Language 下拉選單
- [ ] Refinement 開關 (是否校稿)

### 5.4 資料表格
- [ ] 建立 `src/lib/components/history/TranslationTable.svelte`
- [ ] 欄位實作:
    - [ ] Time (格式化: YYYY-MM-DD HH:mm)
    - [ ] Source Lang (Badge)
    - [ ] Target Lang (Badge)
    - [ ] Original Text (預覽 + 展開)
    - [ ] Translated Text (預覽 + 展開)
    - [ ] Provider (彩色 Badge)
    - [ ] Refined (Icon)

### 5.5 分頁元件
- [ ] 建立 `src/lib/components/common/Pagination.svelte`
- [ ] 顯示「第 X 頁 / 共 Y 頁」
- [ ] 每頁筆數選擇 (10, 20, 50, 100)
- [ ] 上一頁 / 下一頁按鈕

### 5.6 資料串接
- [ ] 呼叫 `GET /api/v1/translations` 並帶入查詢參數
- [ ] URL Query Params 同步 (方便分享連結)

---

## Phase 6: Translate Page (/translate)

### 6.1 頁面結構
- [ ] 建立 `src/routes/translate/+page.svelte`

### 6.2 控制列
- [ ] Source Language 選擇器 (含 "Auto Detect")
- [ ] Target Language 選擇器
- [ ] AI Refinement 開關 (Switch)

### 6.3 輸入區
- [ ] 建立 Tabs: `Text` / `Document`
- [ ] **Text Mode**:
    - [ ] Textarea (自動調整高度)
    - [ ] 字數統計顯示
- [ ] **Document Mode**:
    - [ ] 拖曳上傳區
    - [ ] 支援格式: .txt, .md, .json, .docx
    - [ ] 檔案預覽

### 6.4 輸出區
- [ ] 翻譯結果顯示區
- [ ] Metadata 資訊:
    - [ ] Provider 顯示
    - [ ] 耗時 (ms)
    - [ ] Token / 字元數
    - [ ] 預估成本
- [ ] 複製按鈕

### 6.5 翻譯功能串接
- [ ] 呼叫 `POST /api/v1/translate`
- [ ] Loading 狀態 (Spinner)
- [ ] Error 處理與顯示

---

## Phase 7: Backend API Implementation (Prerequisites)

> ⚠️ 以下為後端需實作的 API，前端開發前需完成。

### 7.1 翻譯歷史查詢 API
- [ ] 實作 `GET /api/v1/translations`
    - [ ] 支援分頁參數: `page`, `page_size`
    - [ ] 支援搜尋: `q` (全文檢索)
    - [ ] 支援篩選: `providers`, `source_lang`, `target_lang`, `is_refined`
    - [ ] 回傳 `items` + `meta`

### 7.2 儀表板統計 API
- [ ] 實作 `GET /api/v1/stats/dashboard`
    - [ ] 總請求數 (`total_requests`)
    - [ ] 總字元數 (`total_chars`)
    - [ ] 總花費 (`total_cost_usd`)
    - [ ] 快取命中率 (`cache_hit_rate`)
    - [ ] 各 Provider 使用量 (`provider_usage`)
    - [ ] 每日趨勢 (`daily_trend`)

### 7.3 翻譯執行 API
- [ ] 確認 `POST /api/v1/translate` 已可用
- [ ] 確認回傳格式符合 FrontendSpec

---

## Phase 8: Testing & Polishing

### 8.1 整合測試
- [ ] 測試 Dashboard 資料載入
- [ ] 測試 History 分頁與篩選
- [ ] 測試 Translate 功能 (文字/文件)

### 8.2 UI/UX 優化
- [ ] Loading Skeleton 效果
- [ ] Empty State 設計 (無資料時)
- [ ] Error Boundary 處理
- [ ] 響應式設計檢查 (Mobile / Tablet / Desktop)

### 8.3 效能優化
- [ ] 圖片/圖示 Lazy Loading
- [ ] API 請求快取策略 (TanStack Query)

---

## Phase 9: Deployment

- [ ] 設定環境變數 (`PUBLIC_API_BASE_URL`)
- [ ] Build 指令: `npm run build`
- [ ] 選擇部署平台 (Vercel / Netlify / Docker)
- [ ] 設定 CORS (後端需配合)
