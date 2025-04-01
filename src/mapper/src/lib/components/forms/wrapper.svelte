<script lang="ts">
	import type { SlDrawer } from '@shoelace-style/shoelace';

	import { getCommonStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';

	const CUSTOM_UPLOAD_ELEMENT_ID = '95c6807c-82b4-4208-b5df-5a3e795227b0';

	const API_URL = import.meta.env.VITE_API_URL;
	type Props = {
		display: Boolean;
		entityId: string | undefined;
		projectId: number | undefined;
		taskId: number | undefined;
		webFormsRef: HTMLElement | undefined;
	};
	const commonStore = getCommonStore();
	const loginStore = getLoginStore();

	let { display = $bindable(false), entityId, webFormsRef = $bindable(undefined), projectId, taskId }: Props = $props();
	let drawerRef: SlDrawer;
	let iframeRef: HTMLIFrameElement | undefined;
	let odkForm: any;
	let startDate: string | undefined;

	let pic: any;

	function handleMutation() {
		if (!iframeRef) return;
		if (!iframeRef.contentDocument) return;
		if (!odkForm) return;
		if (!webFormsRef) return;

		// check if we've already added the custom upload input
		if (iframeRef.contentDocument.getElementById(CUSTOM_UPLOAD_ELEMENT_ID)) return;
		console.log('over-writing control node');

		const uploadControl = odkForm.getChildren().find((n: any) => n.constructor.name === 'UploadControl');
		const uploadControlNodeId = uploadControl.nodeId;
		const uploadControlNodeSelector = `[id='${uploadControlNodeId}_container']`;
		const uploadControlNode = webFormsRef.querySelector(uploadControlNodeSelector);
		if (!uploadControlNode) return;

		const controlText = iframeRef.contentDocument.createElement('div');
		controlText.id = CUSTOM_UPLOAD_ELEMENT_ID;
		controlText.className = 'control-text';
		controlText.style.marginBottom = '.75rem';

		const label = iframeRef.contentDocument.createElement('label');
		label.style.fontWeight = '400';
		label.style.lineHeight = '1.8rem';
		const span = iframeRef.contentDocument.createElement('span');
		span.textContent = uploadControl.engineState.label.chunks.map((chunk: any) => chunk.asString).join(' ');
		label.appendChild(span);
		controlText.appendChild(label);
		const inputWrapper = iframeRef.contentDocument.createElement('div');
		const input = iframeRef.contentDocument.createElement('input');
		input.id = CUSTOM_UPLOAD_ELEMENT_ID;
		input.addEventListener('change', () => {
			pic = input.files?.[0];
		});
		input.type = 'file';
		inputWrapper.appendChild(input);

		uploadControlNode.innerHTML = '';
		uploadControlNode.appendChild(controlText);
		uploadControlNode.appendChild(inputWrapper);
	}
	function handleSubmit(payload: any) {
		(async () => {
			if (!payload.detail) return;

			let submission_xml = await payload.detail[0].data.instanceFile.text();

			submission_xml = submission_xml.replace('<start/>', `<start>${startDate}</start>`);
			submission_xml = submission_xml.replace('<end/>', `<end>${new Date().toISOString()}</end>`);

			const authDetails = loginStore?.getAuthDetails;
			if (authDetails?.username) {
				submission_xml = submission_xml.replace('<username/>', `<username>${authDetails?.username}</username>`);
			}

			if (authDetails?.email_address) {
				submission_xml = submission_xml.replace('<email/>', `<email>${authDetails?.email_address}</email>`);
			}

			if (pic && pic?.name) {
				submission_xml = submission_xml.replace('<image/>', `<image>${pic?.name}</image>`);
			}

			const url = `${API_URL}/submission?project_id=${projectId}`;
			var data = new FormData();
			data.append('submission_xml', submission_xml);
			data.append('submission_files', pic);
			await fetch(url, {
				method: 'POST',
				body: data,
			});
			display = false;
		})();
	}
	function handleOdkForm(evt: any) {
		if (evt?.detail?.[0]) {
			odkForm = evt.detail[0];
			console.log('set odkForm', odkForm);
			// over-write default language
			setFormLanguage(commonStore.locale);

			const nodes = odkForm.getChildren();

			// select feature that you clicked on map
			nodes.find((it: any) => it.definition.nodeset === '/data/feature')?.setValueState([entityId]);
			nodes.find((it: any) => it.definition.nodeset === '/data/task_id')?.setValueState(`${taskId}`);
		}
	}
	const setFormLanguage = (newLocale: string) => {
		if (odkForm) {
			const target = `(${newLocale.toLowerCase()})`;
			const match = odkForm.languages.find((it: any) => it?.language.toLowerCase().includes(target));
			if (match) {
				odkForm?.setLanguage(match);
			}
		}
	};
	$effect(() => {
		// making sure we re-run whenever one of the following reactive variables changes
		display;
		projectId;
		entityId;
		if (display) {
			startDate = new Date().toISOString();
		}
	});
	$effect(() => {
		if (commonStore.locale) {
			setFormLanguage(commonStore.locale);
		}
	});
	$effect(() => {
		// we want to rerun this $effect function whenever a new iframe is rendered
		// because projectId and entityId are state keys that force a re-render below when they change
		// we add them here inside the $effect function, so Svelte knows that the function depends on them
		projectId;
		entityId;
		if (iframeRef) {
			const observer = new MutationObserver(handleMutation);
			const intervalId = setInterval(() => {
				webFormsRef = iframeRef?.contentDocument?.querySelector('odk-web-form') || undefined;
				if (webFormsRef) {
					clearInterval(intervalId);
					webFormsRef.addEventListener('submit', handleSubmit);
					webFormsRef.addEventListener('odkForm', handleOdkForm);
					observer.observe(webFormsRef, { attributes: true, childList: true, subtree: true });
				}
			}, 10);

			// clear interval when re-run
			return () => {
				clearInterval(intervalId);
				observer.disconnect();
			};
		}
	});
	$effect(() => {
		if (drawerRef) {
			drawerRef.addEventListener('sl-hide', function () {
				if (display) {
					display = false;
				}
			});
		}
	});
</script>

<hot-drawer
	id="odk-web-forms-drawer"
	bind:this={drawerRef}
	contained
	open={display}
	placement="start"
	class="drawer-contained drawer-placement-start drawer-overview"
	style="--size: 100vw; --header-spacing: 0px"
>
	{#if entityId}
		{#key projectId}
			{#key entityId}
				<iframe
					bind:this={iframeRef}
					title="odk-web-forms-wrapper"
					src={`./web-forms.html?projectId=${projectId}&entityId=${entityId}&api_url=${API_URL}&language=${commonStore.locale}`}
					style="height: 100%; width: 100%; z-index: 11;"
				>
				</iframe>
			{/key}
		{/key}
	{/if}
</hot-drawer>

<style>
	#odk-web-forms-drawer::part(panel) {
		z-index: 11;
	}
	#odk-web-forms-drawer::part(body) {
		padding: 0;
	}
</style>
