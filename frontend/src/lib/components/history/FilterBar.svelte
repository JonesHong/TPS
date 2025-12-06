<script lang="ts">
	import { t } from 'svelte-i18n';

	interface Props {
		providers: string[];
		sourceLanguages: string[];
		targetLanguages: string[];
		selectedProviders: string[];
		selectedSourceLang: string;
		selectedTargetLang: string;
		onProvidersChange: (providers: string[]) => void;
		onSourceLangChange: (lang: string) => void;
		onTargetLangChange: (lang: string) => void;
	}

	let {
		providers,
		sourceLanguages,
		targetLanguages,
		selectedProviders,
		selectedSourceLang,
		selectedTargetLang,
		onProvidersChange,
		onSourceLangChange,
		onTargetLangChange
	}: Props = $props();

	let providerLabels = $derived({
		cache: $t('providers.cache'),
		deepl: 'DeepL',
		openai: 'OpenAI',
		google: 'Google'
	});

	const providerColors: Record<string, string> = {
		cache: 'bg-green-500',
		deepl: 'bg-blue-500',
		openai: 'bg-purple-500',
		google: 'bg-amber-500'
	};

	function toggleProvider(provider: string) {
		if (selectedProviders.includes(provider)) {
			onProvidersChange(selectedProviders.filter((p) => p !== provider));
		} else {
			onProvidersChange([...selectedProviders, provider]);
		}
	}
</script>

<div class="flex flex-wrap items-center gap-4">
	<!-- Provider filters -->
	<div class="flex items-center gap-2">
		<span class="text-sm font-medium text-gray-700">{$t('common.provider')}:</span>
		<div class="flex flex-wrap gap-2">
			{#each providers as provider}
				{@const isSelected = selectedProviders.includes(provider)}
				<button
					type="button"
					class="flex items-center gap-1.5 rounded-full border px-3 py-1 text-sm transition-colors {isSelected
						? 'border-gray-400 bg-gray-100'
						: 'border-gray-200 hover:bg-gray-50'}"
					onclick={() => toggleProvider(provider)}
				>
					<span class="h-2 w-2 rounded-full {providerColors[provider] || 'bg-gray-400'}"></span>
					{providerLabels[provider as keyof typeof providerLabels] || provider}
					{#if isSelected}
						<span class="ml-1 text-gray-500">✕</span>
					{/if}
				</button>
			{/each}
		</div>
	</div>

	<!-- Source language filter -->
	<div class="flex items-center gap-2">
		<span class="text-sm font-medium text-gray-700">{$t('common.from')}:</span>
		<select
			class="rounded border border-gray-300 px-2 py-1 text-sm"
			value={selectedSourceLang}
			onchange={(e) => onSourceLangChange((e.target as HTMLSelectElement).value)}
		>
			<option value="">{$t('common.all')}</option>
			{#each sourceLanguages as lang}
				<option value={lang}>{lang.toUpperCase()}</option>
			{/each}
		</select>
	</div>

	<!-- Target language filter -->
	<div class="flex items-center gap-2">
		<span class="text-sm font-medium text-gray-700">{$t('common.to')}:</span>
		<select
			class="rounded border border-gray-300 px-2 py-1 text-sm"
			value={selectedTargetLang}
			onchange={(e) => onTargetLangChange((e.target as HTMLSelectElement).value)}
		>
			<option value="">{$t('common.all')}</option>
			{#each targetLanguages as lang}
				<option value={lang}>{lang.toUpperCase()}</option>
			{/each}
		</select>
	</div>

	<!-- Clear filters -->
	{#if selectedProviders.length > 0 || selectedSourceLang || selectedTargetLang}
		<button
			type="button"
			class="text-sm text-primary-600 hover:underline"
			onclick={() => {
				onProvidersChange([]);
				onSourceLangChange('');
				onTargetLangChange('');
			}}
		>
			Clear all
		</button>
	{/if}
</div>
