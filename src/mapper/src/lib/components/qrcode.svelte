<script lang="ts">
	import '$styles/qr-code.css';
	import type { Snippet } from 'svelte';
	import type SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';

	import { getLoginStore } from '$store/login.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { generateQrCode, downloadQrCode } from '$lib/odk/qrcode';
	import { m } from '$translations/messages.js';

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

<div class="qr-code">
	<!-- Text above the QR code -->
	<div class="title-wrapper">
		<div class="title">
			{#key commonStore.locale}<span>{m['odk.scan_qr_code']()}</span>{/key}
			<sl-tooltip content={m['qrcode.moreinfo']()} placement="bottom">
				<sl-icon
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
				></sl-icon>
			</sl-tooltip>
		</div>
	</div>

	<!-- QR Code Container -->
	<div class="qr-code-container">
		<sl-qr-code value={qrCodeData} label={m['qrcode.scan_to_open_odk']()} size="250"></sl-qr-code>
	</div>

	<!-- Download Button -->
	<sl-button
		class="download-button"
		onclick={() => downloadQrCode(projectName)}
		onkeydown={(e: KeyboardEvent) => {
			e.key === 'Enter' && downloadQrCode(projectName);
		}}
		role="button"
		tabindex="0"
		size="small"
	>
		<sl-icon slot="prefix" name="download"></sl-icon>
		{#key commonStore.locale}<span>{m.download()} QR</span>{/key}
	</sl-button>

	{@render children?.()}
</div>
