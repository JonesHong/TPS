<script lang="ts">
	import { onMount } from 'svelte';
	import { selectedTranslation } from '$lib/stores';
	import { translate, getLanguages } from '$lib/api';
	import type { TranslateResponse, LanguagesResponse } from '$lib/types';
	import { Button, Select, Switch, Textarea } from '$lib/components/ui';
	import { t } from 'svelte-i18n';

	// State
	let sourceText = $state('');
	let translatedText = $state('');
	let sourceLang = $state('');
	let targetLang = $state('zh-TW');
	let enableRefinement = $state(false);
	let preferredProvider = $state<'auto' | 'deepl' | 'openai' | 'google'>('auto');
	let loading = $state(false);
	let error = $state<string | null>(null);
	let result = $state<TranslateResponse['data'] | null>(null);
	let languages = $state<LanguagesResponse>({ source_languages: [], target_languages: [] });

	// Handle history selection
	$effect(() => {
		if ($selectedTranslation) {
			sourceText = $selectedTranslation.original_text;
			sourceLang = $selectedTranslation.source_lang;
			targetLang = $selectedTranslation.target_lang;
			translatedText = $selectedTranslation.translated_text;
			
			// Set provider if valid
			const provider = $selectedTranslation.provider;
			if (['auto', 'deepl', 'openai', 'google'].includes(provider)) {
				preferredProvider = provider as any;
			}
			
			// Reset selection
			selectedTranslation.set(null);
		}
	});

	// Character count
	let charCount = $derived(sourceText.length);
	
	// When OpenAI is selected, AI Refinement is not needed (already using AI)
	let showRefinementOption = $derived(preferredProvider !== 'openai');

	// Provider options
	let providerOptions = $derived([
		{ value: 'auto', label: $t('providers.auto') },
		{ value: 'deepl', label: $t('providers.deepl') },
		{ value: 'openai', label: $t('providers.openai') },
		{ value: 'google', label: $t('providers.google') }
	]);

	// Language options
	let commonLanguages = $derived([
		{ value: '', label: $t('common.auto_detect') },
		{ value: 'zh-TW', label: $t('languages.zh-TW') },
		{ value: 'zh-CN', label: $t('languages.zh-CN') },
		{ value: 'en', label: $t('languages.en') },
		{ value: 'ja', label: $t('languages.ja') },
		{ value: 'ko', label: $t('languages.ko') },
		{ value: 'ms', label: $t('languages.ms') },
		{ value: 'vi', label: $t('languages.vi') },
		{ value: 'th', label: $t('languages.th') },
		{ value: 'id', label: $t('languages.id') },
		{ value: 'tl', label: $t('languages.tl') },
		{ value: 'fr', label: $t('languages.fr') },
		{ value: 'de', label: $t('languages.de') },
		{ value: 'es', label: $t('languages.es') },
		{ value: 'it', label: $t('languages.it') },
		{ value: 'ru', label: $t('languages.ru') },
		{ value: 'pt', label: $t('languages.pt') },
		{ value: 'ar', label: $t('languages.ar') },
		{ value: 'hi', label: $t('languages.hi') }
	]);

	let targetLanguageOptions = $derived(commonLanguages.filter((l) => l.value !== ''));

	onMount(async () => {
		try {
			languages = await getLanguages();
		} catch (e) {
			console.error('Failed to load languages:', e);
		}
	});

	async function handleTranslate() {
		if (!sourceText.trim()) {
			error = $t('translate.error_empty');
			return;
		}

		if (!targetLang) {
			error = $t('translate.error_target');
			return;
		}

		loading = true;
		error = null;
		result = null;

		const startTime = performance.now();

		try {
			const response = await translate({
				text: sourceText,
				source_lang: sourceLang || undefined,
				target_lang: targetLang,
				enable_refinement: showRefinementOption ? enableRefinement : false,
				preferred_provider: preferredProvider
			});

			if (response.success && response.data) {
				result = {
					...response.data,
					processing_time_ms: performance.now() - startTime
				};
				translatedText = response.data.text;
			} else {
				error = response.error || $t('translate.failed');
			}
		} catch (e) {
			error = e instanceof Error ? e.message : $t('translate.failed');
		} finally {
			loading = false;
		}
	}

	function copyToClipboard() {
		if (translatedText) {
			navigator.clipboard.writeText(translatedText);
		}
	}

	function clearAll() {
		sourceText = '';
		translatedText = '';
		result = null;
		error = null;
	}

	function swapLanguages() {
		if (sourceLang && targetLang) {
			const temp = sourceLang;
			sourceLang = targetLang;
			targetLang = temp;
			
			// Also swap texts if there's a translation
			if (translatedText) {
				const tempText = sourceText;
				sourceText = translatedText;
				translatedText = tempText;
			}
		}
	}

	// Provider display
	let providerLabels = $derived({
		cache: $t('providers.cache'),
		deepl: 'DeepL',
		openai: 'OpenAI',
		google: 'Google'
	});
</script>

<svelte:head>
	<title>{$t('app.title')}</title>
</svelte:head>

