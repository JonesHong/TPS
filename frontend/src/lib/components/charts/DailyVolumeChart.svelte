<script lang="ts">
	import { t } from 'svelte-i18n';

	interface DailyData {
		date: string;
		count: number;
	}

	interface Props {
		data: DailyData[];
		days?: number;
		onRangeChange?: (days: number) => void;
	}

	let { data, days = 7, onRangeChange }: Props = $props();
	
	// Use $derived to keep selectedRange in sync with the days prop
	let selectedRange = $derived(days);

	// Find the maximum value for scaling
	let maxCount = $derived(Math.max(...data.map((d) => d.count), 5));

	// Format date for display
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
	}

	function handleRangeChange(newDays: number) {
		onRangeChange?.(newDays);
	}
</script>

<div class="flex flex-col h-80">
	<!-- Header with controls -->
	<div class="flex items-center justify-between mb-4">
		<div class="flex items-center gap-2">
			<h3 class="text-sm font-medium text-gray-700">
				{$t('stats.daily_volume')}
				<span class="font-normal text-gray-500">
					({days === 90 ? $t('stats.days_90') : days === 30 ? $t('stats.days_30') : $t('stats.days_7')})
				</span>
			</h3>
			<span class="text-xs text-gray-500">({$t('stats.unit_translations')})</span>
		</div>
		<div class="flex rounded-lg bg-gray-100 p-1">
			{#each [7, 30, 90] as days}
				<button
					class="rounded px-3 py-1 text-xs font-medium transition-colors {selectedRange === days
						? 'bg-white text-primary-600 shadow-sm'
						: 'text-gray-500 hover:text-gray-700'}"
					onclick={() => handleRangeChange(days)}
				>
					{days === 90 ? $t('stats.days_90') : days === 30 ? $t('stats.days_30') : $t('stats.days_7')}
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
							<div class="group relative flex flex-1 h-full flex-col items-center justify-end">
								<!-- Bar label on top -->
								<div class="text-xs text-gray-600 font-medium mb-1">
									{item.count > 0 ? item.count : ''}
								</div>
								
								<!-- Bar -->
								<div 
									class="w-full max-w-[40px] rounded-t bg-blue-500 transition-all duration-300 hover:bg-blue-600 cursor-pointer"
									style="height: {Math.max(heightPercent, item.count > 0 ? 5 : 0)}%"
									title="{formatDate(item.date)}: {item.count} 次翻譯"
								></div>
							</div>
						{/each}
					</div>
					
					<!-- X-axis labels -->
					<div class="flex gap-1 pl-2 pt-2">
						{#each data as item, i}
							<div class="flex-1 relative h-6">
								{#if data.length <= 7 || (selectedRange === 7) || (selectedRange === 30 && i % 5 === 0) || (selectedRange === 90 && i % 15 === 0) || i === data.length - 1}
									<div class="absolute left-1/2 -translate-x-1/2 text-xs text-gray-500 whitespace-nowrap">
										{formatDate(item.date)}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
