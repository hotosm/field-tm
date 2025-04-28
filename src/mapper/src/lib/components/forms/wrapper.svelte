<script lang="ts">
	import '$styles/forms.css';
	import type { SlDrawer } from '@shoelace-style/shoelace';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { fetchBlobUrl, fetchFormMediBlobUrls } from '$lib/api/fetch';
	import { m } from '$translations/messages.js';

	import type { Action } from 'svelte/action';

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
	const selectedEntityCoordinate = $derived(entitiesStore.selectedEntityCoordinate);

	let { display = $bindable(false), entityId, webFormsRef = $bindable(undefined), projectId, taskId }: Props = $props();
	let drawerRef: SlDrawer;
	let odkForm: any;
	let startDate: string | undefined;

	let drawerLabel = $state('');

	const formXmlPromise = fetchBlobUrl(`${API_URL}/central/form-xml?project_id=${projectId}`);

	const odkWebFormPromise = fetchBlobUrl('https://hotosm.github.io/web-forms/odk-web-form.js');

	const formMediaPromise = fetchFormMediBlobUrls(projectId!);

	function handleSubmit(payload: any) {
		(async () => {
			if (!payload.detail) return;
			if (!projectId) return;

			const { instanceFile, attachments = [] } = await payload.detail[0].data[0];
			let submission_xml = await instanceFile.text();

			// missing start, end, today, phonenumber, deviceid, username, email, instruction
			// included xid, xlocation, task_id, status,image number

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

			if (entitiesStore.userLocationCoord) {
				const [longitude, latitude] = entitiesStore.userLocationCoord as [number, number];
				// add 0.0 for altitude and 10.0 for accuracy as defaults
				submission_xml = submission_xml.replace('<warmup/>', `<warmup>${latitude} ${longitude} 0.0 0.0</warmup>`);
			}

			const url = `${API_URL}/submission?project_id=${projectId}`;
			var data = new FormData();
			data.append('submission_xml', submission_xml);
			attachments.forEach((attachment: File) => {
				data.append('submission_files', attachment);
			});
			// Submit the XML + any submission media
			await fetch(url, {
				method: 'POST',
				body: data,
			});

			let entityStatus = null;
			if (submission_xml.includes('<feature_exists>no</feature_exists>')) {
				entityStatus = 6; // MARKED_BAD
			} else if (submission_xml.includes('<digitisation_correct>no</digitisation_correct>')) {
				entityStatus = 6; // MARKED_BAD
			} else if (entitiesStore.newGeomList.features.find((feature) => feature.properties?.entity_id === entityId)) {
				entityStatus = 3; // NEW_GEOM
			} else {
				entityStatus = 2; // SURVEY_SUBMITTED
			}

			entitiesStore.updateEntityStatus(projectId, {
				entity_id: selectedEntity?.entity_id,
				status: entityStatus,
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
			const target = `(${commonStore.locale.toLowerCase()})`;

			// language in OdkWebForm corresponding to app language
			const lang = odkForm.languages.find((it: any) => it?.language.toLowerCase().includes(target));

			// dictionary of languages and the numbers of translations for each
			const lang_translations = Object.fromEntries(
				odkForm.languages.map(({ language }: { language: string }) => [
					language,
					odkForm.definition.model.itextTranslations
						.get(language)
						?.children.filter((node: any) => ![undefined, null, '', '-'].includes(node.children[0].value)).length || 0,
				]),
			);

			// the maximum number of text translations for a language
			// this gives us the upper bound of how much a "fully translated" form should have
			const maxTranslations = Math.max(...(Object.values(lang_translations) as number[]));

			// only consider languages with at least 50% of translations enough to enable that language for display
			const displayableLanguages = odkForm.languages.filter(
				({ language }: { language: string }) => lang_translations[language] / maxTranslations > 0.5,
			);

			// check if language has enough valid translations to display
			if (displayableLanguages.includes(lang)) {
				odkForm?.setLanguage(lang);
			} else {
				drawerLabel = m['forms.default_language_warning']() || '';
			}

			const nodes = odkForm.getChildren();

			// select feature that you clicked on map
			const featureNode = nodes.find((it: any) => it.definition.nodeset === '/data/feature');
			if (featureNode) {
				featureNode?.setValueState([entityId]);

				// hide this node because we don't need to see it after setting the value
				featureNode.state.clientState.relevant = false;
			}

			nodes.find((it: any) => it.definition.nodeset === '/data/task_id')?.setValueState(`${taskId}`);

			if (selectedEntity?.osmid) {
				nodes.find((it: any) => it.definition.nodeset === '/data/xid')?.setValueState(`${selectedEntity?.osmid}`);
			}

			if (selectedEntityCoordinate) {
				const [longitude, latitude] = selectedEntityCoordinate.coordinate as unknown as [number, number];
				nodes
					.find((it: any) => it.definition.nodeset === '/data/xlocation')
					?.setValueState(`${latitude} ${longitude} 0.0 0.0`);
			}
		}
	}

	$effect(() => {
		// making sure we re-run whenever one of the following reactive variables changes
		display;
		projectId;
		entityId;
		if (display) {
			startDate = new Date().toISOString();
		}
	});

	const handleIframe: Action = (node) => {
		$effect(() => {
			const iframe = node as unknown as HTMLIFrameElement;

			// we want to rerun this $effect function whenever a new iframe is rendered
			const intervalId = setInterval(() => {
				webFormsRef = iframe?.contentDocument?.querySelector('odk-web-form') || undefined;
				if (webFormsRef) {
					clearInterval(intervalId);
					webFormsRef.addEventListener('submit', handleSubmit);
					webFormsRef.addEventListener('odkForm', handleOdkForm);
				}
			}, 10);

			// clear interval when re-run
			return () => {
				clearInterval(intervalId);
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
	class="forms-wrapper-drawer"
>
	{#await odkWebFormPromise then odkWebFormUrl}
		{#if entityId}
			{#key projectId}
				{#await formXmlPromise then formXml}
					{#await formMediaPromise then formMedia}
						{#key entityId}
							{#key commonStore.locale}
								<div style="font-size: 10pt; left: 0; padding: 10px; position: absolute; right: 0; text-align: center;">
									{drawerLabel}
								</div>
								<iframe
									class="iframe"
									style:border="none"
									style:height="100%"
									use:handleIframe
									title="odk-web-forms-wrapper"
									src={`./web-forms.html?projectId=${projectId}&entityId=${entityId}&formXml=${formXml}&odkWebFormUrl=${odkWebFormUrl}&formMedia=${encodeURIComponent(JSON.stringify(formMedia))}`}
								></iframe>
							{/key}
						{/key}
					{/await}
				{/await}
			{/key}
		{/if}
	{/await}
</hot-drawer>
