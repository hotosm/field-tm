<script lang="ts">
	import '$styles/header.css';
	import { onMount, onDestroy } from 'svelte';
	import { online } from 'svelte/reactivity/window';
	import type { SlDrawer, SlTooltip } from '@shoelace-style/shoelace';
	// FIXME this is a workaround to re-import, as using sl-dropdown
	// and sl-menu prevents selection of values!
	// perhaps related to https://github.com/hotosm/ui/issues/73
	import '@shoelace-style/shoelace/dist/components/dropdown/dropdown.js';
	import '@shoelace-style/shoelace/dist/components/menu/menu.js';
	import '@shoelace-style/shoelace/dist/components/menu-item/menu-item.js';
	import type { SlSelectEvent } from '@shoelace-style/shoelace/dist/events';

	import { setLocale as setParaglideLocale, locales } from '$translations/runtime.js';
	import { m } from '$translations/messages.js';
	import Login from '$lib/components/login.svelte';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { defaultDrawerItems } from '$constants/drawerItems.ts';
	import { revokeCookies } from '$lib/api/login';
	import { getAlertStore } from '$store/common.svelte';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { goto } from '$app/navigation';
	import { languages } from '$constants/languages';

	type languageListType = {
		code: string;
		name: string;
		flag: string;
	};

	let drawerRef: SlDrawer | undefined = $state();
	let drawerOpenButtonRef: SlTooltip | undefined = $state();
	const loginStore = getLoginStore();
	const alertStore = getAlertStore();
	const commonStore = getCommonStore();
	const primaryLocale = $derived(commonStore.config?.primaryLocale);
	const languageList = $derived(
		locales
			.map((locale: string) => languages.find((language) => language.code === locale))
			.filter((lang): lang is languageListType => !!lang) // ensure no undefined
			.sort((a, b) => {
				// If set, prioritise primary locale from config
				if (primaryLocale) {
					if (a.code === primaryLocale) return -1;
					if (b.code === primaryLocale) return 1;
				}
				// else fallback to 'en' on top of list
				if (a.code === 'en') return -1;
				if (b.code === 'en') return 1;
				return 0;
			})
	);

	const handleSignOut = async () => {
		try {
			await revokeCookies();
			loginStore.signOut();
			drawerRef?.hide();
			// window.location.href = window.location.origin;
		} catch (error) {
			alertStore.setAlert({ variant: 'danger', message: 'Sign Out Failed' });
		}
	};

	const handleLocaleSelect = (event: SlSelectEvent) => {
		const selectedItem = event.detail.item;
		commonStore.setLocale(selectedItem.value);
		setParaglideLocale(selectedItem.value); // paraglide function for UI changes (causes reload)
	};

	let sidebarMenuItems = $derived(
		commonStore.config?.sidebarItemsOverride.length > 0 ? commonStore.config?.sidebarItemsOverride : defaultDrawerItems,
	);

	onMount(() => {
		// Handle locale change
		const container = document.querySelector('.locale-selection');
		const dropdown = container?.querySelector('sl-dropdown');
		dropdown?.addEventListener('sl-select', handleLocaleSelect);
	});

	onDestroy(() => {
		const container = document.querySelector('.locale-selection');
		const dropdown = container?.querySelector('sl-dropdown');
		dropdown?.removeEventListener('sl-select', handleLocaleSelect);
	});
</script>

<div class="header" class:offline-bg-color={!online.current}>
	<div
		onclick={() => goto('/')}
		onkeydown={(e) => {
			if (e.key === 'Enter') goto('/');
		}}
		role="button"
		tabindex="0"
		class="logo"
		aria-label="Home"
	>
		<img src={commonStore.config?.logoUrl} alt="hot-logo" />
		<span class="logo-text">
			{commonStore.config?.logoText}
		</span>
	</div>
	{#if !online.current}
		<sl-icon name="wifi-off"></sl-icon>
	{/if}
	<div class="nav">
		<!-- profile image and username display -->
		{#if loginStore?.getAuthDetails?.username}
			<div class="user">
				{#if !loginStore?.getAuthDetails?.picture}
					<sl-icon name="person-fill" class="" onclick={() => {}} onkeydown={() => {}} role="button" tabindex="0"
					></sl-icon>
				{:else}
					<img src={loginStore?.getAuthDetails?.picture} alt="profile" />
				{/if}
				<p class="username">
					{loginStore?.getAuthDetails?.username}
				</p>
			</div>
		{:else}
			<sl-button
				class="login-link"
				variant="text"
				size="small"
				onclick={() => {
					loginStore.toggleLoginModal(true);
				}}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						loginStore.toggleLoginModal(true);
					}
				}}
				role="button"
				tabindex="0"
			>
				<span>{m['header.sign_in']()}</span>
			</sl-button>
		{/if}

		<!-- drawer component toggle trigger -->
		<sl-icon
			name="list"
			class="drawer-icon"
			onclick={() => {
				drawerRef?.show();
			}}
			onkeydown={() => {
				drawerRef?.show();
			}}
			role="button"
			tabindex="0"
		></sl-icon>
	</div>
</div>
<Login />

<sl-drawer bind:this={drawerRef} class="drawer-overview">
	<div class="content">
		<div class="locale-selection">
			<sl-dropdown>
				<sl-button slot="trigger" caret>
					<sl-icon name="translate"></sl-icon>
					{commonStore.locale}
				</sl-button>
				<sl-menu>
					{#each languageList as language}
						<sl-menu-item value={language.code}><span slot="prefix">{language.flag}</span> {language.name}</sl-menu-item
						>
					{/each}
				</sl-menu>
			</sl-dropdown>
		</div>
		{#each sidebarMenuItems as item}
			<a target="_blank" rel="noopener noreferrer" href={item.path} class="menu-item">{item.name}</a>
		{/each}
		{#if loginStore?.getAuthDetails?.username}
			<sl-button
				class="sign-out"
				variant="primary"
				size="small"
				onclick={handleSignOut}
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') {
						handleSignOut();
					}
				}}
				role="button"
				tabindex="0"
			>
				{#key commonStore.locale}<span>{m['header.sign_out']()}</span>{/key}
			</sl-button>
		{/if}
	</div>
</sl-drawer>
