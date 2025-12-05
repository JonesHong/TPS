<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		value: string | number;
		description?: string;
		icon?: Snippet;
		trend?: {
			value: number;
			isPositive: boolean;
		};
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
			{#if trend}
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
			<div class="rounded-full bg-primary-50 p-3 text-primary-600">
				{@render icon()}
			</div>
		{/if}
	</div>
</div>
