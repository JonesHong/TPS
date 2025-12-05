<script lang="ts">
	interface DailyData {
		date: string;
		count: number;
	}

	interface Props {
		data: DailyData[];
	}

	let { data }: Props = $props();

	// Find the maximum value for scaling
	let maxCount = $derived(Math.max(...data.map((d) => d.count), 1));

	// Format date for display
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
	}
</script>

<div class="h-64">
	{#if data.length === 0}
		<div class="flex h-full items-center justify-center text-gray-500">
			No data available
		</div>
	{:else}
		<div class="flex h-full flex-col">
			<!-- Chart area -->
			<div class="flex flex-1 items-end gap-2">
				{#each data as item}
					{@const heightPercent = (item.count / maxCount) * 100}
					<div class="flex flex-1 flex-col items-center gap-1">
						<!-- Bar -->
						<div class="relative w-full px-1">
							<div
								class="mx-auto w-full max-w-12 rounded-t bg-primary-500 transition-all duration-300 hover:bg-primary-600"
								style="height: {Math.max(heightPercent, 2)}%"
								title="{formatDate(item.date)}: {item.count.toLocaleString()} translations"
							></div>
						</div>
						<!-- Value label -->
						<span class="text-xs font-medium text-gray-700">
							{item.count > 999 ? `${(item.count / 1000).toFixed(1)}k` : item.count}
						</span>
					</div>
				{/each}
			</div>
			<!-- X-axis labels -->
			<div class="mt-2 flex gap-2 border-t pt-2">
				{#each data as item}
					<div class="flex-1 text-center text-xs text-gray-500">
						{formatDate(item.date)}
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>
