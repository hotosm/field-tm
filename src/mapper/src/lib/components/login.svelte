<script lang="ts">
	import OSMLogo from '$assets/images/osm-logo.png';
	import { osmLoginRedirect, TemporaryLoginService } from '$lib/utils/login';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { getAlertStore } from '$store/common.svelte.ts';

	type Props = {
		open: boolean;
		toggleOpen: (value: boolean) => void;
	};

	type loginOptionsType = {
		id: string;
		name: string;
		icon?: string;
		image?: string;
		description: string;
	};

	const loginOptions: loginOptionsType[] = [
		{
			id: 'osm_account',
			name: 'Personal OSM Account',
			image: OSMLogo,
			description: 'Edits made in FMTM will be credited to your OSM account.',
		},
		{
			id: 'temp_account',
			name: 'Temporary Account',
			icon: 'person-fill',
			description: "If you're not an OSM user or prefer not to create an OSM account.",
		},
	];

	let dialogRef;
	const loginStore = getLoginStore();
	const alertStore = getAlertStore();

	const handleSignIn = async (selectedOption: string) => {
		if (selectedOption === 'osm_account') {
			// store current url in local storage so that the user can be redirected to current page after login
			localStorage.setItem('requestedPath', window.location.pathname);
			osmLoginRedirect();
		} else {
			const userDetailResp = await TemporaryLoginService(`${import.meta.env.VITE_API_URL}/auth/temp-login`);

			if (!userDetailResp) {
				alertStore.setAlert({ variant: 'danger', message: 'Temporary Login Failed' });
				return;
			}
			loginStore.setAuthDetails({ authDetails: userDetailResp });

			// the react frontend uses redux-persist to store the authDetails in the local storage, so we maintain the same schema to store data here also
			localStorage.setItem(
				'persist:login',
				JSON.stringify({
					authDetails: JSON.stringify(userDetailResp),
					_persist: JSON.stringify({ version: -1, rehydrated: true }),
				}),
			);
			location.reload();
		}
	};
</script>

<hot-dialog
	bind:this={dialogRef}
	class="dialog-overview z-50 font-barlow-regular"
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
					class="option-card bg-[#F5F5F5] text-gray-700 p-3 rounded-md duration-300 hover:border-primaryRed hover:text-red-600 cursor-pointer text-sm flex items-start gap-3 group"
				>
					<div class="w-10 max-w-10 min-w-10">
						{#if option?.image}
							<img src={option?.image} class="w-full" alt="personal osm account" />
						{:else}
							<hot-icon name={option?.icon} class="text-[2.5rem]"></hot-icon>
						{/if}
					</div>
					<div class="flex flex-col">
						<div class="text-lg font-medium">{option.name}</div>
						<div class="">{option.description}</div>
					</div>
				</div>
			{/each}
		</div>
	</div>
</hot-dialog>

<style>
	.option-card {
		border: 1px solid white;
	}

	.option-card:hover {
		border: solid 1px #d73f3f;
	}
</style>
