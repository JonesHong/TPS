<script lang="ts">
	interface Props {
		data: Record<string, number>;
	}

	let { data }: Props = $props();

	const colors: Record<string, string> = {
		cache: '#10b981', // green
		deepl: '#3b82f6', // blue
		openai: '#8b5cf6', // purple
		google: '#f59e0b' // amber
	};

	const labels: Record<string, string> = {
		cache: 'Cache',
		deepl: 'DeepL',
		openai: 'OpenAI',
		google: 'Google'
	};

	// Calculate total and percentages
	let total = $derived(Object.values(data).reduce((sum, val) => sum + val, 0));
	let segments = $derived(
		Object.entries(data)
			.filter(([_, value]) => value > 0)
			.map(([key, value]) => ({
				key,
				value,
				percentage: total > 0 ? (value / total) * 100 : 0,
				color: colors[key] || '#6b7280'
			}))
	);

	// Calculate cumulative percentages for conic gradient
	let conicGradient = $derived(() => {
		if (segments.length === 0) return 'conic-gradient(#e5e7eb 0deg 360deg)';
		
		let accumulated = 0;
		const gradientStops = segments.flatMap((segment) => {
			const start = accumulated;
			accumulated += segment.percentage;
			return [`${segment.color} ${start}%`, `${segment.color} ${accumulated}%`];
		});
		return `conic-gradient(${gradientStops.join(', ')})`;
	});
</script>

<div class="flex flex-col items-center gap-4 lg:flex-row lg:items-start lg:gap-8">
	<!-- Pie Chart -->
	<div class="relative h-48 w-48 flex-shrink-0">
		<div
			class="h-full w-full rounded-full"
			style="background: {conicGradient()}"
		></div>
		<div
			class="absolute left-1/2 top-1/2 flex h-24 w-24 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white"
		>
			<div class="text-center">
				<div class="text-2xl font-bold text-gray-900">{total.toLocaleString()}</div>
				<div class="text-xs text-gray-500">Total</div>
			</div>
		</div>
	</div>

	<!-- Legend -->
	<div class="flex flex-wrap justify-center gap-4 lg:flex-col lg:gap-2">
		{#each segments as segment}
			<div class="flex items-center gap-2">
				<div class="h-3 w-3 rounded-full" style="background-color: {segment.color}"></div>
				<span class="text-sm text-gray-700">
					{labels[segment.key] || segment.key}
				</span>
				<span class="text-sm font-medium text-gray-900">
					{segment.value.toLocaleString()}
				</span>
				<span class="text-xs text-gray-500">
					({segment.percentage.toFixed(1)}%)
				</span>
			</div>
		{/each}
	</div>
</div>
