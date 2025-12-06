<script lang="ts">
	interface DailyData {
		date: string;
		count: number;
	}

	interface Props {
		data: DailyData[];
		onRangeChange?: (days: number) => void;
	}

	let { data, onRangeChange }: Props = $props();
	let selectedRange = $state(7);

	// Find the maximum value for scaling
	let maxCount = $derived(Math.max(...data.map((d) => d.count), 1));

	// Format date for display
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
	}

	function handleRangeChange(days: number) {
		selectedRange = days;
		onRangeChange?.(days);
	}
</script>

<div class="flex flex-col h-80">
	<!-- Header with controls -->
	<div class="flex items-center justify-between mb-4">
		<div class="flex items-center gap-2">
			<h3 class="text-sm font-medium text-gray-700">Daily Volume</h3>
			<span class="text-xs text-gray-500">(Translations)</span>
		</div>
		<div class="flex rounded-lg bg-gray-100 p-1">
			{#each [7, 30, 90] as days}
				<button
					class="rounded px-3 py-1 text-xs font-medium transition-colors {selectedRange === days
						? 'bg-white text-primary-600 shadow-sm'
						: 'text-gray-500 hover:text-gray-700'}"
					onclick={() => handleRangeChange(days)}
				>
					{days === 90 ? '3M' : `${days}D`}
				</button>
			{/each}
		</div>
	</div>

	<div class="relative flex-1">
		{#if data.length === 0}
			<div class="flex h-full items-center justify-center text-gray-500">
				No data available
			</div>
		{:else}
			<div class="flex h-full">
				<!-- Y-axis labels -->
				<div class="flex flex-col justify-between py-6 pr-2 text-xs text-gray-400 w-12 text-right">
					<span>{maxCount > 999 ? `${(maxCount / 1000).toFixed(1)}k` : maxCount}</span>
					<span>{maxCount > 1 ? (maxCount > 1998 ? `${(maxCount / 2000).toFixed(1)}k` : Math.round(maxCount / 2)) : ''}</span>
					<span>0</span>
				</div>

				<!-- Chart area -->
				<div class="flex flex-1 flex-col">
					<div class="flex flex-1 items-end gap-1 border-l border-b border-gray-200 pl-2 pb-2">
						{#each data as item}
							{@const heightPercent = (item.count / maxCount) * 100}
							<div class="group relative flex flex-1 flex-col items-center">
								<!-- Tooltip -->
								<div class="absolute bottom-full mb-2 hidden flex-col items-center whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:flex group-hover:opacity-100 z-10">
									<span class="font-bold">{item.count.toLocaleString()}</span>
									<span class="text-gray-300">{formatDate(item.date)}</span>
									<!-- Arrow -->
									<div class="absolute top-full h-0 w-0 border-4 border-transparent border-t-gray-800"></div>
								</div>
								
								<!-- Bar -->
								<div class="relative w-full px-0.5 h-full flex items-end">
									<div
										class="w-full rounded-t bg-primary-500 transition-all duration-300 hover:bg-primary-600"
										style="height: {Math.max(heightPercent, 2)}%"
									></div>
								</div>
							</div>
						{/each}
					</div>
					
					<!-- X-axis labels -->
					<div class="flex gap-1 pl-14 pt-2">
						{#each data.filter((_, i, arr) => {
							// Show fewer labels for longer ranges
							if (selectedRange === 7) return true;
							if (selectedRange === 30) return i % 5 === 0;
							return i % 15 === 0;
						}) as item}
							<div class="flex-1 text-center text-xs text-gray-500 truncate">
								{formatDate(item.date)}
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
