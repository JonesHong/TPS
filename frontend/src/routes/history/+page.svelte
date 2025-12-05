<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { getTranslations, getLanguages } from '$lib/api';
	import type { TranslationItem, PaginationMeta, LanguagesResponse } from '$lib/types';
	import { Input } from '$lib/components/ui';
	import { Pagination } from '$lib/components/common';
	import { TranslationTable, FilterBar } from '$lib/components/history';

	// State
	let items = $state<TranslationItem[]>([]);
	let meta = $state<PaginationMeta>({ total: 0, page: 1, page_size: 20, total_pages: 0 });
	let languages = $state<LanguagesResponse>({ source_languages: [], target_languages: [] });
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Filter state
	let searchQuery = $state('');
	let selectedProviders = $state<string[]>([]);
	let selectedSourceLang = $state('');
	let selectedTargetLang = $state('');
	let currentPage = $state(1);
	let pageSize = $state(20);

	// Debounce timer
	let searchTimeout: ReturnType<typeof setTimeout>;

	// Available providers
	const providers = ['cache', 'deepl', 'openai', 'google'];

	onMount(async () => {
		// Parse URL params
		const params = $page.url.searchParams;
		searchQuery = params.get('q') || '';
		currentPage = parseInt(params.get('page') || '1', 10);
		pageSize = parseInt(params.get('page_size') || '20', 10);
		selectedSourceLang = params.get('source_lang') || '';
		selectedTargetLang = params.get('target_lang') || '';
		const providersParam = params.get('providers');
		if (providersParam) {
			selectedProviders = providersParam.split(',');
		}

		// Load languages
		try {
			languages = await getLanguages();
		} catch (e) {
			console.error('Failed to load languages:', e);
		}

		await loadTranslations();
	});

	async function loadTranslations() {
		loading = true;
		error = null;
		try {
			const result = await getTranslations({
				page: currentPage,
				page_size: pageSize,
				q: searchQuery || undefined,
				providers: selectedProviders.length > 0 ? selectedProviders : undefined,
				source_lang: selectedSourceLang || undefined,
				target_lang: selectedTargetLang || undefined
			});
			items = result.items;
			meta = result.meta;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load translations';
		} finally {
			loading = false;
		}
	}

	function updateUrl() {
		const params = new URLSearchParams();
		if (searchQuery) params.set('q', searchQuery);
		if (currentPage > 1) params.set('page', currentPage.toString());
		if (pageSize !== 20) params.set('page_size', pageSize.toString());
		if (selectedProviders.length > 0) params.set('providers', selectedProviders.join(','));
		if (selectedSourceLang) params.set('source_lang', selectedSourceLang);
		if (selectedTargetLang) params.set('target_lang', selectedTargetLang);

		const queryString = params.toString();
		goto(queryString ? `?${queryString}` : '/history', { replaceState: true, noScroll: true });
	}

	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			currentPage = 1;
			updateUrl();
			loadTranslations();
		}, 500);
	}

	function handlePageChange(page: number) {
		currentPage = page;
		updateUrl();
		loadTranslations();
	}

	function handlePageSizeChange(size: number) {
		pageSize = size;
		currentPage = 1;
		updateUrl();
		loadTranslations();
	}

	function handleProvidersChange(newProviders: string[]) {
		selectedProviders = newProviders;
		currentPage = 1;
		updateUrl();
		loadTranslations();
	}

	function handleSourceLangChange(lang: string) {
		selectedSourceLang = lang;
		currentPage = 1;
		updateUrl();
		loadTranslations();
	}

	function handleTargetLangChange(lang: string) {
		selectedTargetLang = lang;
		currentPage = 1;
		updateUrl();
		loadTranslations();
	}
</script>

<svelte:head>
	<title>Translation History - TPS</title>
</svelte:head>

<div class="space-y-4">
	<!-- Search bar -->
	<div class="rounded-lg border bg-white p-4 shadow-sm">
		<div class="relative">
			<svg
				class="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/>
			</svg>
			<Input
				type="search"
				placeholder="Search translations..."
				bind:value={searchQuery}
				oninput={handleSearch}
				class="pl-10"
			/>
		</div>
	</div>

	<!-- Filters -->
	<div class="rounded-lg border bg-white p-4 shadow-sm">
		<FilterBar
			{providers}
			sourceLanguages={languages.source_languages}
			targetLanguages={languages.target_languages}
			{selectedProviders}
			{selectedSourceLang}
			{selectedTargetLang}
			onProvidersChange={handleProvidersChange}
			onSourceLangChange={handleSourceLangChange}
			onTargetLangChange={handleTargetLangChange}
		/>
	</div>

	<!-- Table -->
	<div class="rounded-lg border bg-white shadow-sm">
		{#if loading}
			<div class="flex h-64 items-center justify-center">
				<div class="text-gray-500">Loading...</div>
			</div>
		{:else if error}
			<div class="flex h-64 flex-col items-center justify-center gap-4">
				<p class="text-red-600">{error}</p>
				<button
					class="rounded bg-primary-600 px-4 py-2 text-sm text-white hover:bg-primary-700"
					onclick={loadTranslations}
				>
					Retry
				</button>
			</div>
		{:else}
			<TranslationTable {items} />
		{/if}
	</div>

	<!-- Pagination -->
	{#if !loading && !error && meta.total > 0}
		<div class="rounded-lg border bg-white p-4 shadow-sm">
			<Pagination
				{meta}
				onPageChange={handlePageChange}
				onPageSizeChange={handlePageSizeChange}
			/>
		</div>
	{/if}
</div>
