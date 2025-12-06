<script lang="ts">
	import { onMount } from 'svelte';
	import { getTranslations, getLanguages } from '$lib/api';
	import type { TranslationItem, PaginationMeta, LanguagesResponse } from '$lib/types';
	import { Input } from '$lib/components/ui';
	import { Pagination } from '$lib/components/common';
	import { TranslationTable, FilterBar } from '$lib/components/history';
	import { t } from 'svelte-i18n';

	// Props
	let { isOpen = $bindable(false), onSelect } = $props<{ 
		isOpen: boolean;
		onSelect?: (item: TranslationItem) => void;
	}>();

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
		// Load languages
		try {
			languages = await getLanguages();
		} catch (e) {
			console.error('Failed to load languages:', e);
		}
		// Initial load
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
			error = e instanceof Error ? e.message : $t('history.error_load');
		} finally {
			loading = false;
		}
	}

	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			currentPage = 1;
			loadTranslations();
		}, 500);
	}

	function handlePageChange(page: number) {
		currentPage = page;
		loadTranslations();
	}

	function handlePageSizeChange(size: number) {
		pageSize = size;
		currentPage = 1;
		loadTranslations();
	}

	function handleProvidersChange(newProviders: string[]) {
		selectedProviders = newProviders;
		currentPage = 1;
		loadTranslations();
	}

	function handleSourceLangChange(lang: string) {
		selectedSourceLang = lang;
		currentPage = 1;
		loadTranslations();
	}

	function handleTargetLangChange(lang: string) {
		selectedTargetLang = lang;
		currentPage = 1;
		loadTranslations();
	}

	function close() {
		isOpen = false;
	}
</script>

{#if isOpen}
	<!-- Backdrop -->
	<div 
		class="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm transition-opacity"
		onclick={close}
		role="button"
		tabindex="0"
		onkeydown={(e) => e.key === 'Escape' && close()}
	></div>

	<!-- Panel -->
	<div class="fixed inset-y-0 right-0 z-50 flex w-full max-w-6xl transform flex-col bg-white shadow-2xl transition-transform duration-300 ease-in-out">
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-slate-50/50">
			<h2 class="text-xl font-bold text-slate-800">{$t('history.title')}</h2>
			<button 
				class="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
				onclick={close}
			>
				<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="flex flex-1 flex-col overflow-hidden bg-slate-50/30">
			<div class="flex-1 overflow-y-auto p-6">
				<div class="space-y-6">
					<!-- Search and Filters -->
					<div class="flex flex-col gap-4">
						<div class="relative">
							<svg
								class="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400"
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
								type="text"
								placeholder={$t('history.search_placeholder')}
								bind:value={searchQuery}
								oninput={handleSearch}
								class="pl-10 rounded-xl border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
							/>
						</div>
					</div>

					<!-- Filters -->
					<FilterBar
						{languages}
						{selectedProviders}
						{selectedSourceLang}
						{selectedTargetLang}
						onProvidersChange={handleProvidersChange}
						onSourceLangChange={handleSourceLangChange}
						onTargetLangChange={handleTargetLangChange}
					/>

					<!-- Table -->
					<div class="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
						{#if loading}
							<div class="p-12 text-center text-slate-500 flex flex-col items-center gap-3">
								<div class="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
								<span>{$t('common.loading')}</span>
							</div>
						{:else if error}
							<div class="p-12 text-center text-red-500">{error}</div>
						{:else}
							<TranslationTable {items} {onSelect} />
						{/if}
					</div>

					<!-- Pagination -->
					{#if meta.total_pages > 1}
						<Pagination
							{meta}
							onPageChange={handlePageChange}
							onPageSizeChange={handlePageSizeChange}
						/>
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}
