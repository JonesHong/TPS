<script lang="ts">
	import '../app.css';
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	let isSidebarOpen = $state(false);

	const navItems = [
		{ href: '/', label: 'Dashboard', icon: 'chart-pie' },
		{ href: '/history', label: 'History', icon: 'clock' },
		{ href: '/translate', label: 'Translate', icon: 'language' }
	];

	function toggleSidebar() {
		isSidebarOpen = !isSidebarOpen;
	}

	function closeSidebar() {
		isSidebarOpen = false;
	}
</script>

<div class="flex h-screen bg-gray-50">
	<!-- Mobile sidebar backdrop -->
	{#if isSidebarOpen}
		<div
			class="fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden"
			onclick={closeSidebar}
			onkeydown={(e) => e.key === 'Escape' && closeSidebar()}
			role="button"
			tabindex="-1"
		></div>
	{/if}

	<!-- Sidebar -->
	<aside
		class="fixed inset-y-0 left-0 z-30 w-64 transform bg-white shadow-lg transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 {isSidebarOpen
			? 'translate-x-0'
			: '-translate-x-full'}"
	>
		<div class="flex h-full flex-col">
			<!-- Logo -->
			<div class="flex h-16 items-center justify-center border-b px-4">
				<h1 class="text-xl font-bold text-primary-600">
					<span class="text-2xl">🌐</span> TPS
				</h1>
			</div>

			<!-- Navigation -->
			<nav class="flex-1 space-y-1 px-3 py-4">
				{#each navItems as item}
					{@const isActive = $page.url.pathname === item.href}
					<a
						href={item.href}
						onclick={closeSidebar}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors {isActive
							? 'bg-primary-50 text-primary-700'
							: 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
					>
						{#if item.icon === 'chart-pie'}
							<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"
								/>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"
								/>
							</svg>
						{:else if item.icon === 'clock'}
							<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
								/>
							</svg>
						{:else if item.icon === 'language'}
							<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
								/>
							</svg>
						{/if}
						{item.label}
					</a>
				{/each}
			</nav>

			<!-- Footer -->
			<div class="border-t p-4 text-center text-xs text-gray-500">
				Translation Proxy System
			</div>
		</div>
	</aside>

	<!-- Main content -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Header -->
		<header class="flex h-16 items-center justify-between border-b bg-white px-4 shadow-sm">
			<!-- Mobile menu button -->
			<button
				type="button"
				class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-600 lg:hidden"
				onclick={toggleSidebar}
			>
				<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 6h16M4 12h16M4 18h16"
					/>
				</svg>
			</button>

			<!-- Page title -->
			<h2 class="text-lg font-semibold text-gray-800">
				{#if $page.url.pathname === '/'}
					Dashboard
				{:else if $page.url.pathname === '/history'}
					Translation History
				{:else if $page.url.pathname === '/translate'}
					Translate
				{/if}
			</h2>

			<!-- Placeholder for user menu -->
			<div class="w-8"></div>
		</header>

		<!-- Page content -->
		<main class="flex-1 overflow-auto p-4 lg:p-6">
			{@render children()}
		</main>
	</div>
</div>
