<script lang="ts">
	import '$styles/forms.css';
	import type { Action } from 'svelte/action';
	import type { SlDrawer } from '@shoelace-style/shoelace';

	import { getCommonStore } from '$store/common.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { fetchCachedBlobUrl, fetchFormMediBlobUrls } from '$lib/api/fetch';
	import { getDeviceId } from '$lib/utils/random';
	import { m } from '$translations/messages.js';

	type Props = {
		display: Boolean;
		entityId: string | undefined;
		projectId: number | undefined;
		formXml: string | undefined;
		taskId: number | undefined;
		webFormsRef: HTMLElement | undefined;
	};

	const WEB_FORMS_IFRAME_ID = '7f86f661-efd6-4cc6-b068-48dd7eb53dbb';

	// example: convert mapper.fmtm.localhost to fmtm.localhost
	const FMTM_DOMAIN = window.location.hostname.replace('mapper.', '');

	const commonStore = getCommonStore();
	const loginStore = getLoginStore();
	const entitiesStore = getEntitiesStatusStore();
	const selectedEntity = $derived(entitiesStore.selectedEntity);

	let {
		display = $bindable(false),
		entityId,
		webFormsRef = $bindable(undefined),
		projectId,
		formXml,
		taskId,
	}: Props = $props();
	let drawerRef: SlDrawer;
	let odkForm: any;
	let startDate: string | undefined;

	let drawerLabel = $state('');
	let uploading = $state(false);
	let uploadingMessage = $state('');

	const odkWebFormPromise = fetchCachedBlobUrl(
		'https://hotosm.github.io/web-forms/odk-web-form.js',
		commonStore.config.cacheName,
		true, // clean old cache entries
	);

	const webFormPagePromise = fetchCachedBlobUrl('/web-forms.html', commonStore.config.cacheName, true);

	const formMediaPromise = fetchFormMediBlobUrls(projectId!);

	function insertExtraMetadataIntoSubmissionXml(submissionXml: string): string {
		// missing start, end, today, phonenumber, deviceid, username, email, instruction
		// included xid, xlocation, task_id, status,image number

		// entity id isn't included in the payload by default because we marked it as not relevant earlier
		// (in order to hide it from the user's display)
		submissionXml = submissionXml.replace('<warmup/>', `<warmup/><feature>${entityId}</feature>`);

		// feature exists question isn't in the payload if it was intentionally hidden because it's a new feature
		// the verification question is also hidden because it depends on the feature_exists question
		if (!submissionXml.includes('<feature_exists>') && selectedEntity?.created_by) {
			submissionXml = submissionXml.replace(
				'<survey_questions>',
				`<feature_exists>yes</feature_exists><survey_questions>`,
			);
			submissionXml = submissionXml.replace(
				'</survey_questions>',
				`</survey_questions><verification><digitisation_correct>yes</digitisation_correct></verification>`,
			);
		}

		submissionXml = submissionXml.replace('<start/>', `<start>${startDate}</start>`);
		submissionXml = submissionXml.replace('<end/>', `<end>${new Date().toISOString()}</end>`);
		submissionXml = submissionXml.replace('<today/>', `<today>${new Date().toISOString().split('T')[0]}</today>`);

		const authDetails = loginStore?.getAuthDetails;
		if (authDetails?.username) {
			submissionXml = submissionXml.replace('<username/>', `<username>${authDetails?.username}</username>`);
		}

		if (authDetails?.email_address) {
			submissionXml = submissionXml.replace('<email/>', `<email>${authDetails?.email_address}</email>`);
		}

		if (entitiesStore.userLocationCoord) {
			const [longitude, latitude] = entitiesStore.userLocationCoord as [number, number];
			// add 0.0 for altitude and 10.0 for accuracy as defaults
			submissionXml = submissionXml.replace('<warmup/>', `<warmup>${latitude} ${longitude} 0.0 0.0</warmup>`);
		}

		submissionXml = submissionXml.replace('<deviceid/>', `<deviceid>${FMTM_DOMAIN}:${getDeviceId()}</deviceid>`);

		return submissionXml;
	}

	// We need this as ODK Central does not seem to automatically update the entity status based on submitted data
	// Using ODK Collect this works, but something in the web-forms workflow is broken to not allow this for now
	function updateEntityStatusBasedOnSubmissionXml(submissionXml: string) {
		let entityStatus = null;
		if (submissionXml.includes('<feature_exists>no</feature_exists>')) {
			entityStatus = 6; // MARKED_BAD
		} else if (submissionXml.includes('<digitisation_correct>no</digitisation_correct>')) {
			entityStatus = 6; // MARKED_BAD
		} else {
			entityStatus = 2; // SURVEY_SUBMITTED
		}

		const submissionIdMatch = submissionXml.match(/<submission_ids>(.*?)<\/submission_ids>/);
		let submissionIds = submissionIdMatch?.[1] ?? '';

		if (selectedEntity?.submission_ids) {
			submissionIds = `${selectedEntity.submission_ids},${submissionIds}`;
		}

		entitiesStore.updateEntityStatus(projectId, {
			entity_id: selectedEntity?.entity_id,
			status: entityStatus,
			// NOTE here we don't translate the field as English values are always saved as the Entity label
			label: `Feature ${selectedEntity?.osm_id}`,
			submission_ids: submissionIds,
		});
	}

	function handleSubmit(payload: any) {
		(async () => {
			if (!payload.detail || !projectId) return;

			const { instanceFile, attachments = [] } = await payload.detail[0].data[0];
			let submissionXml = await instanceFile.text();
			submissionXml = insertExtraMetadataIntoSubmissionXml(submissionXml);

			uploadingMessage = m['forms.uploading']() || 'uploading';
			uploading = true;

			// Submit the XML + any submission media
			await entitiesStore.createNewSubmission(projectId, submissionXml, attachments);

			uploading = false;
			updateEntityStatusBasedOnSubmissionXml(submissionXml);
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

			if (selectedEntity?.osm_id) {
				nodes.find((it: any) => it.definition.nodeset === '/data/xid')?.setValueState(`${selectedEntity?.osm_id}`);
			}
			if (entitiesStore.selectedEntityJavaRosaGeom || selectedEntity?.geometry) {
				nodes
					.find((it: any) => it.definition.nodeset === '/data/xlocation')
					?.setValueState(entitiesStore.selectedEntityJavaRosaGeom || selectedEntity?.geometry);
			}

			const featureExistsNode = nodes.find((it: any) => it.definition.nodeset === '/data/feature_exists');
			// If the `created_by` field exists, then it must be a new feature
			if (featureExistsNode && selectedEntity?.created_by) {
				featureExistsNode?.setValueState('yes');

				// hide this node because we don't need to see it after setting the value
				featureExistsNode.state.clientState.relevant = false;
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

<sl-drawer
	id="odk-web-forms-drawer"
	bind:this={drawerRef}
	contained
	open={display}
	placement="start"
	class="forms-wrapper-drawer"
>
	{#await odkWebFormPromise then odkWebFormUrl}
		{#await webFormPagePromise then webFormPageUrl}
			{#if entityId}
				{#key projectId}
					{#await formMediaPromise then formMedia}
						{#key entityId}
							{#key commonStore.locale}
								{#if uploading}
									<div id="web-forms-uploader">
										<div id="uploading-inner">
											<div id="spinner"></div>
											{uploadingMessage}
										</div>
									</div>
								{:else}
									{#if drawerLabel}
										<div
											style="background: white; font-size: 10pt; left: 0; padding: 10px; position: absolute; right: 0; text-align: center;"
										>
											{drawerLabel}
										</div>
									{/if}
									<iframe
										class="iframe"
										style="border: none; height: 100%; height: -webkit-fill-available;"
										use:handleIframe
										title="odk-web-forms-wrapper"
										id={WEB_FORMS_IFRAME_ID}
										name={WEB_FORMS_IFRAME_ID}
										src={`${webFormPageUrl}`}
										data-project-id={projectId}
										data-entity-id={entityId}
										data-form-xml={formXml}
										data-odk-web-form-url={odkWebFormUrl}
										data-form-media={encodeURIComponent(JSON.stringify(formMedia))}
										data-css-file={commonStore.config?.cssFileWebformsOverride || ''}
									></iframe>
								{/if}
							{/key}
						{/key}
					{/await}
				{/key}
			{/if}
		{/await}
	{/await}
</sl-drawer>

<style>
	/* from https://www.w3schools.com/howto/howto_css_loader.asp */
	#spinner {
		border: 16px solid var(--sl-color-neutral-300);
		border-top: 16px solid var(--sl-color-primary-700);
		border-radius: 50%;
		width: 120px;
		height: 120px;
		animation: spin 2s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	#uploading-inner {
		font-size: 30px;
		left: 50%;
		position: absolute;
		transform: translate(-50%, -50%);
		top: 40%;
	}
</style>
