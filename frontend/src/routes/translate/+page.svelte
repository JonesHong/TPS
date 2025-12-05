<script lang="ts">
	import { onMount } from 'svelte';
	import { translate, getLanguages } from '$lib/api';
	import type { TranslateResponse, LanguagesResponse } from '$lib/types';
	import { Button, Select, Switch, Textarea } from '$lib/components/ui';

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

	// Character count
	let charCount = $derived(sourceText.length);
	
	// When OpenAI is selected, AI Refinement is not needed (already using AI)
	let showRefinementOption = $derived(preferredProvider !== 'openai');

	// Provider options
	const providerOptions = [
		{ value: 'auto', label: 'Auto (DeepL → OpenAI → Google)' },
		{ value: 'deepl', label: 'DeepL (Free: 500K/month)' },
		{ value: 'openai', label: 'OpenAI GPT-4o-mini' },
		{ value: 'google', label: 'Google Translate' }
	];

	// Language options
	const commonLanguages = [
		{ value: '', label: 'Auto Detect' },
		{ value: 'en', label: 'English' },
		{ value: 'zh-TW', label: '繁體中文' },
		{ value: 'zh-CN', label: '简体中文' },
		{ value: 'ja', label: '日本語' },
		{ value: 'ko', label: '한국어' },
		{ value: 'de', label: 'Deutsch' },
		{ value: 'fr', label: 'Français' },
		{ value: 'es', label: 'Español' },
		{ value: 'pt', label: 'Português' },
		{ value: 'it', label: 'Italiano' },
		{ value: 'ru', label: 'Русский' },
		{ value: 'ar', label: 'العربية' },
		{ value: 'th', label: 'ไทย' },
		{ value: 'vi', label: 'Tiếng Việt' }
	];

	const targetLanguageOptions = commonLanguages.filter((l) => l.value !== '');

	onMount(async () => {
		try {
			languages = await getLanguages();
		} catch (e) {
			console.error('Failed to load languages:', e);
		}
	});

	async function handleTranslate() {
		if (!sourceText.trim()) {
			error = 'Please enter text to translate';
			return;
		}

		if (!targetLang) {
			error = 'Please select a target language';
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
				error = response.error || 'Translation failed';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Translation failed';
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
	const providerLabels: Record<string, string> = {
		cache: 'Cache',
		deepl: 'DeepL',
		openai: 'OpenAI',
		google: 'Google'
	};
</script>

<svelte:head>
	<title>Translate - TPS</title>
</svelte:head>

<div class="mx-auto max-w-5xl space-y-4">
	<!-- Controls -->
	<div class="flex flex-wrap items-center gap-4 rounded-lg border bg-white p-4 shadow-sm">
		<!-- Source language -->
		<div class="flex items-center gap-2">
			<label for="source-lang" class="text-sm font-medium text-gray-700">From:</label>
			<Select
				options={commonLanguages}
				bind:value={sourceLang}
				class="w-40"
			/>
		</div>

		<!-- Swap button -->
		<button
			type="button"
			class="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-100"
			onclick={swapLanguages}
			disabled={!sourceLang}
			title="Swap languages"
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
		<div class="flex items-center gap-2">
			<label for="target-lang" class="text-sm font-medium text-gray-700">To:</label>
			<Select
				options={targetLanguageOptions}
				bind:value={targetLang}
				class="w-40"
			/>
		</div>

		<div class="flex-1"></div>

		<!-- Provider selection -->
		<div class="flex items-center gap-2">
			<label for="provider" class="text-sm font-medium text-gray-700">Provider:</label>
			<Select
				options={providerOptions}
				bind:value={preferredProvider}
				class="w-56"
			/>
		</div>

		<!-- Refinement toggle (hidden when using OpenAI) -->
		{#if showRefinementOption}
			<div class="flex items-center gap-2">
				<Switch bind:checked={enableRefinement} />
				<span class="text-sm text-gray-700">AI Refinement</span>
			</div>
		{:else}
			<div class="flex items-center gap-2 text-sm text-gray-400">
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				<span>AI-powered (no refinement needed)</span>
			</div>
		{/if}
	</div>

	<!-- Translation panels -->
	<div class="grid gap-4 lg:grid-cols-2">
		<!-- Source panel -->
		<div class="rounded-lg border bg-white shadow-sm">
			<div class="flex items-center justify-between border-b px-4 py-3">
				<h3 class="font-medium text-gray-900">Original Text</h3>
				<span class="text-sm text-gray-500">{charCount} characters</span>
			</div>
			<div class="p-4">
				<Textarea
					placeholder="Enter text to translate..."
					bind:value={sourceText}
					rows={10}
					class="resize-none"
				/>
			</div>
			<div class="flex items-center justify-between border-t px-4 py-3">
				<button
					type="button"
					class="text-sm text-gray-500 hover:text-gray-700"
					onclick={clearAll}
				>
					Clear
				</button>
				<Button onclick={handleTranslate} disabled={loading || !sourceText.trim()}>
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
							Translating...
						</span>
					{:else}
						Translate
					{/if}
				</Button>
			</div>
		</div>

		<!-- Result panel -->
		<div class="rounded-lg border bg-white shadow-sm">
			<div class="flex items-center justify-between border-b px-4 py-3">
				<h3 class="font-medium text-gray-900">Translation</h3>
				{#if result}
					<span
						class="rounded-full px-2 py-0.5 text-xs font-medium {result.is_cached
							? 'bg-green-100 text-green-800'
							: 'bg-blue-100 text-blue-800'}"
					>
						{result.is_cached ? 'Cached' : providerLabels[result.provider] || result.provider}
					</span>
				{/if}
			</div>
			<div class="p-4">
				{#if error}
					<div class="flex h-[244px] items-center justify-center rounded-md bg-red-50 text-red-600">
						{error}
					</div>
				{:else if translatedText}
					<div class="h-[244px] overflow-auto rounded-md bg-gray-50 p-3 text-gray-900">
						{translatedText}
					</div>
				{:else}
					<div
						class="flex h-[244px] items-center justify-center rounded-md bg-gray-50 text-gray-400"
					>
						Translation will appear here
					</div>
				{/if}
			</div>
			<div class="flex items-center justify-between border-t px-4 py-3">
				<!-- Metadata -->
				{#if result}
					<div class="flex items-center gap-4 text-xs text-gray-500">
						{#if result.processing_time_ms}
							<span>{Math.round(result.processing_time_ms)}ms</span>
						{/if}
						{#if result.char_count}
							<span>{result.char_count} chars</span>
						{/if}
						{#if result.is_refined}
							<span class="text-purple-600">✨ Refined</span>
						{/if}
					</div>
				{:else}
					<div></div>
				{/if}

				<!-- Copy button -->
				<button
					type="button"
					class="flex items-center gap-1 text-sm text-gray-500 transition-colors hover:text-gray-700 disabled:opacity-50"
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
					Copy
				</button>
			</div>
		</div>
	</div>
</div>
