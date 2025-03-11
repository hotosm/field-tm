<script lang="ts">
	import type { Snippet } from 'svelte';
	import type SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';

	import { getLoginStore } from '$store/login.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { generateQrCode, downloadQrCode } from '$lib/odk/qrcode';
	import { m } from "$translations/messages.js";

	interface Props {
		infoDialogRef: SlDialog | null;
		projectName: string;
		projectOdkToken: string;
		children?: Snippet;
	}

	let { infoDialogRef, projectName, projectOdkToken, children }: Props = $props();

	const loginStore = getLoginStore();
	const commonStore = getCommonStore();

	let qrCodeData = $derived(
		generateQrCode(projectName, projectOdkToken, loginStore.getAuthDetails?.username || 'fmtm user'),
	);
</script>

<div class="font-barlow flex flex-col items-center p-4 space-y-4">
	<!-- Text above the QR code -->
	<div class="text-center w-full">
		<div class="text-lg font-medium">
			{#key commonStore.locale}<span class="mr-1">{m.scan_qr_code()}</span>{/key}
			<sl-tooltip content="More information on manually importing qr code" placement="bottom">
				<hot-icon
					onclick={() => {
						if (infoDialogRef) infoDialogRef?.show();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							if (infoDialogRef) infoDialogRef?.show();
						}
					}}
					role="button"
					tabindex="0"
					name="info-circle-fill"
					class="!text-[14px] text-[#b91c1c] cursor-pointer duration-200 scale-[1.5]"
				></hot-icon>
			</sl-tooltip>
		</div>
	</div>

	<!-- QR Code Container -->
	<div class="flex justify-center w-full max-w-sm">
		<hot-qr-code value={qrCodeData} label="Scan to open ODK Collect" size="250" class="p-4 bg-white m-4"></hot-qr-code>
	</div>

	<!-- Download Button -->
	<sl-button
		onclick={() => downloadQrCode(projectName)}
		onkeydown={(e: KeyboardEvent) => {
			e.key === 'Enter' && downloadQrCode(projectName);
		}}
		role="button"
		tabindex="0"
		size="small"
		class="secondary w-full max-w-[200px]"
	>
		<hot-icon slot="prefix" name="download" class="!text-[1rem] text-[#b91c1c] cursor-pointer duration-200"></hot-icon>
		{#key commonStore.locale}<span class="font-barlow font-medium text-base uppercase">{m.download()} QR</span>{/key}
	</sl-button>

	{@render children?.()}
</div>
