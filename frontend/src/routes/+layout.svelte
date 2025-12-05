<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import HistoryPanel from '$lib/components/panels/HistoryPanel.svelte';
	import StatsPanel from '$lib/components/panels/StatsPanel.svelte';
	import { selectedTranslation } from '$lib/stores';
	import type { TranslationItem } from '$lib/types';
	import '$lib/i18n'; // Initialize i18n
	import { t, locale, isLoading } from 'svelte-i18n';

	let { children } = $props();

	let isHistoryOpen = $state(false);
	let isStatsOpen = $state(false);

	function toggleHistory() {
		isHistoryOpen = !isHistoryOpen;
		if (isHistoryOpen) isStatsOpen = false;
	}

	function toggleStats() {
		isStatsOpen = !isStatsOpen;
		if (isStatsOpen) isHistoryOpen = false;
	}

	function closeAll() {
		isHistoryOpen = false;
		isStatsOpen = false;
	}

	function handleHistorySelect(item: TranslationItem) {
		selectedTranslation.set(item);
		isHistoryOpen = false;
	}

	function toggleLanguage() {
		const current = $locale;
		const next = current === 'zh-TW' ? 'en' : 'zh-TW';
		locale.set(next);
	}
</script>

{#if $isLoading}
	<div class="flex h-screen w-full items-center justify-center bg-slate-50">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
	</div>
{:else}
	<div class="flex h-screen w-full bg-slate-50 font-sans text-slate-900">
		<!-- Dock / Sidebar -->
		<aside class="flex w-20 flex-col items-center border-r border-slate-800 bg-slate-900 py-6 shadow-xl z-50">
			<!-- Logo -->
			<div class="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-900/50">
				<span class="text-xl font-bold">T</span>
			</div>

			<!-- Navigation -->
			<nav class="flex flex-1 flex-col gap-6 w-full items-center">
				<!-- Translate (Home) -->
				<a 
					href="/" 
					class="group relative flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-200 {$page.url.pathname === '/' && !isHistoryOpen && !isStatsOpen ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}"
					onclick={closeAll}
					title={$t('nav.translate')}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
					</svg>
					<span class="absolute left-16 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white opacity-0 shadow-xl transition-opacity group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-slate-700">
						{$t('nav.translate')}
					</span>
				</a>

				<!-- File Translation -->
				<a 
					href="/files" 
					class="group relative flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-200 {$page.url.pathname === '/files' && !isHistoryOpen && !isStatsOpen ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}"
					onclick={closeAll}
					title={$t('nav.files')}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
					</svg>
					<span class="absolute left-16 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white opacity-0 shadow-xl transition-opacity group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-slate-700">
						{$t('nav.files')}
					</span>
				</a>

				<!-- History -->
				<button 
					class="group relative flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-200 {isHistoryOpen ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}"
					onclick={toggleHistory}
					title={$t('nav.history')}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
					</svg>
					<span class="absolute left-16 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white opacity-0 shadow-xl transition-opacity group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-slate-700">
						{$t('nav.history')}
					</span>
				</button>

				<!-- Dashboard / Stats -->
				<button 
					class="group relative flex h-12 w-12 items-center justify-center rounded-xl transition-all duration-200 {isStatsOpen ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}"
					onclick={toggleStats}
					title={$t('nav.dashboard')}
				>
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
					</svg>
					<span class="absolute left-16 rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white opacity-0 shadow-xl transition-opacity group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 border border-slate-700">
						{$t('nav.dashboard')}
					</span>
				</button>
			</nav>

			<!-- Bottom Actions -->
			<div class="mt-auto flex flex-col gap-4 w-full items-center">
				<!-- Language Switcher -->
				<button 
					class="group relative flex h-10 w-10 items-center justify-center rounded-lg text-slate-400 transition-all hover:bg-slate-800 hover:text-white"
					onclick={toggleLanguage}
					title="Switch Language"
				>
					<span class="text-xs font-bold uppercase tracking-wider">{$locale === 'zh-TW' ? '中' : 'EN'}</span>
				</button>

				<!-- Settings -->
				<button class="group relative flex h-10 w-10 items-center justify-center rounded-lg text-slate-400 transition-all hover:bg-slate-800 hover:text-white">
					<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
					</svg>
				</button>
			</div>
		</aside>

		<!-- Main Content -->
		<main class="flex-1 overflow-hidden relative">
			{@render children()}
		</main>

		<!-- Panels -->
		<HistoryPanel bind:isOpen={isHistoryOpen} onSelect={handleHistorySelect} />
		<StatsPanel bind:isOpen={isStatsOpen} />
	</div>
{/if}
