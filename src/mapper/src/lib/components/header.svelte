<script lang="ts">
	import '$styles/header.css';
	import { onMount, onDestroy } from 'svelte';
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
	import { revokeCookies } from '$lib/utils/login';
	import { getAlertStore } from '$store/common.svelte';
	import { getCommonStore, getProjectSetupStepStore } from '$store/common.svelte.ts';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import { goto } from '$app/navigation';

	let drawerRef: SlDrawer | undefined = $state();
	let drawerOpenButtonRef: SlTooltip | undefined = $state();
	const loginStore = getLoginStore();
	const alertStore = getAlertStore();
	const commonStore = getCommonStore();
	const projectSetupStepStore = getProjectSetupStepStore();

	let isFirstLoad = $derived(
		+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load'],
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

	let sidebarMenuItems = $derived(commonStore.config?.sidebarItemsOverride.length > 0 ? commonStore.config?.sidebarItemsOverride : defaultDrawerItems)

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
<div class="header">
	<div
		onclick={() => goto('/')}
		onkeydown={(e) => {
			if (e.key === 'Enter') goto('/');
		}}
		role="button"
		tabindex="0"
		class="logo"
	>
		<img src={commonStore.config?.logoUrl} alt="hot-logo" />
		<!-- The approach below is finicky - can loading the logo via CSS work nicely? -->
		<!-- <a href={window.location.origin} 
			class="inline-block flex h-[2.2rem] sm:h-[3rem] w-[2.2rem] sm:w-[3rem] bg-no-repeat bg-cover"
			style="background-image: url('https://upload.wikimedia.org/wikipedia/commons/4/45/Humanitarian_OpenStreetMap_Team_logo.svg');"
			aria-label="Home"
		></a> -->
		<span class="logo-text">
			{commonStore.config?.logoText}
		</span>
	</div>
	<div class="nav">
		<!-- profile image and username display -->
		{#if loginStore?.getAuthDetails?.username}
			<div class="user">
				{#if !loginStore?.getAuthDetails?.picture}
					<hot-icon
						name="person-fill"
						class=""
						onclick={() => {}}
						onkeydown={() => {}}
						role="button"
						tabindex="0"
					></hot-icon>
				{:else}
					<img
						src={loginStore?.getAuthDetails?.picture}
						alt="profile"
					/>
				{/if}
				<p class="username">
					{loginStore?.getAuthDetails?.username}
				</p>
			</div>
		{:else}
			<hot-button
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
			</hot-button>
		{/if}

		<!-- drawer component toggle trigger (snippet to reuse below) -->
		{#snippet drawerOpenButton()}
			<hot-icon
				name="list"
				class="drawer-icon ${isFirstLoad && !commonStore.enableWebforms ? 'drawer-icon-firstload' : ''}"
				onclick={() => {
					drawerRef?.show();
				}}
				onkeydown={() => {
					drawerRef?.show();
				}}
				role="button"
				tabindex="0"
			></hot-icon>
		{/snippet}
		<!-- add tooltip on first load -->
		{#if isFirstLoad && !commonStore.enableWebforms}
			<hot-tooltip
				bind:this={drawerOpenButtonRef}
				content="First download the custom ODK Collect app here"
				open={true}
				placement="bottom"
				onhot-after-hide={() => {
					// Always keep tooltip open
					drawerOpenButtonRef?.show();
				}}
			>
				{@render drawerOpenButton()}
			</hot-tooltip>
			<!-- else render with no tooltip -->
		{:else}
			{@render drawerOpenButton()}
		{/if}
	</div>
</div>
<Login />

<hot-drawer bind:this={drawerRef} class="drawer-overview">
	<div class="content">
		<div class="locale-selection">
			<sl-dropdown>
				<hot-button slot="trigger" caret>
					<hot-icon name="translate"></hot-icon>
					{commonStore.locale}
				</hot-button>
				<sl-menu>
					{#each locales as locale}
						<sl-menu-item value={locale}>{locale}</sl-menu-item>
					{/each}
				</sl-menu>
			</sl-dropdown>
		</div>
		{#each sidebarMenuItems as item}
			<a
				target="_blank"
				rel="noopener noreferrer"
				href={item.path}
				class="menu-item">{item.name}</a
			>
		{/each}
		{#if loginStore?.getAuthDetails?.username}
			<hot-button
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
			</hot-button>
		{/if}
	</div>
</hot-drawer>
