<script lang="ts">
	import type { SlDrawer } from '@shoelace-style/shoelace';

	import { getCommonStore } from '$store/common.svelte.ts';

	const API_URL = import.meta.env.VITE_API_URL;
	type Props = {
		drawerRef: SlDrawer | undefined;
		entityId: string | undefined;
		projectId: number | undefined;
		webFormsRef: HTMLElement | undefined;
	};
	const commonStore = getCommonStore();
	let { drawerRef = $bindable(undefined), entityId, webFormsRef = $bindable(undefined), projectId }: Props = $props();
	let iframeRef: HTMLIFrameElement;
	let odkForm: any;
	// to-do: hide drawer upon successful submission
	function handleSubmit(payload: any) {
		(async () => {
			if (!payload.detail) return;
			const url = `${API_URL}/submission?project_id=${projectId}`;
			var data = new FormData();
			data.append('submission_xml', await payload.detail[0].data.instanceFile.text());
			await fetch(url, {
				method: 'POST',
				body: data,
			});
			drawerRef?.hide();
		})();
	}
	function handleOdkForm(evt: any) {
		if (evt?.detail?.[0]) {
			odkForm = evt.detail[0];
			console.log('set odkForm', odkForm);
			// over-write default language
			setFormLanguage(commonStore.locale);
			// select feature that you clicked on map
			odkForm
				.getChildren()
				.find((it: any) => it.definition.nodeset === '/data/feature')
				?.setValueState([entityId]);
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
			const intervalId = setInterval(() => {
				webFormsRef = iframeRef.contentDocument?.querySelector('odk-web-form') || undefined;
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
		}
	});
</script>

<hot-drawer
	id="odk-web-forms-drawer"
	bind:this={drawerRef}
	contained
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
					style="height: {window.outerHeight}px; width: 100%; z-index: 11;"
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
