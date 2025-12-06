<script lang="ts">
	import type { TranslationItem } from '$lib/types';
	import { Badge } from '$lib/components/ui';
	import { t } from 'svelte-i18n';

	interface Props {
		items: TranslationItem[];
		onSelect?: (item: TranslationItem) => void;
		onSort?: (field: string, direction: 'asc' | 'desc') => void;
		onDelete?: (item: TranslationItem) => Promise<void>;
		onUpdate?: (item: TranslationItem, newTranslated: string, newRefined?: string) => Promise<void>;
		onRefine?: (item: TranslationItem) => Promise<void>;
	}

	let { items, onSelect, onSort, onDelete, onUpdate, onRefine }: Props = $props();

	const providerColors: Record<string, { bg: string; text: string }> = {
		cache: { bg: 'bg-emerald-100', text: 'text-emerald-800' },
		deepl: { bg: 'bg-indigo-100', text: 'text-indigo-800' },
		openai: { bg: 'bg-purple-100', text: 'text-purple-800' },
		google: { bg: 'bg-blue-100', text: 'text-blue-800' }
	};

	// Sorting state
	let sortField = $state<string>('created_at');
	let sortDirection = $state<'asc' | 'desc'>('desc');

	// Editing state
	let editingItem = $state<TranslationItem | null>(null);
	let editTranslated = $state('');
	let editRefined = $state('');
	let isSubmitting = $state(false);

	// Column widths (in pixels)
	let columnWidths = $state<Record<string, number>>({
		time: 140,
		languages: 100,
		original: 180,
		translated: 180,
		refined: 180,
		provider: 80,
		actions: 120
	});

	// Resizing state
	let isResizing = $state(false);
	let resizingColumn = $state<string | null>(null);
	let startX = $state(0);
	let startWidth = $state(0);

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
	let expandedRows = $state<Set<string>>(new Set());

	function toggleRow(key: string) {
		if (expandedRows.has(key)) {
			expandedRows.delete(key);
			expandedRows = new Set(expandedRows);
		} else {
			expandedRows.add(key);
			expandedRows = new Set(expandedRows);
		}
	}

	function handleSort(field: string) {
		if (sortField === field) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortField = field;
			sortDirection = 'desc';
		}
		onSort?.(field, sortDirection);
	}

	function startResize(e: MouseEvent, column: string) {
		e.preventDefault();
		e.stopPropagation();
		isResizing = true;
		resizingColumn = column;
		startX = e.clientX;
		startWidth = columnWidths[column];
		
		document.addEventListener('mousemove', handleResize);
		document.addEventListener('mouseup', stopResize);
	}

	function handleResize(e: MouseEvent) {
		if (!isResizing || !resizingColumn) return;
		
		const diff = e.clientX - startX;
		const newWidth = Math.max(60, startWidth + diff);
		columnWidths[resizingColumn] = newWidth;
	}

	function stopResize() {
		isResizing = false;
		resizingColumn = null;
		document.removeEventListener('mousemove', handleResize);
		document.removeEventListener('mouseup', stopResize);
	}

	function openEdit(item: TranslationItem, e: Event) {
		e.stopPropagation();
		editingItem = item;
		editTranslated = item.translated_text;
		editRefined = item.refined_text || '';
	}

	async function saveEdit() {
		if (!editingItem || !onUpdate) return;
		isSubmitting = true;
		try {
			await onUpdate(editingItem, editTranslated, editRefined || undefined);
			editingItem = null;
		} finally {
			isSubmitting = false;
		}
	}

	async function handleDelete(item: TranslationItem, e: Event) {
		e.stopPropagation();
		if (!confirm($t('history.confirm_delete'))) return;
		if (onDelete) await onDelete(item);
	}

	async function handleRefine(item: TranslationItem, e: Event) {
		e.stopPropagation();
		if (onRefine) await onRefine(item);
	}

	// Sorted items (client-side sorting)
	let sortedItems = $derived(() => {
		return [...items].sort((a, b) => {
			let aVal: any, bVal: any;
			
			switch (sortField) {
				case 'created_at':
					aVal = new Date(a.created_at).getTime();
					bVal = new Date(b.created_at).getTime();
					break;
				case 'source_lang':
					aVal = a.source_lang;
					bVal = b.source_lang;
					break;
				case 'target_lang':
					aVal = a.target_lang;
					bVal = b.target_lang;
					break;
				case 'provider':
					aVal = a.provider;
					bVal = b.provider;
					break;
				case 'original_text':
					aVal = a.original_text;
					bVal = b.original_text;
					break;
				case 'translated_text':
					aVal = a.translated_text;
					bVal = b.translated_text;
					break;
				default:
					return 0;
			}
			
			if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
			if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		});
	});

	const columns = [
		{ key: 'time', field: 'created_at', sortable: true },
		{ key: 'languages', field: 'source_lang', sortable: true },
		{ key: 'original', field: 'original_text', sortable: true },
		{ key: 'translated', field: 'translated_text', sortable: true },
		{ key: 'refined', field: 'refined_text', sortable: false },
		{ key: 'provider', field: 'provider', sortable: true },
		{ key: 'actions', field: null, sortable: false }
	];
