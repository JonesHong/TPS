<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		value: string | number;
		description?: string;
		icon?: string | Snippet;
		trend?: {
			value: number;
			isPositive: boolean;
		} | number;
	}

	let { title, value, description, icon, trend }: Props = $props();
</script>

<div class="rounded-lg border bg-white p-6 shadow-sm">
	<div class="flex items-center justify-between">
		<div>
			<p class="text-sm font-medium text-gray-500">{title}</p>
			<p class="mt-1 text-3xl font-semibold text-gray-900">{value}</p>
			{#if description}
				<p class="mt-1 text-sm text-gray-500">{description}</p>
			{/if}
			{#if trend && typeof trend === 'object'}
				<p
					class="mt-2 flex items-center text-sm {trend.isPositive
						? 'text-green-600'
						: 'text-red-600'}"
				>
					{#if trend.isPositive}
						<svg class="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M5 10l7-7m0 0l7 7m-7-7v18"
							/>
						</svg>
					{:else}
						<svg class="mr-1 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M19 14l-7 7m0 0l-7-7m7 7V3"
							/>
						</svg>
					{/if}
					{Math.abs(trend.value)}%
				</p>
			{/if}
		</div>
		{#if icon}
			<div class="rounded-full bg-indigo-50 p-3 text-indigo-600">
				{#if typeof icon === 'string'}
					{#if icon === 'document'}
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
						</svg>
					{:else if icon === 'chart'}
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
						</svg>
					{:else if icon === 'lightning'}
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
					{:else if icon === 'currency'}
						<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
					{/if}
				{:else}
					{@render icon()}
				{/if}
			</div>
		{/if}
	</div>
</div>
