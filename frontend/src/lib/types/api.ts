// Translation Item from history
export interface TranslationItem {
	cache_key: string;
	original_text: string;
	translated_text: string;
	refined_text?: string;
	source_lang: string;
	target_lang: string;
	provider: 'cache' | 'deepl' | 'openai' | 'google';
	is_refined: boolean;
	char_count: number;
	created_at: string;
}

// Pagination metadata
export interface PaginationMeta {
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

// Translations list response
export interface TranslationsListResponse {
	items: TranslationItem[];
	meta: PaginationMeta;
}

// Dashboard stats response
export interface DashboardStats {
	total_requests: number;
	total_chars: number;
	total_cost_usd: number;
	cache_hit_rate: number;
	provider_usage: {
		cache: number;
		deepl: number;
		openai: number;
		google: number;
	};
	daily_trend: Array<{
		date: string;
		count: number;
	}>;
	// Provider quota details (monthly)
	deepl_chars_month: number;
	google_chars_month: number;
	openai_tokens_input_month: number;
	openai_tokens_output_month: number;
	openai_cost_month: number;
	deepl_quota_percent: number;
	google_quota_percent: number;
	deepl_quota_limit: number;
	google_quota_limit: number;
	// External Data
	exchange_rate: number;
	external_data_updated_at: string;
	pricing_data: {
		deepl_free_limit: number;
		google_free_limit: number;
		google_price_per_million_chars: number;
		openai_price_input: number;
		openai_price_output: number;
	};
}

// Translate request
export interface TranslateRequest {
	text: string;
	source_lang?: string;
	target_lang: string;
	enable_refinement?: boolean;
	preferred_provider?: 'auto' | 'deepl' | 'openai' | 'google';
}

// Translate response
export interface TranslateResponse {
	success: boolean;
	data: {
		text: string;
		provider: string;
		is_refined: boolean;
		is_cached: boolean;
		source_lang?: string;
		target_lang?: string;
		char_count?: number;
		processing_time_ms?: number;
	};
	error?: string;
}

// Languages response
export interface LanguagesResponse {
	source_languages: string[];
	target_languages: string[];
}

// Query params for translations list
export interface TranslationsQueryParams {
	page?: number;
	page_size?: number;
	q?: string;
	providers?: string[];
	source_lang?: string;
	target_lang?: string;
	is_refined?: boolean;
}