</script>

<div class="overflow-x-auto select-none" class:cursor-col-resize={isResizing}>
	<table class="w-full text-left text-sm" style="min-width: {Object.values(columnWidths).reduce((a, b) => a + b, 0)}px; table-layout: fixed;">
		<thead class="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500 font-semibold tracking-wider">
			<tr>
				{#each columns as col}
					<th 
						class="relative px-3 py-3 {col.sortable ? 'cursor-pointer hover:bg-slate-100' : ''} {col.key === 'actions' ? 'text-right' : ''}"
						style="width: {columnWidths[col.key]}px;"
						onclick={() => col.sortable && col.field && handleSort(col.field)}
					>
						<div class="flex items-center gap-1 {col.key === 'actions' ? 'justify-end' : ''}">
							<span>{$t(`history.columns.${col.key}`)}</span>
							{#if col.sortable && col.field}
								<span class="inline-flex flex-col text-[8px] leading-none">
									<svg 
										class="h-2 w-2 {sortField === col.field && sortDirection === 'asc' ? 'text-indigo-600' : 'text-slate-300'}" 
										fill="currentColor" 
										viewBox="0 0 20 20"
									>
										<path d="M10 3l7 7H3l7-7z"/>
									</svg>
									<svg 
										class="h-2 w-2 {sortField === col.field && sortDirection === 'desc' ? 'text-indigo-600' : 'text-slate-300'}" 
										fill="currentColor" 
										viewBox="0 0 20 20"
									>
										<path d="M10 17l-7-7h14l-7 7z"/>
									</svg>
								</span>
							{/if}
						</div>
						<!-- Resize handle -->
						{#if col.key !== 'actions'}
							<div 
								class="absolute right-0 top-0 h-full w-1 cursor-col-resize bg-transparent hover:bg-indigo-400 transition-colors"
								onmousedown={(e) => startResize(e, col.key)}
							></div>
						{/if}
					</th>
				{/each}
			</tr>
		</thead>
		<tbody class="divide-y divide-slate-100">
			{#if items.length === 0}
				<tr>
					<td colspan="7" class="px-6 py-12 text-center text-slate-400">
						{$t('history.empty')}
					</td>
				</tr>
			{:else}
				{#each sortedItems() as item}
					{@const isExpanded = expandedRows.has(item.cache_key)}
					{@const colors = providerColors[item.provider] || { bg: 'bg-slate-100', text: 'text-slate-800' }}
					<tr
						class="cursor-pointer transition-colors hover:bg-slate-50/80"
						onclick={() => toggleRow(item.cache_key)}
					>
						<td class="whitespace-nowrap px-3 py-3 text-slate-500 text-xs overflow-hidden text-ellipsis" style="width: {columnWidths.time}px;">
							{formatDate(item.created_at)}
						</td>
						<td class="px-3 py-3 overflow-hidden" style="width: {columnWidths.languages}px;">
							<div class="flex items-center gap-1">
								<Badge variant="outline" class="border-slate-200 text-slate-600 text-xs">{item.source_lang}</Badge>
								<span class="text-slate-300">→</span>
								<Badge variant="outline" class="border-slate-200 text-slate-600 text-xs">{item.target_lang}</Badge>
							</div>
						</td>
						<td class="px-3 py-3 overflow-hidden" style="width: {columnWidths.original}px;">
							<div class="break-words text-slate-700 {isExpanded ? '' : 'line-clamp-2'} text-xs">
								{isExpanded ? item.original_text : truncateText(item.original_text, 40)}
							</div>
						</td>
						<td class="px-3 py-3 overflow-hidden" style="width: {columnWidths.translated}px;">
							<div class="break-words text-slate-700 {isExpanded ? '' : 'line-clamp-2'} text-xs">
								{isExpanded ? item.translated_text : truncateText(item.translated_text, 40)}
							</div>
						</td>
						<td class="px-3 py-3 overflow-hidden" style="width: {columnWidths.refined}px;">
							{#if item.refined_text}
								<div class="break-words text-purple-700 {isExpanded ? '' : 'line-clamp-2'} text-xs">
									{isExpanded ? item.refined_text : truncateText(item.refined_text, 40)}
								</div>
							{:else}
								<span class="text-slate-300 text-xs">{$t('history.no_refinement')}</span>
							{/if}
						</td>
						<td class="px-3 py-3" style="width: {columnWidths.provider}px;">
							<span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {colors.bg} {colors.text}">
								{item.provider}
							</span>
						</td>
						<td class="px-3 py-3 text-right" style="width: {columnWidths.actions}px;">
							<div class="flex items-center justify-end gap-1">
								{#if onRefine && !item.is_refined}
									<button 
										class="rounded-lg p-1.5 text-purple-600 hover:bg-purple-50 transition-colors"
										onclick={(e) => handleRefine(item, e)}
										title={$t('history.refine')}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
										</svg>
									</button>
								{/if}
								{#if onUpdate}
									<button 
										class="rounded-lg p-1.5 text-blue-600 hover:bg-blue-50 transition-colors"
										onclick={(e) => openEdit(item, e)}
										title={$t('history.edit')}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
										</svg>
									</button>
								{/if}
								{#if onDelete}
									<button 
										class="rounded-lg p-1.5 text-red-600 hover:bg-red-50 transition-colors"
										onclick={(e) => handleDelete(item, e)}
										title={$t('history.delete')}
									>
										<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
										</svg>
									</button>
								{/if}
								{#if onSelect}
									<button 
										class="rounded-lg p-1.5 text-indigo-600 hover:bg-indigo-50 transition-colors"
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

{#if editingItem}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onclick={() => editingItem = null}>
		<div class="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl" onclick={(e) => e.stopPropagation()}>
			<h3 class="mb-4 text-lg font-semibold text-slate-900">{$t('history.edit_title')}</h3>
			
			<div class="mb-4">
				<label class="mb-1 block text-sm font-medium text-slate-700">{$t('history.original')}</label>
				<div class="rounded-lg bg-slate-50 p-3 text-sm text-slate-600 max-h-32 overflow-y-auto">
					{editingItem.original_text}
				</div>
			</div>

			<div class="mb-4">
				<label class="mb-1 block text-sm font-medium text-slate-700">{$t('history.translated')}</label>
				<textarea
					bind:value={editTranslated}
					class="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
					rows="4"
				></textarea>
			</div>

			<div class="mb-6">
				<label class="mb-1 block text-sm font-medium text-slate-700">{$t('history.refined')}</label>
				<textarea
					bind:value={editRefined}
					class="w-full rounded-lg border border-slate-300 p-3 text-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
					rows="4"
					placeholder={$t('history.no_refinement')}
				></textarea>
			</div>

			<div class="flex justify-end gap-3">
				<button
					class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
					onclick={() => editingItem = null}
					disabled={isSubmitting}
				>
					{$t('common.cancel')}
				</button>
				<button
					class="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
					onclick={saveEdit}
					disabled={isSubmitting}
				>
					{isSubmitting ? $t('common.saving') : $t('common.save')}
				</button>
			</div>
		</div>
	</div>
{/if}
