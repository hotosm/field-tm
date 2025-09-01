// Module for generating ODK Collect QR Code (zlib, base64)

import { deflate } from 'pako/lib/deflate';

// function base64zlibdecode(string) {
//   return new TextDecoder().decode(inflate(Uint8Array.from(window.atob(string), (c) => c.codePointAt(0))))
// }

function base64zlibencode(string: string) {
	return window.btoa(String.fromCodePoint(...deflate(new TextEncoder().encode(string))));
}

export function generateQrCode(projectName: string, odkToken: string, username: string) {
	const odkCollectJson = JSON.stringify({
		general: {
			server_url: odkToken,
			form_update_mode: 'match_exactly',
			basemap_source: 'osm',
			autosend: 'wifi_and_cellular',
			metadata_email: 'NOT IMPLEMENTED',
			metadata_username: username,
		},
		project: { name: projectName },
		admin: {},
	});

	return base64zlibencode(odkCollectJson);
}

export function downloadQrCode(projectName: string) {
	const qrCodeElement = document.querySelector('sl-qr-code')?.shadowRoot;
	if (!qrCodeElement) return;

	const canvas = qrCodeElement.querySelector('canvas');
	if (!canvas) return;

	const downloadLink = document.createElement('a');
	downloadLink.download = `QRCode_${projectName}.png`;
	downloadLink.href = canvas.toDataURL('image/png');
	downloadLink.click();
}
