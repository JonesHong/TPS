<script lang="ts">
	import { onMount } from 'svelte';
	import { getDashboardStats } from '$lib/api';
	import type { DashboardStats } from '$lib/types';
	import { KpiCard } from '$lib/components/dashboard';
	import { ProviderPieChart, DailyVolumeChart } from '$lib/components/charts';
	import { t, locale } from 'svelte-i18n';
	import { slide } from 'svelte/transition';

	// Props
	let { isOpen = $bindable(false) } = $props<{ isOpen: boolean }>();

	let stats: DashboardStats | null = $state(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let isOpenAIExpanded = $state(false);

	// Load stats when opened
	$effect(() => {
		if (isOpen) {
			loadStats();
		}
	});

	async function loadStats(days: number = 30) {
		loading = true;
		error = null;
		try {
			stats = await getDashboardStats(days);
		} catch (e) {
			error = e instanceof Error ? e.message : $t('stats.error');
		} finally {
			loading = false;
		}
	}

	function handleRangeChange(days: number) {
		loadStats(days);
	}

	function formatCurrency(value: number): string {
		if ($locale === 'zh-TW') {
			return new Intl.NumberFormat('zh-TW', {
				style: 'currency',
				currency: 'TWD',
				minimumFractionDigits: 3
			}).format(value * 32.5);
		}
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 3
		}).format(value);
	}

	function formatNumber(value: number): string {
		if (value >= 1000000) {
			return `${(value / 1000000).toFixed(1)}M`;
		}
		if (value >= 1000) {
			return `${(value / 1000).toFixed(1)}K`;
		}
		return value.toString();
	}

	function formatPercentage(value: number): string {
		return `${(value * 100).toFixed(1)}%`;
	}

	function formatTokens(value: number): string {
		if (value >= 1000000) {
			return `${(value / 1000000).toFixed(2)}M`;
		}
		if (value >= 1000) {
			return `${(value / 1000).toFixed(1)}K`;
		}
		return value.toString();
	}

	function getQuotaColor(percent: number): string {
		if (percent >= 90) return 'bg-red-500';
		if (percent >= 70) return 'bg-amber-500';
		return 'bg-emerald-500';
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

	<!-- Modal -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
		<div class="flex max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl">
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-slate-50/50">
				<h2 class="text-xl font-bold text-slate-800">{$t('stats.title')}</h2>
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
			<div class="flex-1 overflow-y-auto bg-slate-50/30 p-6">
				{#if loading}
					<div class="flex h-64 items-center justify-center flex-col gap-3 text-slate-500">
						<div class="h-8 w-8 animate-spin rounded-full border-4 border-indigo-600 border-t-transparent"></div>
						<span>{$t('stats.loading')}</span>
					</div>
				{:else if error}
					<div class="flex h-64 items-center justify-center rounded-xl bg-red-50 text-red-600 border border-red-100">
						{error}
					</div>
				{:else if stats}
					<div class="space-y-6">
						<!-- KPI Cards -->
						<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
							<KpiCard
								title={$t('stats.total_requests')}
								value={formatNumber(stats.total_requests)}
								trend={0}
								icon="document"
							/>
							<KpiCard
								title={$t('stats.total_chars')}
								value={formatNumber(stats.total_chars)}
								trend={0}
								icon="chart"
							/>
							<KpiCard
								title={$t('stats.cache_hit_rate')}
								value={formatPercentage(stats.cache_hit_rate)}
								trend={0}
								icon="lightning"
							/>
							<KpiCard
								title={$t('stats.est_cost')}
								value={formatCurrency(stats.total_cost_usd)}
								trend={0}
								icon="currency"
							/>
						</div>

						<!-- Charts Row -->
						<div class="grid gap-6 lg:grid-cols-2">
							<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
								<h3 class="mb-4 text-lg font-semibold text-slate-800">{$t('stats.provider_usage')}</h3>
								<div class="h-64">
									<ProviderPieChart data={stats.provider_usage} />
								</div>
							</div>
							<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
								<DailyVolumeChart data={stats.daily_trend} onRangeChange={handleRangeChange} />
							</div>
						</div>

						<!-- Quotas -->
						<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
							<h3 class="mb-4 text-lg font-semibold text-slate-800">{$t('stats.provider_quotas')}</h3>
							<div class="space-y-6">
								<!-- OpenAI -->
								<div 
									class="cursor-pointer transition-all hover:opacity-80"
									onclick={() => isOpenAIExpanded = !isOpenAIExpanded}
									role="button"
									tabindex="0"
									onkeydown={(e) => e.key === 'Enter' && (isOpenAIExpanded = !isOpenAIExpanded)}
								>
									<div class="mb-2 flex justify-between text-sm">
										<div class="flex items-center gap-2">
											<span class="font-medium text-slate-700">OpenAI API</span>
											<svg 
												class="h-4 w-4 text-slate-400 transition-transform {isOpenAIExpanded ? 'rotate-180' : ''}" 
												fill="none" 
												viewBox="0 0 24 24" 
												stroke="currentColor"
											>
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
											</svg>
										</div>
										<span class="text-slate-500">
											{formatTokens(stats.openai_tokens_input_month + stats.openai_tokens_output_month)} tokens
											<span class="ml-1 text-slate-400">({formatCurrency(stats.openai_cost_month)})</span>
										</span>
									</div>
									<div class="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
										<div
											class="h-full bg-indigo-500 transition-all duration-500"
											style="width: 100%"
										></div>
									</div>

									{#if isOpenAIExpanded}
										<div class="mt-3 grid grid-cols-2 gap-4 border-t border-slate-100 pt-3 text-xs" transition:slide>
											<div>
												<p class="font-medium text-slate-600">Input</p>
												<p class="text-slate-500">{formatTokens(stats.openai_tokens_input_month)} tokens</p>
												<p class="text-slate-400">≈ {formatCurrency(stats.openai_tokens_input_month / 1000000 * 0.15)}</p>
											</div>
											<div class="text-right">
												<p class="font-medium text-slate-600">Output</p>
												<p class="text-slate-500">{formatTokens(stats.openai_tokens_output_month)} tokens</p>
												<p class="text-slate-400">≈ {formatCurrency(stats.openai_tokens_output_month / 1000000 * 0.60)}</p>
											</div>
										</div>
									{/if}
								</div>

								<!-- DeepL -->
								<div>
									<div class="mb-2 flex justify-between text-sm">
										<span class="font-medium text-slate-700">DeepL API (Free)</span>
										<span class="text-slate-500">
											{formatNumber(stats.deepl_chars_month)} / {formatNumber(stats.deepl_quota_limit)} chars ({stats.deepl_quota_percent.toFixed(1)}%)
										</span>
									</div>
									<div class="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
										<div
											class="h-full {getQuotaColor(stats.deepl_quota_percent)} transition-all duration-500"
											style="width: {Math.min(stats.deepl_quota_percent, 100)}%"
										></div>
									</div>
								</div>

								<!-- Google -->
								<div>
									<div class="mb-2 flex justify-between text-sm">
										<span class="font-medium text-slate-700">Google Translate API</span>
										<span class="text-slate-500">
											{formatNumber(stats.google_chars_month)} / {formatNumber(stats.google_quota_limit)} chars ({stats.google_quota_percent.toFixed(1)}%)
										</span>
									</div>
									<div class="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
										<div
											class="h-full {getQuotaColor(stats.google_quota_percent)} transition-all duration-500"
											style="width: {Math.min(stats.google_quota_percent, 100)}%"
										></div>
									</div>
								</div>
							</div>
						</div>
						
						<!-- External Data (Live) -->
						<div class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
							<div class="mb-4 flex items-center justify-between">
								<h3 class="text-lg font-semibold text-slate-800">{$t('stats.external_data')}</h3>
								<span class="text-xs text-slate-500">
									{$t('stats.last_updated')}: {new Date(stats.external_data_updated_at || Date.now()).toLocaleString()}
								</span>
							</div>
							
							<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
								<!-- Exchange Rate -->
								<div class="rounded-lg bg-blue-50 p-4">
									<div class="mb-1 text-xs font-medium text-blue-600">USD / TWD</div>
									<div class="text-2xl font-bold text-blue-800">{stats.exchange_rate.toFixed(2)}</div>
								</div>

								<!-- DeepL Pricing -->
								<div class="rounded-lg bg-slate-50 p-4">
									<div class="mb-1 text-xs font-medium text-slate-600">DeepL Free Limit</div>
									<div class="text-lg font-semibold text-slate-800">{formatNumber(stats.pricing_data.deepl_free_limit)} chars</div>
								</div>

								<!-- Google Pricing -->
								<div class="rounded-lg bg-slate-50 p-4">
									<div class="mb-1 text-xs font-medium text-slate-600">Google Pricing</div>
									<div class="flex flex-col">
										<span class="text-xs text-slate-500">Free: {formatNumber(stats.pricing_data.google_free_limit)}</span>
										<span class="text-sm font-semibold text-slate-800">${stats.pricing_data.google_price_per_million_chars}/1M chars</span>
									</div>
								</div>

								<!-- OpenAI Pricing -->
								<div class="rounded-lg bg-slate-50 p-4">
									<div class="mb-1 text-xs font-medium text-slate-600">OpenAI (GPT-4o-mini)</div>
									<div class="flex flex-col">
										<span class="text-xs text-slate-500">In: ${stats.pricing_data.openai_price_input}/1M</span>
										<span class="text-xs text-slate-500">Out: ${stats.pricing_data.openai_price_output}/1M</span>
									</div>
								</div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
