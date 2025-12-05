<script lang="ts">
	import type { TranslationItem } from '$lib/types';
	import { Badge } from '$lib/components/ui';
	import { t } from 'svelte-i18n';

	interface Props {
		items: TranslationItem[];
		onSelect?: (item: TranslationItem) => void;
	}

	let { items, onSelect }: Props = $props();

	const providerColors: Record<string, { bg: string; text: string }> = {
		cache: { bg: 'bg-emerald-100', text: 'text-emerald-800' },
		deepl: { bg: 'bg-indigo-100', text: 'text-indigo-800' },
		openai: { bg: 'bg-purple-100', text: 'text-purple-800' },
		google: { bg: 'bg-blue-100', text: 'text-blue-800' }
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
		<thead class="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500 font-semibold tracking-wider">
			<tr>
				<th class="px-6 py-4">{$t('history.columns.time')}</th>
				<th class="px-6 py-4">{$t('history.columns.languages')}</th>
				<th class="px-6 py-4">{$t('history.columns.original')}</th>
				<th class="px-6 py-4">{$t('history.columns.translated')}</th>
				<th class="px-6 py-4">{$t('history.columns.provider')}</th>
				<th class="px-6 py-4 text-right">{$t('history.columns.actions')}</th>
			</tr>
		</thead>
		<tbody class="divide-y divide-slate-100">
			{#if items.length === 0}
				<tr>
					<td colspan="6" class="px-6 py-12 text-center text-slate-400">
						{$t('history.empty')}
					</td>
				</tr>
			{:else}
				{#each items as item}
					{@const isExpanded = expandedRows.has(item.id)}
					{@const colors = providerColors[item.provider] || { bg: 'bg-slate-100', text: 'text-slate-800' }}
					<tr
						class="cursor-pointer transition-colors hover:bg-slate-50/80"
						onclick={() => toggleRow(item.id)}
					>
						<td class="whitespace-nowrap px-6 py-4 text-slate-500">
							{formatDate(item.created_at)}
						</td>
						<td class="px-6 py-4">
							<div class="flex items-center gap-2">
								<Badge variant="outline" class="border-slate-200 text-slate-600">{item.source_lang}</Badge>
								<span class="text-slate-300">→</span>
								<Badge variant="outline" class="border-slate-200 text-slate-600">{item.target_lang}</Badge>
							</div>
						</td>
						<td class="max-w-[200px] px-6 py-4">
							<div class="break-words text-slate-700 {isExpanded ? '' : 'line-clamp-2'}">
								{isExpanded ? item.original_text : truncateText(item.original_text)}
							</div>
						</td>
						<td class="max-w-[200px] px-6 py-4">
							<div class="break-words text-slate-700 {isExpanded ? '' : 'line-clamp-2'}">
								{isExpanded ? item.translated_text : truncateText(item.translated_text)}
							</div>
						</td>
						<td class="px-6 py-4">
							<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium {colors.bg} {colors.text}">
								{item.provider}
							</span>
						</td>
						<td class="px-6 py-4 text-right">
							<div class="flex items-center justify-end gap-2">
								{#if item.is_refined}
									<span class="text-purple-600 mr-2 bg-purple-50 rounded-full p-1" title={$t('translate.refined')}>
										<svg class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
										</svg>
									</span>
								{/if}
								{#if onSelect}
									<button 
										class="rounded-lg p-2 text-indigo-600 hover:bg-indigo-50 transition-colors"
										onclick={(e) => { e.stopPropagation(); onSelect(item); }}
										title={$t('history.load')}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
										</svg>
									</button>
								{/if}
							</div>
						</td>
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
