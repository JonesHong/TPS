<script lang="ts">
	import type { TranslationItem } from '$lib/types';
	import { Badge } from '$lib/components/ui';

	interface Props {
		items: TranslationItem[];
	}

	let { items }: Props = $props();

	const providerColors: Record<string, { bg: string; text: string }> = {
		cache: { bg: 'bg-green-100', text: 'text-green-800' },
		deepl: { bg: 'bg-blue-100', text: 'text-blue-800' },
		openai: { bg: 'bg-purple-100', text: 'text-purple-800' },
		google: { bg: 'bg-amber-100', text: 'text-amber-800' }
	};

	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleString('zh-TW', {
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function truncateText(text: string, maxLength: number = 50): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	// Track expanded rows
	let expandedRows = $state<Set<number>>(new Set());

	function toggleRow(id: number) {
		if (expandedRows.has(id)) {
			expandedRows.delete(id);
			expandedRows = new Set(expandedRows);
		} else {
			expandedRows.add(id);
			expandedRows = new Set(expandedRows);
		}
	}
</script>

<div class="overflow-x-auto">
	<table class="w-full min-w-[800px] text-left text-sm">
		<thead class="border-b bg-gray-50 text-xs uppercase text-gray-700">
			<tr>
				<th class="px-4 py-3">Time</th>
				<th class="px-4 py-3">Languages</th>
				<th class="px-4 py-3">Original Text</th>
				<th class="px-4 py-3">Translated Text</th>
				<th class="px-4 py-3">Provider</th>
				<th class="px-4 py-3">Refined</th>
			</tr>
		</thead>
		<tbody>
			{#if items.length === 0}
				<tr>
					<td colspan="6" class="px-4 py-8 text-center text-gray-500">
						No translations found
					</td>
				</tr>
			{:else}
				{#each items as item}
					{@const isExpanded = expandedRows.has(item.id)}
					{@const colors = providerColors[item.provider] || { bg: 'bg-gray-100', text: 'text-gray-800' }}
					<tr
						class="cursor-pointer border-b transition-colors hover:bg-gray-50"
						onclick={() => toggleRow(item.id)}
					>
						<td class="whitespace-nowrap px-4 py-3 text-gray-600">
							{formatDate(item.created_at)}
						</td>
						<td class="px-4 py-3">
							<div class="flex items-center gap-1">
								<Badge variant="outline">{item.source_lang}</Badge>
								<span class="text-gray-400">→</span>
								<Badge variant="outline">{item.target_lang}</Badge>
							</div>
						</td>
						<td class="max-w-[200px] px-4 py-3">
							<div class="break-words {isExpanded ? '' : 'line-clamp-2'}">
								{isExpanded ? item.original_text : truncateText(item.original_text)}
							</div>
						</td>
						<td class="max-w-[200px] px-4 py-3">
							<div class="break-words {isExpanded ? '' : 'line-clamp-2'}">
								{isExpanded ? item.translated_text : truncateText(item.translated_text)}
							</div>
						</td>
						<td class="px-4 py-3">
							<span class="inline-flex rounded-full px-2 py-1 text-xs font-medium {colors.bg} {colors.text}">
								{item.provider}
							</span>
						</td>
						<td class="px-4 py-3 text-center">
							{#if item.is_refined}
								<span class="text-green-600" title="Refined">✓</span>
							{:else}
								<span class="text-gray-400">—</span>
							{/if}
						</td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
