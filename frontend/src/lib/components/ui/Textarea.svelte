<script lang="ts">
	interface Props {
		placeholder?: string;
		value?: string;
		disabled?: boolean;
		rows?: number;
		class?: string;
		oninput?: (e: Event) => void;
	}

	let {
		placeholder = '',
		value = $bindable(''),
		disabled = false,
		rows = 4,
		class: className = '',
		oninput
	}: Props = $props();
</script>

<textarea
	{placeholder}
	{disabled}
	{rows}
	bind:value
	{oninput}
	class="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 {className}"
></textarea>
