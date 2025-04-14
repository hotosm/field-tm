<script lang="ts">
	import OSMLogo from '$assets/images/osm-logo.png';
	import GoogleLogo from '$assets/images/google-logo.svg';
	import { loginRedirect } from '$lib/utils/login';
	import { getLoginStore } from '$store/login.svelte.ts';
	import type { LoginProviderKey } from '$store/common.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';

	const commonStore = getCommonStore();
	const loginStore = getLoginStore();

	type LoginOption = {
		id: LoginProviderKey;
		name: string;
		image: string;
		description?: string;
	};
	const ALL_LOGIN_PROVIDERS: Record<LoginProviderKey, Omit<LoginOption, 'id'>> = {
		osm: {
			name: 'Sign in with OSM',
			image: OSMLogo,
			description: 'Edits made in FMTM will be credited to your OSM account.',
		},
		google: {
			name: 'Sign in with Google',
			image: GoogleLogo,
		}
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
		loginRedirect(selectedOption);
	};
</script>

<hot-dialog
	bind:this={dialogRef}
	class="dialog-overview z-50 font-barlow font-regular"
	open={loginStore.isLoginModalOpen}
	onsl-hide={() => {
		loginStore.toggleLoginModal(false);
	}}
	noHeader
>
	<div class="flex items-start flex-col">
		<div class="flex items-center justify-between w-full mb-2">
			<p class="text-2xl font-bold mb-1">Sign In</p>
			<hot-icon
				name="close"
				class="text-[1.5rem] text-gray-500 cursor-pointer"
				onclick={() => loginStore.toggleLoginModal(false)}
				role="button"
				tabindex="0"
				onkeydown={(e: KeyboardEvent) => {
					if (e.key === 'Enter') loginStore.toggleLoginModal(false);
				}}
			></hot-icon>
		</div>
		<div class="text-base mb-5 text-gray-700">Select an account type to sign in</div>
		<div class="w-full flex flex-col gap-4 justify-items-center">
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
					class="option-card bg-[#F5F5F5] text-gray-700 p-3 border-1 border-solid border-white hover:border-[#d73f3f] rounded-md duration-300 hover:text-red-600 cursor-pointer text-sm flex items-start gap-3 group flex items-center"
				>
					<img src={option?.image} class="w-10" alt="personal osm account" />

					<div class="flex flex-col">
						<div class="text-lg font-medium">{option.name}</div>
						{#if option.description}
							<div class="">{option.description}</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</hot-dialog>
