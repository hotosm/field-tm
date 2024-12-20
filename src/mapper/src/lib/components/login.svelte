<script lang="ts">
	import OSMLogo from '$assets/images/osm-logo.png';
	import { osmLoginRedirect } from '$lib/utils/login';
	import { getLoginStore } from '$store/login.svelte.ts';

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
	];

	let dialogRef;
	const loginStore = getLoginStore();

	const handleSignIn = async (selectedOption: string) => {
		if (selectedOption === 'osm_account') {
			// store current url in local storage so that the user can be redirected to current page after login
			sessionStorage.setItem('requestedPath', window.location.pathname);
			osmLoginRedirect();
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
