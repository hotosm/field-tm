<script lang="ts">
	import type { SlDrawer } from '@shoelace-style/shoelace';

	import { getCommonStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { fetchBlobUrl, fetchFormMediBlobUrls } from '$lib/utils/fetch.ts';

	import type { Action } from 'svelte/action';

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
	const entitiesStore = getEntitiesStatusStore();
	// use Map for quick lookups
	let entityMap = $derived(new Map(entitiesStore.entitiesStatusList.map((entity) => [entity.entity_id, entity])));
	const selectedEntityId = $derived(entitiesStore.selectedEntity || '');
	const selectedEntity = $derived(entityMap.get(selectedEntityId));

	let { display = $bindable(false), entityId, webFormsRef = $bindable(undefined), projectId, taskId }: Props = $props();
	let drawerRef: SlDrawer;
	let odkForm: any;
	let startDate: string | undefined;

	let pic: any;

	const formXmlPromise = fetchBlobUrl(`${API_URL}/projects/${projectId}/form-xml`);

	const odkWebFormPromise = fetchBlobUrl('https://hotosm.github.io/web-forms/odk-web-form.js');

	const formMediaPromise = fetchFormMediBlobUrls(projectId!);

	function handleMutation(iframe: HTMLIFrameElement) {
		if (!iframe.contentDocument) return;
		if (!odkForm) return;
		if (!webFormsRef) return;

		// check if we've already added the custom upload input
		if (iframe.contentDocument.getElementById(CUSTOM_UPLOAD_ELEMENT_ID)) return;

		const uploadControl = odkForm.getChildren().find((n: any) => n.constructor.name === 'UploadControl');
		const uploadControlNode = webFormsRef.querySelector(`[id='${uploadControl.nodeId}_container']`);
		if (!uploadControlNode) return;

		const controlText = iframe.contentDocument.createElement('div');
		controlText.id = CUSTOM_UPLOAD_ELEMENT_ID;
		controlText.className = 'control-text';
		controlText.style.marginBottom = '.75rem';

		const label = iframe.contentDocument.createElement('label');
		label.style.fontWeight = '400';
		label.style.lineHeight = '1.8rem';
		const span = iframe.contentDocument.createElement('span');
		span.textContent = uploadControl.engineState.label.chunks.map((chunk: any) => chunk.asString).join(' ');
		label.appendChild(span);
		controlText.appendChild(label);
		const inputWrapper = iframe.contentDocument.createElement('div');
		const input = iframe.contentDocument.createElement('input');
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

			// entity id isn't included in the payload by default because we marked it as not relevant earlier
			// (in order to hide it from the user's display)
			submission_xml = submission_xml.replace('<warmup/>', `<warmup/><feature>${entityId}</feature>`);

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
			if (pic && pic?.name) {
				data.append('submission_files', pic);
			}
			// Submit the XML + any submission media
			await fetch(url, {
				method: 'POST',
				body: data,
			});

			// Set the entity status to SURVEY_SUBMITTED (2)
			entitiesStore.updateEntityStatus(projectId, {
				entity_id: selectedEntity?.entity_id,
				status: 2,
				// NOTE here we don't translate the field as English values are always saved as the Entity label
				label: `Task ${selectedEntity?.task_id} Feature ${selectedEntity?.osmid}`,
			});

			display = false;
		})();
	}
	function handleOdkForm(evt: any) {
		if (evt?.detail?.[0]) {
			odkForm = evt.detail[0];
			// over-write default language
			setFormLanguage(commonStore.locale);

			const nodes = odkForm.getChildren();

			// select feature that you clicked on map
			const featureNode = nodes.find((it: any) => it.definition.nodeset === '/data/feature');
			if (featureNode) {
				featureNode?.setValueState([entityId]);

				// hide this node because we don't need to see it after setting the value
				featureNode.state.clientState.relevant = false;
			}

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

	const handleIframe: Action = (node) => {
		$effect(() => {
			const iframe = node as unknown as HTMLIFrameElement;

			// we want to rerun this $effect function whenever a new iframe is rendered
			const observer = new MutationObserver(() => handleMutation(iframe));
			const intervalId = setInterval(() => {
				webFormsRef = iframe?.contentDocument?.querySelector('odk-web-form') || undefined;
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
		});
	};

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
	{#await odkWebFormPromise then odkWebFormUrl}
		{#if entityId}
			{#key projectId}
				{#await formXmlPromise then formXml}
					{#await formMediaPromise then formMedia}
						{#key entityId}
							<iframe
								use:handleIframe
								title="odk-web-forms-wrapper"
								src={`./web-forms.html?projectId=${projectId}&entityId=${entityId}&formXml=${formXml}&language=${commonStore.locale}&odkWebFormUrl=${odkWebFormUrl}&formMedia=${encodeURIComponent(JSON.stringify(formMedia))}`}
								style="height: 100%; width: 100%; z-index: 11;"
							></iframe>
						{/key}
					{/await}
				{/await}
			{/key}
		{/if}
	{/await}
</hot-drawer>

<style>
	#odk-web-forms-drawer::part(panel) {
		z-index: 11;
	}
	#odk-web-forms-drawer::part(body) {
		padding: 0;
	}
</style>
