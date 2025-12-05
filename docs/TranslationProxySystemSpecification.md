# Translation Proxy System Specification (v2.0)

## 1. 系統概述 (System Overview)
本系統為高可用、低成本且具備 AI 智慧的翻譯中介層。整合 **SQLite 本地快取**、**NMT (DeepL/Google)** 與 **LLM (OpenAI)**，實現多層次防禦策略。

### 1.1 核心目標
*   **成本最佳化 (Cost Efficiency)**：透過 Cache 與低成本 LLM (`gpt-4o-mini`) 大幅降低對昂貴 API (Google) 的依賴。
*   **品質提升 (Quality)**：引入 LLM 進行「語意校稿 (Refinement)」，解決傳統機翻生硬問題。
*   **高可用性 (Resilience)**：具備自動 Failover 與熔斷機制。

### 1.2 服務型態
*   **介面**：Synchronous REST API
*   **回應格式**：統一 JSON 結構，包含狀態碼與錯誤訊息。

---

## 2. 策略配置 (Strategy Configuration)

為平衡成本與品質，定義以下預設優先級策略 (Strategy Profile)：

1.  **Tier 1: Local Cache (SQLite)**
    *   **成本**：$0
    *   **延遲**：< 10ms
    *   **說明**：優先查找本地紀錄。若命中且符合校稿需求 (`is_refined` 狀態吻合)，直接回傳。

2.  **Tier 2: DeepL API (Primary NMT)**
    *   **成本**：低 (利用每月免費額度 500,000 字元)
    *   **品質**：高
    *   **說明**：首選外部翻譯引擎。

3.  **Tier 3: OpenAI `gpt-4o-mini` (Secondary / Fallback)**
    *   **成本**：極低 ($0.15 / 1M input tokens)
    *   **品質**：中高 (需透過 Prompt 控制)
    *   **說明**：當 DeepL 額度用盡或失敗時接手。**比 Google 便宜約 90%**。

4.  **Tier 4: Google Translate V3 (Last Resort)**
    *   **成本**：高 (每月前 50 萬字元免費，之後 $20 / 1M chars)
    *   **品質**：穩定
    *   **說明**：僅在 DeepL 與 OpenAI 皆不可用時的最後防線。雖有少量免費額度，但超額後單價最高。

5.  **Optional: AI Refinement (校稿)**
    *   **觸發**：僅當 `enable_refinement=True` 且原始翻譯來源非 OpenAI 時觸發。
    *   **模型**：`gpt-4o-mini` (預設) 或 `gpt-4o` (高階)。

---

## 3. 資料庫設計 (Database Schema)

採用 SQLite (WAL Mode) 以支援高併發。

