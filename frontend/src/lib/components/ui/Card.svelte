<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		children: Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div class="rounded-lg border bg-card text-card-foreground shadow-sm {className}">
	{@render children()}
</div>
