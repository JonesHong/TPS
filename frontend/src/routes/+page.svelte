<script lang="ts">
	import { onMount } from 'svelte';
	import { getDashboardStats } from '$lib/api';
	import type { DashboardStats } from '$lib/types';
	import { KpiCard } from '$lib/components/dashboard';
	import { ProviderPieChart, DailyVolumeChart } from '$lib/components/charts';

	let stats: DashboardStats | null = $state(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		await loadStats();
	});

	async function loadStats() {
		loading = true;
		error = null;
		try {
			stats = await getDashboardStats();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load dashboard stats';
		} finally {
			loading = false;
		}
	}

	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 2
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
		if (percent >= 70) return 'bg-yellow-500';
		return 'bg-green-500';
	}
</script>

<svelte:head>
	<title>Dashboard - TPS</title>
</svelte:head>

<div class="space-y-6">
	{#if loading}
		<!-- Loading skeleton -->
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			{#each Array(4) as _}
				<div class="h-32 animate-pulse rounded-lg bg-gray-200"></div>
			{/each}
		</div>
		<div class="grid gap-6 lg:grid-cols-2">
			<div class="h-80 animate-pulse rounded-lg bg-gray-200"></div>
			<div class="h-80 animate-pulse rounded-lg bg-gray-200"></div>
		</div>
	{:else if error}
		<!-- Error state -->
		<div class="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
			<p class="text-red-600">{error}</p>
			<button
				class="mt-4 rounded-md bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700"
				onclick={loadStats}
			>
				Retry
			</button>
		</div>
	{:else if stats}
		<!-- KPI Cards -->
		<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			<KpiCard title="Total Translations" value={formatNumber(stats.total_requests)}>
				{#snippet icon()}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
				{/snippet}
			</KpiCard>

			<KpiCard
				title="Total Characters"
				value={formatNumber(stats.total_chars)}
				description="Translated characters"
			>
				{#snippet icon()}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10"
						/>
					</svg>
				{/snippet}
			</KpiCard>

			<KpiCard
				title="Estimated Cost"
				value={formatCurrency(stats.total_cost_usd)}
				description="This month"
			>
				{#snippet icon()}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
				{/snippet}
			</KpiCard>

			<KpiCard
				title="Cache Hit Rate"
				value={formatPercentage(stats.cache_hit_rate)}
				description="API calls saved"
			>
				{#snippet icon()}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M13 10V3L4 14h7v7l9-11h-7z"
						/>
					</svg>
				{/snippet}
			</KpiCard>
		</div>

		<!-- Charts -->
		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Provider Usage -->
			<div class="rounded-lg border bg-white p-6 shadow-sm">
				<h3 class="mb-4 text-lg font-semibold text-gray-900">Usage by Provider</h3>
				<ProviderPieChart data={stats.provider_usage} />
			</div>

			<!-- Daily Volume -->
			<div class="rounded-lg border bg-white p-6 shadow-sm">
				<h3 class="mb-4 text-lg font-semibold text-gray-900">Daily Translation Volume</h3>
				<DailyVolumeChart data={stats.daily_trend} />
			</div>
		</div>

		<!-- Provider Quota Details -->
		<div class="rounded-lg border bg-white p-6 shadow-sm">
			<h3 class="mb-4 text-lg font-semibold text-gray-900">Provider Quota Usage (This Month)</h3>
			<div class="grid gap-6 md:grid-cols-3">
				<!-- DeepL Quota -->
				<div class="space-y-3">
					<div class="flex items-center gap-2">
						<div class="h-3 w-3 rounded-full bg-blue-500"></div>
						<span class="font-medium text-gray-900">DeepL</span>
						<span class="ml-auto text-sm text-gray-500">Free Tier: 500K chars/month</span>
					</div>
					<div class="relative h-4 w-full overflow-hidden rounded-full bg-gray-200">
						<div 
							class="absolute left-0 top-0 h-full transition-all duration-300 {getQuotaColor(stats.deepl_quota_percent)}"
							style="width: {Math.min(stats.deepl_quota_percent, 100)}%"
						></div>
					</div>
					<div class="flex justify-between text-sm">
						<span class="text-gray-600">{formatNumber(stats.deepl_chars_month)} chars used</span>
						<span class="font-medium {stats.deepl_quota_percent >= 90 ? 'text-red-600' : stats.deepl_quota_percent >= 70 ? 'text-yellow-600' : 'text-green-600'}">
							{stats.deepl_quota_percent.toFixed(1)}%
						</span>
					</div>
				</div>

				<!-- Google Translate Quota -->
				<div class="space-y-3">
					<div class="flex items-center gap-2">
						<div class="h-3 w-3 rounded-full bg-green-500"></div>
						<span class="font-medium text-gray-900">Google Translate</span>
						<span class="ml-auto text-sm text-gray-500">Free Tier: 500K chars/month</span>
					</div>
					<div class="relative h-4 w-full overflow-hidden rounded-full bg-gray-200">
						<div 
							class="absolute left-0 top-0 h-full transition-all duration-300 {getQuotaColor(stats.google_quota_percent)}"
							style="width: {Math.min(stats.google_quota_percent, 100)}%"
						></div>
					</div>
					<div class="flex justify-between text-sm">
						<span class="text-gray-600">{formatNumber(stats.google_chars_month)} chars used</span>
						<span class="font-medium {stats.google_quota_percent >= 90 ? 'text-red-600' : stats.google_quota_percent >= 70 ? 'text-yellow-600' : 'text-green-600'}">
							{stats.google_quota_percent.toFixed(1)}%
						</span>
					</div>
				</div>

				<!-- OpenAI Token Usage -->
				<div class="space-y-3">
					<div class="flex items-center gap-2">
						<div class="h-3 w-3 rounded-full bg-purple-500"></div>
						<span class="font-medium text-gray-900">OpenAI (gpt-4o-mini)</span>
						<span class="ml-auto text-sm text-gray-500">Pay-as-you-go</span>
					</div>
					<div class="rounded-lg bg-purple-50 p-3">
						<div class="grid grid-cols-2 gap-2 text-sm">
							<div>
								<span class="text-gray-500">Input:</span>
								<span class="ml-1 font-medium text-gray-900">{formatTokens(stats.openai_tokens_input_month)} tokens</span>
							</div>
							<div>
								<span class="text-gray-500">Output:</span>
								<span class="ml-1 font-medium text-gray-900">{formatTokens(stats.openai_tokens_output_month)} tokens</span>
							</div>
						</div>
					</div>
					<div class="flex justify-between text-sm">
						<span class="text-gray-600">This month's cost</span>
						<span class="font-medium text-purple-600">{formatCurrency(stats.openai_cost_month)}</span>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
