<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class="flex flex-col space-y-1.5 p-6 {className}">
	{@render children()}
</div>
