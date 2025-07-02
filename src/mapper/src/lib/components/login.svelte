<script lang="ts">
	import '$styles/login.css';
	import OSMLogo from '$assets/images/osm-logo.png';
	import GoogleLogo from '$assets/images/google-logo.svg';
	import { loginRedirect } from '$lib/api/login';
	import { getLoginStore } from '$store/login.svelte.ts';
	import type { LoginProviderKey } from '$store/common.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';

	const commonStore = getCommonStore();
	const loginStore = getLoginStore();

	type LoginOption = {
		id: LoginProviderKey;
		name: string;
		image: string;
	};
	const ALL_LOGIN_PROVIDERS: Record<LoginProviderKey, Omit<LoginOption, 'id'>> = {
		osm: {
			name: 'Sign in with OSM',
			image: OSMLogo,
		},
		google: {
			name: 'Sign in with Google',
			image: GoogleLogo,
		},
	};
	// Determine enabled providers from config (default enabled, unless disabled)
	const loginOptions: LoginOption[] = Object.entries(ALL_LOGIN_PROVIDERS)
		.filter(([key]) => commonStore.config?.loginProviders?.[key as LoginProviderKey] !== false)
		.map(([key, info]) => ({
			id: key as LoginProviderKey,
			...info,
		}));

	// 🧼 Refs / handlers
	let dialogRef;

	const handleSignIn = async (selectedOption: LoginProviderKey) => {
		sessionStorage.setItem('requestedPath', window.location.pathname);
		loginRedirect(selectedOption);
	};
</script>

<hot-dialog
	bind:this={dialogRef}
	class="login-dialog"
	open={loginStore.isLoginModalOpen}
	onsl-hide={() => {
		loginStore.toggleLoginModal(false);
	}}
	noHeader
>
	<div class="content">
		<div class="header">
			<p class="title">Sign In</p>
			<hot-icon
				name="close"
				onclick={() => loginStore.toggleLoginModal(false)}
				role="button"
				tabindex="0"
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') loginStore.toggleLoginModal(false);
				}}
			></hot-icon>
		</div>
		<div class="subtitle">Select an account type to sign in</div>
		<div class="options">
			{#each loginOptions as option}
				<div
					id={option.id}
					onclick={() => handleSignIn(option.id)}
					role="button"
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							handleSignIn(option.id);
						}
					}}
					tabindex="0"
					class="option"
				>
					<img src={option?.image} class="image" alt="personal osm account" />

					<div class="name-desc">
						<div class="option-name">{option.name}</div>
						{#if option.description}
							<div>{option.description}</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</hot-dialog>