<div class="mx-auto max-w-6xl space-y-6 p-6">
	<!-- Controls -->
	<div class="flex flex-wrap items-center gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-lg shadow-slate-200/50">
		<!-- Source language -->
		<div class="flex items-center gap-3">
			<label for="source-lang" class="text-sm font-semibold text-slate-600">{$t('translate.from')}:</label>
			<Select
				options={commonLanguages}
				bind:value={sourceLang}
				class="w-44 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
			/>
		</div>

		<!-- Swap button -->
		<button
			type="button"
			class="rounded-full p-2 text-slate-400 transition-all hover:bg-indigo-50 hover:text-indigo-600 disabled:opacity-30"
			onclick={swapLanguages}
			disabled={!sourceLang}
			title={$t('translate.swap')}
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
				/>
			</svg>
		</button>

		<!-- Target language -->
		<div class="flex items-center gap-3">
			<label for="target-lang" class="text-sm font-semibold text-slate-600">{$t('translate.to')}:</label>
			<Select
				options={targetLanguageOptions}
				bind:value={targetLang}
				class="w-44 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
			/>
		</div>

		<div class="flex-1"></div>

		<!-- Provider selection -->
		<div class="flex items-center gap-3">
			<label for="provider" class="text-sm font-semibold text-slate-600">{$t('translate.provider')}:</label>
			<Select
				options={providerOptions}
				bind:value={preferredProvider}
				class="w-60 rounded-lg border-slate-300 focus:border-indigo-500 focus:ring-indigo-500"
			/>
		</div>

		<!-- Refinement toggle (hidden when using OpenAI) -->
		{#if showRefinementOption}
			<div class="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-1.5 border border-slate-100">
				<Switch bind:checked={enableRefinement} />
				<span class="text-sm font-medium text-slate-700">{$t('translate.refinement')}</span>
			</div>
		{:else}
			<div class="flex items-center gap-2 rounded-lg bg-indigo-50 px-3 py-1.5 text-sm text-indigo-600 border border-indigo-100">
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				<span class="font-medium">{$t('translate.ai_powered')}</span>
			</div>
		{/if}
	</div>

	<!-- Translation panels -->
	<div class="grid gap-6 lg:grid-cols-2 h-[calc(100vh-12rem)]">
		<!-- Source panel -->
		<div class="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-200/50 transition-all focus-within:ring-2 focus-within:ring-indigo-500/20">
			<div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
				<h3 class="font-semibold text-slate-800">{$t('translate.original_text')}</h3>
				<span class="text-xs font-medium text-slate-400 bg-slate-100 px-2 py-1 rounded-full">{charCount} {$t('translate.chars')}</span>
			</div>
			<div class="flex-1 p-5">
				<Textarea
					placeholder={$t('translate.placeholder')}
					bind:value={sourceText}
					class="h-full w-full resize-none border-0 p-0 text-lg leading-relaxed text-slate-700 placeholder:text-slate-300 focus:ring-0"
				/>
			</div>
			<div class="flex items-center justify-between border-t border-slate-100 px-5 py-4 bg-slate-50/50 rounded-b-2xl">
				<button
					type="button"
					class="text-sm font-medium text-slate-500 hover:text-red-500 transition-colors"
					onclick={clearAll}
				>
					{$t('translate.clear')}
				</button>
				<Button 
					onclick={handleTranslate} 
					disabled={loading || !sourceText.trim()}
					class="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/30 px-6 py-2 rounded-lg font-medium transition-all active:scale-95"
				>
					{#if loading}
						<span class="flex items-center gap-2">
							<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24">
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
									fill="none"
								></circle>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
								></path>
							</svg>
							{$t('translate.translating')}
						</span>
					{:else}
						{$t('translate.translate_btn')}
					{/if}
				</Button>
			</div>
		</div>

		<!-- Result panel -->
		<div class="flex flex-col rounded-2xl border border-slate-200 bg-slate-50/50 shadow-xl shadow-slate-200/50">
			<div class="flex items-center justify-between border-b border-slate-200/60 px-5 py-4">
				<h3 class="font-semibold text-slate-800">{$t('translate.translation')}</h3>
				{#if result}
					<span
						class="rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide uppercase {result.is_cached
							? 'bg-emerald-100 text-emerald-700'
							: 'bg-indigo-100 text-indigo-700'}"
					>
						{result.is_cached ? $t('translate.cached') : providerLabels[result.provider] || result.provider}
					</span>
				{/if}
			</div>
			<div class="flex-1 p-5 relative">
				{#if error}
					<div class="flex h-full items-center justify-center rounded-xl bg-red-50 text-red-600 border border-red-100">
						<div class="text-center">
							<svg class="mx-auto h-8 w-8 mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
							</svg>
							{error}
						</div>
					</div>
				{:else if translatedText}
					<div class="h-full overflow-auto text-lg leading-relaxed text-slate-800">
						{translatedText}
					</div>
				{:else}
					<div
						class="flex h-full items-center justify-center text-slate-300"
					>
						<div class="text-center">
							<svg class="mx-auto h-12 w-12 mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
							</svg>
							<span>{$t('translate.translation')}</span>
						</div>
					</div>
				{/if}
			</div>
			<div class="flex items-center justify-between border-t border-slate-200/60 px-5 py-4 bg-slate-100/50 rounded-b-2xl">
				<!-- Metadata -->
				{#if result}
					<div class="flex items-center gap-4 text-xs font-medium text-slate-500">
						{#if result.processing_time_ms}
							<span class="flex items-center gap-1">
								<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
								</svg>
								{Math.round(result.processing_time_ms)}ms
							</span>
						{/if}
						{#if result.char_count}
							<span>{result.char_count} {$t('translate.chars')}</span>
						{/if}
						{#if result.is_refined}
							<span class="flex items-center gap-1 text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
								<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
								</svg>
								{$t('translate.refined')}
							</span>
						{/if}
					</div>
				{:else}
					<div></div>
				{/if}

				<!-- Copy button -->
				<button
					type="button"
					class="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 transition-all hover:bg-white hover:text-indigo-600 hover:shadow-sm disabled:opacity-50"
					onclick={copyToClipboard}
					disabled={!translatedText}
				>
					<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
						/>
					</svg>
					{$t('translate.copy')}
				</button>
			</div>
		</div>
	</div>
</div>
