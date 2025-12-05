<script lang="ts">
	import { t } from 'svelte-i18n';
	import { fade, fly } from 'svelte/transition';
	import { translateFile } from '$lib/api/translations';
	import type { TranslateResponse } from '$lib/types';

	// Types
	interface FileItem {
		id: string;
		file: File;
		status: 'pending' | 'uploading' | 'translating' | 'completed' | 'error';
		progress: number;
		result?: string;
		error?: string;
	}

	// State
	let files = $state<FileItem[]>([]);
	let isDragging = $state(false);
	let targetLang = $state('zh-TW');
	let sourceLang = $state('');
	let preferredProvider = $state('auto');
	let enableRefinement = $state(false);
	let fileInput: HTMLInputElement;

	// Handlers
	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		isDragging = true;
	}

	function handleDragLeave() {
		isDragging = false;
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		isDragging = false;
		if (e.dataTransfer?.files) {
			addFiles(e.dataTransfer.files);
		}
	}

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (target.files) {
			addFiles(target.files);
		}
	}

	function addFiles(fileList: FileList) {
		const newFiles = Array.from(fileList).map((file) => ({
			id: Math.random().toString(36).substring(7),
			file,
			status: 'pending' as const,
			progress: 0
		}));
		files = [...files, ...newFiles];
	}

	function removeFile(id: string) {
		files = files.filter((f) => f.id !== id);
	}

	function clearAll() {
		files = [];
	}

	async function translateAll() {
		const pendingFiles = files.filter((f) => f.status === 'pending' || f.status === 'error');
		
		for (const item of pendingFiles) {
			await processFile(item);
		}
	}

	async function processFile(item: FileItem) {
		// Update status to uploading
		const index = files.findIndex((f) => f.id === item.id);
		if (index === -1) return;
		
		files[index].status = 'translating';
		files[index].progress = 20; // Fake progress start

		try {
			// Simulate progress
			const progressInterval = setInterval(() => {
				if (files[index].progress < 90) {
					files[index].progress += 10;
				}
			}, 500);

			const response = await translateFile(
				item.file,
				targetLang,
				sourceLang || undefined,
				enableRefinement,
				preferredProvider === 'auto' ? undefined : preferredProvider
			);

			clearInterval(progressInterval);

			if (response.success && response.data) {
				files[index].status = 'completed';
				files[index].progress = 100;
				files[index].result = response.data.text;
			} else {
				throw new Error(response.error || 'Translation failed');
			}
		} catch (e) {
			files[index].status = 'error';
			files[index].error = e instanceof Error ? e.message : 'Unknown error';
		}
	}

	function downloadFile(item: FileItem) {
		if (!item.result) return;
		
		const blob = new Blob([item.result], { type: 'text/plain;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `translated_${item.file.name}`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	}

	function formatSize(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
</script>

<div class="flex h-full flex-col gap-6 p-6 md:p-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-slate-800">{$t('files.title')}</h1>
			<p class="mt-1 text-slate-500">Upload documents to translate them while preserving formatting.</p>
		</div>
		<div class="flex gap-3">
			<button
				class="rounded-xl px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 transition-colors"
				onclick={clearAll}
				disabled={files.length === 0}
			>
				{$t('files.clear_all')}
			</button>
			<button
				class="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
				onclick={translateAll}
				disabled={files.filter(f => f.status === 'pending' || f.status === 'error').length === 0}
			>
				<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				{$t('files.translate_all')}
			</button>
		</div>
	</div>

	<!-- Settings Bar -->
	<div class="grid gap-4 rounded-2xl bg-white p-4 shadow-sm sm:grid-cols-4">
		<!-- Source Lang -->
		<div class="flex flex-col gap-1.5">
			<label class="text-xs font-medium text-slate-500">{$t('translate.from')}</label>
			<select
				bind:value={sourceLang}
				class="rounded-lg border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:border-indigo-500 focus:ring-indigo-500"
			>
				<option value="">{$t('common.auto_detect')}</option>
				<option value="en">English</option>
				<option value="zh-TW">Traditional Chinese</option>
				<option value="ja">Japanese</option>
				<option value="ko">Korean</option>
			</select>
		</div>

		<!-- Target Lang -->
		<div class="flex flex-col gap-1.5">
			<label class="text-xs font-medium text-slate-500">{$t('translate.to')}</label>
			<select
				bind:value={targetLang}
				class="rounded-lg border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:border-indigo-500 focus:ring-indigo-500"
			>
				<option value="zh-TW">Traditional Chinese</option>
				<option value="en">English</option>
				<option value="ja">Japanese</option>
				<option value="ko">Korean</option>
			</select>
		</div>

		<!-- Provider -->
		<div class="flex flex-col gap-1.5">
			<label class="text-xs font-medium text-slate-500">{$t('translate.provider')}</label>
			<select
				bind:value={preferredProvider}
				class="rounded-lg border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:border-indigo-500 focus:ring-indigo-500"
			>
				<option value="auto">Auto (Best)</option>
				<option value="deepl">DeepL</option>
				<option value="openai">OpenAI</option>
				<option value="google">Google</option>
			</select>
		</div>

		<!-- Options -->
		<div class="flex items-center pt-6">
			<label class="flex cursor-pointer items-center gap-2">
				<input
					type="checkbox"
					bind:checked={enableRefinement}
					class="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
				/>
				<span class="text-sm font-medium text-slate-700">{$t('translate.refinement')}</span>
			</label>
		</div>
	</div>

	<!-- Dropzone -->
	<div
		class="relative flex min-h-[200px] cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed transition-all duration-200 {isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-slate-100'}"
		onbackend:dragover={handleDragOver}
		onbackend:dragleave={handleDragLeave}
		onbackend:drop={handleDrop}
		onclick={() => fileInput.click()}
		role="button"
		tabindex="0"
		onkeydown={(e) => e.key === 'Enter' && fileInput.click()}
	>
		<input
			type="file"
			multiple
			class="hidden"
			bind:this={fileInput}
			onchange={handleFileSelect}
			accept=".txt,.md,.json,.csv"
		/>
		
		<div class="pointer-events-none flex flex-col items-center gap-3 text-center">
			<div class="rounded-full bg-white p-4 shadow-sm">
				<svg class="h-8 w-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
				</svg>
			</div>
			<div>
				<p class="text-lg font-medium text-slate-700">{$t('files.upload_desc')}</p>
				<p class="mt-1 text-sm text-slate-400">Supports .txt, .md, .json, .csv</p>
			</div>
		</div>
	</div>

	<!-- File List -->
	{#if files.length > 0}
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" transition:fade>
			{#each files as item (item.id)}
				<div class="group relative flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:shadow-md" transition:fly={{ y: 20, duration: 300 }}>
					<!-- Remove Button -->
					<button 
						class="absolute right-2 top-2 rounded-full p-1 text-slate-300 opacity-0 hover:bg-slate-100 hover:text-red-500 group-hover:opacity-100 transition-all"
						onclick={() => removeFile(item.id)}
					>
						<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>

					<div class="mb-4 flex items-start gap-3">
						<div class="rounded-lg bg-slate-100 p-2 text-slate-500">
							<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
							</svg>
						</div>
						<div class="overflow-hidden">
							<h3 class="truncate font-medium text-slate-800" title={item.file.name}>{item.file.name}</h3>
							<p class="text-xs text-slate-500">{formatSize(item.file.size)}</p>
						</div>
					</div>

					<div class="space-y-3">
						<!-- Status & Progress -->
						<div class="flex items-center justify-between text-xs">
							<span class="font-medium {
								item.status === 'completed' ? 'text-emerald-600' : 
								item.status === 'error' ? 'text-red-600' : 
								item.status === 'translating' ? 'text-indigo-600' : 'text-slate-500'
							}">
								{item.status === 'pending' ? 'Ready' : 
								 item.status === 'translating' ? $t('files.translating') : 
								 item.status === 'completed' ? $t('files.completed') : 
								 item.status === 'error' ? $t('files.error') : 'Uploading...'}
							</span>
							<span>{item.progress}%</span>
						</div>
						
						<div class="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
							<div 
								class="h-full transition-all duration-300 {
									item.status === 'completed' ? 'bg-emerald-500' : 
									item.status === 'error' ? 'bg-red-500' : 'bg-indigo-500'
								}"
								style="width: {item.progress}%"
							></div>
						</div>

						<!-- Actions -->
						{#if item.status === 'completed'}
							<button
								class="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 bg-white py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 hover:text-indigo-600 transition-colors"
								onclick={() => downloadFile(item)}
							>
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
								</svg>
								{$t('files.download')}
							</button>
						{:else if item.status === 'error'}
							<p class="text-xs text-red-500 truncate" title={item.error}>{item.error}</p>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
