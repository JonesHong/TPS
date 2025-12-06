import { get, post } from './client';
import type {
	TranslationsListResponse,
	TranslationsQueryParams,
	TranslateRequest,
	TranslateResponse,
	LanguagesResponse
} from '$lib/types';

export async function getTranslations(params: TranslationsQueryParams = {}): Promise<TranslationsListResponse> {
	const queryParams: Record<string, string | number | boolean | string[] | undefined> = {
		page: params.page,
		page_size: params.page_size,
		q: params.q,
		source_lang: params.source_lang,
		target_lang: params.target_lang,
		is_refined: params.is_refined
	};
	
	// Handle providers array
	if (params.providers && params.providers.length > 0) {
		queryParams.providers = params.providers;
	}
	
	return get<TranslationsListResponse>('/translations', { params: queryParams });
}

export async function translate(request: TranslateRequest): Promise<TranslateResponse> {
	return post<TranslateResponse, TranslateRequest>('/translate', request);
}

export async function translateFile(
	file: File,
	targetLang: string,
	sourceLang?: string,
	enableRefinement: boolean = false,
	preferredProvider?: string
): Promise<TranslateResponse> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('target_lang', targetLang);
	if (sourceLang) formData.append('source_lang', sourceLang);
	formData.append('enable_refinement', String(enableRefinement));
	if (preferredProvider) formData.append('preferred_provider', preferredProvider);

	const response = await fetch('/api/v1/translate/file', {
		method: 'POST',
		body: formData
	});

	if (!response.ok) {
		throw new Error(`HTTP error! status: ${response.status}`);
	}

	return response.json();
}

export async function getLanguages(): Promise<LanguagesResponse> {
	return get<LanguagesResponse>('/languages');
}

export async function deleteTranslation(cacheKey: string): Promise<void> {
	const response = await fetch(`/api/v1/history/${cacheKey}`, { method: 'DELETE' });
	if (!response.ok) throw new Error('Failed to delete translation');
}

export async function updateTranslation(cacheKey: string, translatedText: string, refinedText?: string): Promise<void> {
	const response = await fetch(`/api/v1/history/${cacheKey}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ translated_text: translatedText, refined_text: refinedText })
	});
	if (!response.ok) throw new Error('Failed to update translation');
}

export async function refineTranslation(cacheKey: string): Promise<TranslateResponse> {
	const response = await fetch(`/api/v1/history/${cacheKey}/refine`, { method: 'POST' });
	if (!response.ok) throw new Error('Failed to refine translation');
	return response.json();
}
