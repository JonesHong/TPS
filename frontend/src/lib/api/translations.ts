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