### 3.1 設定 (Configuration)
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000; -- 64MB
PRAGMA busy_timeout = 5000;
```

### 3.2 Table: `translations` (快取層)
| 欄位名稱 | 類型 | 說明 |
| :--- | :--- | :--- |
| `cache_key` | TEXT (PK) | MD5 Hash (Source+Target+Format+Text) |
| `source_lang` | TEXT | 來源語言 (ISO) |
| `target_lang` | TEXT | 目標語言 (ISO) |
| `original_text` | TEXT | 正規化原文 |
| `translated_text` | TEXT | 最終翻譯結果 |
| `provider` | TEXT | `deepl`, `google`, `openai` |
| `is_refined` | BOOLEAN | 是否經過 AI 校稿 (Default: 0) |
| `refinement_model`| TEXT | 校稿模型名稱 (Nullable) |
| `char_count` | INTEGER | 原文字元數 |
| `created_at` | DATETIME | 建立時間 |
| `last_accessed_at`| DATETIME | 用於 LRU 清理 |
| `expires_at` | DATETIME | (Optional) 強制過期時間 |

*   **Indices**:
    *   `idx_cleanup`: ON `translations(last_accessed_at)`

### 3.3 Table: `daily_usage_stats` (統計與預算)
| 欄位名稱 | 類型 | 說明 |
| :--- | :--- | :--- |
| `date` | TEXT (PK) | YYYY-MM-DD |
| `provider` | TEXT (PK) | `deepl`, `google`, `openai_trans`, `openai_refine` |
| `request_count` | INTEGER | 呼叫次數 |
| `char_count` | INTEGER | 字元數 (DeepL/Google 計費基準) |
| `token_input` | INTEGER | Input Tokens (OpenAI 用) |
| `token_output` | INTEGER | Output Tokens (OpenAI 用) |
| `cost_estimated` | REAL | 預估費用 (USD) |

---

## 4. LLM 策略與 Prompt 工程

### 4.1 Prompt 架構
採用 `System` + `User` 分層結構，並強制 JSON 輸出以利程式解析。

**情境 A: 純翻譯 (Translation)**
*   **System**: "You are a professional translator API. Translate the user's text from {source} to {target}. Preserve all HTML tags and variables (e.g., {name}). Do not add explanations."
*   **User**: `{ "text": "..." }`

**情境 B: 校稿 (Refinement)**
*   **System**: "You are a localization expert. Improve the translation for naturalness and nuance. Keep technical terms consistent. Return JSON."
*   **User**:
    ```json
    {
      "source_lang": "en",
      "target_lang": "zh-TW",
      "original": "...",
      "draft_translation": "..."
    }
    ```

### 4.2 參數設定
*   **Temperature**: 翻譯 `0.1` (穩定)，校稿 `0.3` (自然)。
*   **Max Tokens**: 動態設定為 `Input Tokens * 2` 以防截斷或無限迴圈。

---

## 5. 核心流程 (Core Workflow)

### 5.1 錯誤處理規範
API 回傳統一格式：
```json
{
  "success": true,
  "data": { "text": "...", "provider": "deepl", "is_refined": false },
  "error": null
}
```
若全失敗，回傳 `success: false` 並由 Client 決定是否顯示原文。

### 5.2 邏輯 Pseudocode

```python
def handle_translation_request(text, source, target, options):
    # 1. Key Generation & Cache Lookup
    key = generate_md5_key(text, source, target, options['format'])
    cached = db.query(key)
    
    # Cache Hit 邏輯：有快取 且 (不需校稿 或 快取已是校稿版)
    if cached and (not options['enable_refinement'] or cached.is_refined):
        update_last_accessed(key)
        return success_response(cached.translated_text, "cache")

    result_text = None
    provider = None
    is_refined = False

    # 2. Translation Chain (Failover)
    try:
        # Tier 2: DeepL
        if not result_text and not is_quota_exceeded('deepl'):
            try:
                result_text = deepl_api.translate(text, source, target)
                provider = 'deepl'
                record_usage('deepl', char_len=len(text))
            except QuotaExceeded:
                set_quota_exceeded('deepl')

        # Tier 3: OpenAI (gpt-4o-mini)
        if not result_text and not is_budget_exceeded('openai'):
            try:
                result_text, usage = openai_api.translate(text, model='gpt-4o-mini')
                provider = 'openai'
                record_usage('openai_trans', tokens=usage)
            except OpenAIError:
                pass

        # Tier 4: Google
        if not result_text and not is_budget_exceeded('google'):
            try:
                result_text = google_api.translate(text, source, target)
                provider = 'google'
                record_usage('google', char_len=len(text))
            except GoogleAPIError:
                pass
                
    except Exception as e:
        log_system_error(e)
        return error_response("Translation failed", original_text=text)

    if not result_text:
        return error_response("All providers failed", original_text=text)

    # 3. Refinement (Optional)
    if options['enable_refinement'] and provider != 'openai':
        if not is_budget_exceeded('openai'):
            try:
                refined, usage = openai_api.refine(text, result_text, model='gpt-4o-mini')
                result_text = refined
                is_refined = True
                record_usage('openai_refine', tokens=usage)
            except Exception:
                log_warning("Refinement failed, using draft")

    # 4. Save to Cache
    db.upsert(key, result_text, provider, is_refined, ...)
    
    return success_response(result_text, provider, is_refined)
```

---

## 6. 用量與成本控管 (Cost Control)

### 6.1 預算熔斷 (Circuit Breaker)
*   **DeepL**: 依賴 API 回傳狀態或 456 錯誤碼。
*   **Google**: 本地 `daily_usage_stats` 累加字元數 > 每日限額 (如 $10) 則阻擋。
*   **OpenAI**: 本地 `daily_usage_stats` 累加預估費用 > 每日限額 (如 $5) 則阻擋。

### 6.2 費用估算公式
*   **OpenAI Cost** = `(Input_Tokens * Price_In) + (Output_Tokens * Price_Out)`
*   **Google Cost** = `(Char_Count / 1,000,000) * 20`

---

## 7. 安全性與運維 (Security & Ops)

### 7.1 安全性
*   **API Keys**: 僅透過環境變數 (Environment Variables) 注入，嚴禁 Hardcode。
*   **PII (個資) 處理**: 
    *   本系統預設**不處理** PII 脫敏。
    *   若原文包含敏感個資 (姓名、卡號)，呼叫端需自行負責或先進行遮蔽 (Masking)。

### 7.2 監控與日誌
*   **Logging**: 記錄 `request_id`, `provider`, `latency_ms`, `success`。**禁止記錄完整原文或譯文**以防洩漏隱私。
*   **Metrics**: 監控 Cache Hit Rate (目標 > 80%) 與 Provider Error Rate。

### 7.3 維護排程
*   **Weekly**: 清理 `last_accessed_at > 90 days` 的快取。
*   **Monthly**: 執行 `VACUUM` 重組資料庫。

---

## 8. 開發實作 Checklist

*   [ ] **Database**: 建立 SQLite Table 並確認 WAL 模式開啟。
*   [ ] **API Clients**:
    *   DeepL SDK (處理 Quota Exception)。
    *   Google Cloud Translation Client (設定 Credentials)。
    *   OpenAI SDK (設定 Timeout 與 Retry)。
*   [ ] **Token Counting**: 整合 `tiktoken` 套件，確保 OpenAI 費用估算準確。
*   [ ] **Cost Logic**: 實作 `daily_usage_stats` 的寫入與熔斷檢查邏輯。
*   [ ] **Refinement**: 實作校稿 Prompt 與 JSON Parser。
*   [ ] **Testing**: 撰寫 Unit Test 模擬各 Provider 失敗時的 Fallback 行為。
