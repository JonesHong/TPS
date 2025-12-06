<script lang="ts">
	import type { PaginationMeta } from '$lib/types';
	import { t } from 'svelte-i18n';

	interface Props {
		meta: PaginationMeta;
		onPageChange: (page: number) => void;
		onPageSizeChange?: (pageSize: number) => void;
	}

	let { meta, onPageChange, onPageSizeChange }: Props = $props();

	const pageSizeOptions = [10, 20, 50, 100];

	function goToPage(page: number) {
		if (page >= 1 && page <= meta.total_pages) {
			onPageChange(page);
		}
	}

	function handlePageSizeChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		onPageSizeChange?.(parseInt(target.value, 10));
	}
</script>

<div class="flex flex-col items-center justify-between gap-4 sm:flex-row">
	<!-- Page size selector -->
	<div class="flex items-center gap-2 text-sm text-gray-600">
		<span>{$t('pagination.show')}</span>
		<select
			class="rounded border border-gray-300 px-2 py-1 text-sm"
			value={meta.page_size}
			onchange={handlePageSizeChange}
		>
			{#each pageSizeOptions as size}
				<option value={size}>{size}</option>
			{/each}
		</select>
		<span>{$t('pagination.per_page')}</span>
	</div>

	<!-- Page info -->
	<div class="text-sm text-gray-600">
		{$t('pagination.page', { values: { page: meta.page, total_pages: meta.total_pages, total: meta.total } })}
	</div>

	<!-- Navigation buttons -->
	<div class="flex items-center gap-1">
		<button
			class="rounded border border-gray-300 px-2 py-1 text-xs transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={meta.page <= 1}
			onclick={() => goToPage(1)}
		>
			{$t('pagination.first')}
		</button>
		<button
			class="rounded border border-gray-300 px-2 py-1 text-xs transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={meta.page <= 1}
			onclick={() => goToPage(meta.page - 1)}
		>
			{$t('pagination.prev')}
		</button>
		
		<!-- Page numbers -->
		<div class="hidden items-center gap-1 sm:flex">
			{#each Array.from({ length: Math.min(5, meta.total_pages) }, (_, i) => {
				const start = Math.max(1, Math.min(meta.page - 2, meta.total_pages - 4));
				return start + i;
			}).filter(p => p <= meta.total_pages) as pageNum}
				<button
					class="h-7 w-7 rounded text-xs transition-colors {pageNum === meta.page
						? 'bg-primary-600 text-white'
						: 'border border-gray-300 hover:bg-gray-100'}"
					onclick={() => goToPage(pageNum)}
				>
					{pageNum}
				</button>
			{/each}
		</div>

		<button
			class="rounded border border-gray-300 px-2 py-1 text-xs transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={meta.page >= meta.total_pages}
			onclick={() => goToPage(meta.page + 1)}
		>
			{$t('pagination.next')}
		</button>
		<button
			class="rounded border border-gray-300 px-2 py-1 text-xs transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
			disabled={meta.page >= meta.total_pages}
			onclick={() => goToPage(meta.total_pages)}
		>
			{$t('pagination.last')}
		</button>
	</div>
</div>
