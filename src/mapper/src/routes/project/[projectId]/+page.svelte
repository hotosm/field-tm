<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import './page.css';
	import type { PageData } from './$types';
	import { onMount, onDestroy } from 'svelte';
	import { online } from 'svelte/reactivity/window';
	import type { ShapeStream } from '@electric-sql/client';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	import type SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';

	import type { ProjectTask } from '$lib/types';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import { m } from '$translations/messages.js';
	import { DbApiSubmission } from '$lib/db/api-submissions.ts';
	import { sendNextQueuedSubmissionToApi } from '$lib/api/fetch';
	import { openOdkCollectNewFeature } from '$lib/odk/collect';
	import { convertDateToTimeAgo } from '$lib/utils/datetime';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getProjectSetupStepStore, getCommonStore, getAlertStore } from '$store/common.svelte.ts';
	import { readFileFromOPFS } from '$lib/fs/opfs';
	import { loadOfflineExtract, writeOfflineExtract } from '$lib/map/extracts';
	import { getNewOsmId } from '$lib/utils/random';

	import ImportQrGif from '$assets/images/importQr.gif';
	import BottomSheet from '$lib/components/bottom-sheet.svelte';
	import MapComponent from '$lib/components/map/main.svelte';
	import QRCodeComponent from '$lib/components/qrcode.svelte';
	import OfflineComponent from '$lib/components/offline/index.svelte';
	import DialogTaskActions from '$lib/components/dialog-task-actions.svelte';
	import DialogEntityActions from '$lib/components/dialog-entities-actions.svelte';
	import OdkWebFormsWrapper from '$lib/components/forms/wrapper.svelte';
	import More from '$lib/components/more/index.svelte';
	import Editor from '$lib/components/editor/editor.svelte';

	interface Props {
		data: PageData;
	}

	const { data }: Props = $props();
	const { project, projectId, db } = data;

	const { odk_form_xml } = project;
	const formXmlBlob = new Blob([odk_form_xml], { type: 'application/xml' });
	const formXmlUrl = URL.createObjectURL(formXmlBlob);

	let webFormsRef: HTMLElement | undefined = $state();
	let displayWebFormsDrawer = $state(false);

	let maplibreMap: maplibregl.Map | undefined = $state(undefined);
	let tabGroup: SlTabGroup | undefined = $state(undefined);
	let openedActionModal: 'entity-modal' | 'task-modal' | null = $state(null);
	let infoDialogRef: SlDialog | null = $state(null);
	let isDrawEnabled: boolean = $state(false);
	let latestEventTime: string = $state('');
	let isGeometryCreationLoading: boolean = $state(false);
	let timeout: NodeJS.Timeout | undefined = $state();

	const taskStore = getTaskStore();
	const entitiesStore = getEntitiesStatusStore();
	const commonStore = getCommonStore();
	const alertStore = getAlertStore();

	let taskEventStream: ShapeStream | undefined;
	let entityStatusStream: ShapeStream | undefined;
	let lastOnlineStatus: boolean | null = $state(null);
	let subscribeDebounce: ReturnType<typeof setTimeout> | null = $state(null);

	const latestEvent = $derived(taskStore.latestEvent);
	const commentMention = $derived(taskStore.commentMention);
	// Make db accessible via store
	commonStore.setDb(db);
	commonStore.setUseOdkCollectOverride(project.use_odk_collect);

	// Update the geojson task states when a new event is added
	$effect(() => {
		if (latestEvent) {
			taskStore.appendTaskStatesToFeatcol(db, projectId, project.tasks);
		}
	});

	$effect(() => {
		let taskIdIndexMap: Record<number, number> = {};
		if (project?.tasks && project?.tasks?.length > 0) {
			project?.tasks?.forEach((task: ProjectTask) => {
				taskIdIndexMap[task.id] = task.project_task_index;
			});
		}
		taskStore.setTaskIdIndexMap(taskIdIndexMap);
	});

	// update the latest time time every minute
	$effect(() => {
		const updateLatestTime = () => {
			if (latestEvent?.created_at) {
				latestEventTime = convertDateToTimeAgo(latestEvent.created_at);
			}
		};

		updateLatestTime();

		const interval = setInterval(updateLatestTime, 60000);

		return () => clearInterval(interval); // Cleanup interval on unmount
	});

	function zoomToTask(taskId: number, fitOptions?: Record<string, any> = { duration: 0 }) {
		const taskObj = project.tasks.find((task: ProjectTask) => task.id === taskId);

		if (!taskObj) return;
		// Set as selected task for buttons
		taskStore.setSelectedTaskId(db, taskObj.id, taskObj?.task_index);

		const taskPolygon = polygon(taskObj.outline.coordinates);
		const taskBuffer = buffer(taskPolygon, 5, { units: 'meters' });
		if (taskBuffer && maplibreMap) {
			const taskBbox: [number, number, number, number] = bbox(taskBuffer) as [number, number, number, number];
			maplibreMap.fitBounds(taskBbox, fitOptions);
		}

		// Open the map tab
		tabGroup.show('map');
	}

	// if the content-length is less than 2MB, download
	const storeFgbExtractOffline = async () => {
		const response = await fetch(project.data_extract_url, {
			method: 'HEAD',
		});
		const contentLength = response.headers.get('Content-Length');
		if (!contentLength) return;

		const maxAutoDownloadSize = 2 * 1024 * 1024; // 2MB
		const fileSize = parseInt(contentLength, 10);
		if (fileSize <= maxAutoDownloadSize) {
			writeOfflineExtract(projectId, project.data_extract_url);
		}
	};

	async function subscribeToAllStreams() {
		// Ensure unsubscribed first
		unsubscribeFromAllStreams();

		taskEventStream = await taskStore.getTaskEventStream(db, projectId);
		entityStatusStream = await entitiesStore.getEntityStatusStream(db, projectId);
	}

	onMount(async () => {
		if (online.current) {
			// Only subscribe if currently online
			subscribeToAllStreams();
		}

		// Note we need this for now, as the task outlines are from API, while task
		// events are from pglite / sync. We pass through the task outlines.
		taskStore.appendTaskStatesToFeatcol(db, projectId, project.tasks);

		// check if Fgb extract exists in OPFS
		const offlineExtractFile = await readFileFromOPFS(`${projectId}/extract.fgb`);
		if (offlineExtractFile) {
			loadOfflineExtract(projectId);
			return;
		}

		// 20s delay to defer saving data until after initial page load
		timeout = setTimeout(() => {
			storeFgbExtractOffline();
		}, 20000);
	});

	async function unsubscribeFromAllStreams() {
		taskStore.unsubscribeEventStream();
		entitiesStore.unsubscribeEntitiesStream();
	}

	onDestroy(() => {
		unsubscribeFromAllStreams();

		taskStore.clearTaskStates();
		entitiesStore.setFgbOpfsUrl('');

		if (timeout) clearTimeout(timeout);
	});

	/**
	 * Iterate and attempt to send all pending API submissions from the local database.
	 * 
	 * This function is triggered in two scenarios:
	 *  - Automatically when coming back online (debounced via $effect)
	 *  - Manually via the sync button in the map UI
	 * 
	 * Each submission is sent sequentially. If the API acknowledges receipt (status becomes 'RECEIVED'),
	 * it is considered a success. Failures are logged but not retried immediately (they remain in 'PENDING').
	 * 
	 * Syncing status is tracked via `commonStore.offlineDataIsSyncing` and alerts are shown after each attempt.
	 */
	 async function iterateAndSendOfflineSubmissions(): Promise<boolean> {
		if (!db) return false;

		let sent = 0;
		let failed = 0;

		// Count remaining pending submissions
		const total = await DbApiSubmission.count(db);
		if (total === 0) return true; // Nothing to be done

		commonStore.setOfflineDataIsSyncing(true);
		alertStore.setAlert({
			message: `Found ${total} offline submissions.`,
			variant: 'default'
		});

		let processed = 0; // how many attempts made (success + fail)

		while (true) {
			const row = await DbApiSubmission.first(db);
			if (!row) break; // No more pending entries

			let success = false;

			try {
				let options: RequestInit;

				// Handle JSON POSTs
				if (row.content_type === 'application/json') {
					options = {
						method: row.method,
						body: JSON.stringify(row.payload.body),
						headers: {
							'Content-Type': 'application/json'
						},
						credentials: 'include'
					};
				// Handle multipart FormData posts (base64 encoded attachments)
				} else if (row.content_type === 'multipart/form-data') {
					const form = new FormData();
					form.append('submission_xml', row.payload.form.submission_xml);

					for (const f of row.payload.form.submission_files) {
						const byteString = atob(f.base64.split(',')[1]);
						const arrayBuffer = new Uint8Array(byteString.length);
						for (let i = 0; i < byteString.length; i++) {
							arrayBuffer[i] = byteString.charCodeAt(i);
						}
						const blob = new Blob([arrayBuffer], { type: f.type });
						const file = new File([blob], f.name, { type: f.type });
						form.append('submission_files', file);
					}

					options = {
						method: row.method,
						body: form,
						credentials: 'include'
					};
				} else {
					throw new Error(`Unsupported content_type: ${row.content_type}`);
				}

				const res = await fetch(row.url, options);

				if (!res.ok) throw new Error(`HTTP ${res.status}`);
				success = true;
			} catch (err) {
				console.error('Offline send failed:', err);
				success = false;
			}

			processed++;

			if (success) {
				sent++;
				// This is bad ux if multiple send in quick succession
				// alertStore.setAlert({
				// 	message: `Successfully sent offline data ${sent}/${total} to API`,
				// 	variant: 'success'
				// });
				await DbApiSubmission.deleteById(db, row.id);
			} else {
				failed++;
				alertStore.setAlert({
					message: `Failed to send offline data ${processed}/${total} to API (Failures: ${failed})`,
					variant: 'danger'
				});
			}

			commonStore.setOfflineSyncPercentComplete((processed / total) * 100);
			// Wait 1 second until next API call
			await new Promise((resolve) => setTimeout(resolve, 1000));
		}

		commonStore.setOfflineSyncPercentComplete(null);
		commonStore.setOfflineDataIsSyncing(false);

		if (failed < 1) {
			alertStore.setAlert({
				message: `Finished sending offline data.`,
				variant: 'success'
			});
			// Clear the table if all sent successfully
			await DbApiSubmission.clear(db);
			return true;
		} else {
			alertStore.setAlert({
				message: `Offline sync: (${sent} succeeded, ${failed} failed).`,
				variant: 'warning'
			});
			return false;
		}
	}

	async function triggerManualOfflineDataSync() {
		if (!db) return;
		const success = await iterateAndSendOfflineSubmissions();
		// Return immediately if there were submission failures, to prevent overwriting entities below
		if (!success) return;

		// Wait 3 seconds for everything to process on the backend, before requesting new data
		// + we need to set spinner again, as set false once offline sync done.
		// (we have the 3 second gap until syncEntityStatusManually is triggered)
		commonStore.setOfflineDataIsSyncing(true);
		await new Promise((resolve) => setTimeout(resolve, 3000));
		commonStore.setOfflineDataIsSyncing(false);

		// This call has it's own loading param
		await entitiesStore.syncEntityStatusManually(db, projectId)
	}

	async function handleOnlineSync() {
		// Also send any pending submissions first
		const success = await iterateAndSendOfflineSubmissions();

		// Once done, subscribe to electric ShapeStreams
		if (success) {
			subscribeToAllStreams();
		} else {
			console.warn("Offline sync failed; subscribing to latest ShapeStreams anyway...");
			subscribeToAllStreams();
		}
	}

	// Subscribe / unsubscribe from streams based on connectivity
	// note: the effect rune can't accept async, but this is fine
	// note: we also need to debounce this to prevent infinite loop
	$effect(() => {
		const isOnline = online.current;

		if (isOnline === lastOnlineStatus) return;
		lastOnlineStatus = isOnline;

		if (subscribeDebounce) {
			clearTimeout(subscribeDebounce);
			subscribeDebounce = null;
		}

		subscribeDebounce = setTimeout(() => {
			if (isOnline) {
				// Delay initial sync and subscriptions by 5 seconds after load (reduce memory spike)
				setTimeout(() => {
					handleOnlineSync();
				}, 5000);
			} else {
				unsubscribeFromAllStreams();
			}
		}, 200);
	});

	const projectSetupStepStore = getProjectSetupStepStore();

	$effect(() => {
		// if project loaded for the first time, set projectSetupStep to 1 else get it from localStorage
		if (!localStorage.getItem(`project-${projectId}-setup`)) {
			// if webforms enabled, avoid project load in odk step
			if (commonStore.enableWebforms) {
				localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['task_selection'].toString());
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['task_selection']);
			} else {
				localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['odk_project_load'].toString());
				projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['odk_project_load']);
			}
		} else {
			const projectStep = localStorage.getItem(`project-${projectId}-setup`);
			projectSetupStepStore.setProjectSetupStep(projectStep ? +projectStep : 0);
		}
		// if project loaded for the first time then show qrcode tab
		if (+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load']) {
			if (tabGroup) {
				tabGroup.updateComplete.then(() => {
					tabGroup.show('qrcode');
				});
			}
		}
	});

	let newFeatureDrawInstance: any = $state(null);
	let newFeatureGeom: any = $state(null);

	function cancelMapNewFeatureInODK() {
		newFeatureDrawInstance.clear();
		isDrawEnabled = false;
		newFeatureDrawInstance = null;
		newFeatureGeom = null;
	}

	async function mapNewFeatureInODK() {
		{
			/*
			1: create entity in ODK of newly created feature
			2: create geom record to show the feature on map
			3: pass entity uuid to ODK intent URL as a param 
			*/
		}
		try {
			isGeometryCreationLoading = true;
			const entityUuid = crypto.randomUUID();
			const newOsmId = getNewOsmId();
			// NOTE here the top level 'id' field is also required for the backend processing
			// NOTE the id field is the osm_id, not the entity id!
			await entitiesStore.createEntity(db, projectId, entityUuid, {
				type: 'FeatureCollection',
				features: [{ type: 'Feature', id: newOsmId, geometry: newFeatureGeom, properties: {
					project_id: projectId,
					osm_id: newOsmId,
					task_id: taskStore.selectedTaskIndex || '',
					is_new: '✅', // NOTE usage of an emoji is valid here
					status: '0', // TODO update this to use the enum / mapping
				}}],
			});
			cancelMapNewFeatureInODK();

			if (commonStore.enableWebforms) {
				await entitiesStore.setSelectedEntityId(entityUuid);
				openedActionModal = null;
				const entityOsmId = entitiesStore.getOsmIdByEntityId(entityUuid);
				entitiesStore.updateEntityStatus(db, projectId, {
					entity_id: entityUuid,
					status: 1,
					label: `Feature ${entityOsmId}`
				});
				displayWebFormsDrawer = true;
			} else {
				openOdkCollectNewFeature(project?.odk_form_id, entityUuid);
			}
		} catch (error) {
			console.error(error);
			alertStore.setAlert({ message: 'Unable to create entity', variant: 'danger' });
		} finally {
			isGeometryCreationLoading = false;
		}
	}
</script>

<!-- There is a new event to display in the top right corner -->
{#if latestEvent}
	<div id="notification-banner" class="floating-msg">
		<b>{latestEventTime}</b>&nbsp;| {latestEvent.event}
		on task {taskStore.taskIdIndexMap[latestEvent.task_id]} by {latestEvent.username || 'anon'}
	</div>
{/if}

<!-- Alert shown when user is tagged on a comment when they is active -->
{#if commentMention}
	<div class="alert-msg">
		<sl-alert open={true} variant="neutral">
			<sl-icon slot="icon" name="chat"></sl-icon>
			<strong>{commentMention?.username} mentioned you on a comment</strong><br />
			<p>{commentMention?.comment?.replace(/#submissionId:uuid:[\w-]+|#featureId:[\w-]+/g, '')?.trim()}</p>
			<div class="page-content">
				<sl-button
					onclick={() => {
						taskStore.dismissCommentMention();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							taskStore.dismissCommentMention();
						}
					}}
					role="button"
					tabindex="0"
					size="small"
				>
					<span>Dismiss</span>
				</sl-button>
				<sl-button
					onclick={() => {
						zoomToTask(commentMention.task_id, { duration: 0, padding: { bottom: 325 } });
						const osmIdStr = commentMention?.comment?.split(' ')?.[1]?.replace('#featureId:', '');
						const osmId = Number(osmIdStr);
						const entity = entitiesStore.getEntityByOsmId(osmId);
						if (entity) {
							entitiesStore.setSelectedEntityId(entity.entity_id);
						}
						openedActionModal = 'entity-modal';
						taskStore.dismissCommentMention();
					}}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') {
							const osmIdStr = commentMention?.comment?.split(' ')?.[1]?.replace('#featureId:', '');
							const osmId = Number(osmIdStr);
							const entity = entitiesStore.getEntityByOsmId(osmId);
							if (entity) {
								entitiesStore.setSelectedEntityId(entity.entity_id);
							}
							openedActionModal = 'entity-modal';
							taskStore.dismissCommentMention();
						}
					}}
					role="button"
					tabindex="0"
					size="small"
				>
					<span>Tap to View</span>
				</sl-button>
			</div>
		</sl-alert>
	</div>
{/if}

<!-- The main page -->
<div class="main-page">
	<MapComponent
		setMapRef={(map) => {
			maplibreMap = map;
		}}
		toggleActionModal={(value) => {
			openedActionModal = value;
		}}
		projectOutlineCoords={project.outline.coordinates}
		{projectId}
		entitiesUrl={project.data_extract_url}
		primaryGeomType={project.primary_geom_type}
		draw={isDrawEnabled}
		drawGeomType={project?.new_geom_type}
		handleDrawnGeom={(drawInstance, geom) => {
			newFeatureDrawInstance = drawInstance;
			newFeatureGeom = geom;
			// after drawing a feature, allow user to modify the drawn feature
			newFeatureDrawInstance.setMode('select');
		}}
		syncButtonTrigger={async () => {
			await triggerManualOfflineDataSync();
		}}
	></MapComponent>

	{#if newFeatureGeom}
		<div class="proceed-dialog">
			<div class="proceed-dialog-content">
				<p>{m['map.geometry_correct_place']()}</p>
				<div class="buttons">
					<sl-button
						onclick={() => {
							cancelMapNewFeatureInODK();
						}}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') {
								cancelMapNewFeatureInODK();
							}
						}}
						role="button"
						tabindex="0"
						size="small"
						variant="secondary"
					>
						<span>{m['popup.cancel']()}</span>
					</sl-button>
					<sl-button
						onclick={() => mapNewFeatureInODK()}
						onkeydown={(e: KeyboardEvent) => {
							e.key === 'Enter' && mapNewFeatureInODK();
						}}
						role="button"
						tabindex="0"
						size="small"
						variant="primary"
						loading={isGeometryCreationLoading}
					>
						<span>PROCEED</span>
					</sl-button>
				</div>
			</div>
		</div>
	{/if}
	<!-- task action buttons popup -->
	<DialogTaskActions
		isTaskActionModalOpen={openedActionModal === 'task-modal'}
		toggleTaskActionModal={(value) => {
			openedActionModal = value ? 'task-modal' : null;
		}}
		selectedTab={commonStore.selectedTab}
		projectData={project}
		clickMapNewFeature={() => {
			openedActionModal = null;
			isDrawEnabled = true;
		}}
	/>
	<DialogEntityActions
		isTaskActionModalOpen={openedActionModal === 'entity-modal'}
		toggleTaskActionModal={(value) => {
			openedActionModal = value ? 'entity-modal' : null;
		}}
		selectedTab={commonStore.selectedTab}
		projectData={project}
		bind:displayWebFormsDrawer
	/>
	{#if commonStore.selectedTab !== 'map'}
		<BottomSheet onClose={() => tabGroup.show('map')}>
			{#if commonStore.selectedTab === 'events'}
				<More projectData={project} zoomToTask={(taskId) => zoomToTask(taskId)}></More>
			{/if}
			{#if commonStore.selectedTab === 'offline'}
				<OfflineComponent projectId={project.id} {project} />
			{/if}
			{#if commonStore.selectedTab === 'qrcode'}
				<QRCodeComponent class="map-qr" {infoDialogRef} projectName={project.name} projectOdkToken={project.odk_token}>
					<!-- Open ODK Button (Hide if it's project walkthrough step) -->
					{#if +(projectSetupStepStore.projectSetupStep || 0) !== projectSetupStepEnum['odk_project_load']}
						<sl-button size="small" variant="primary" href="odkcollect://form/{project.odk_form_id}">
							<span>{m['odk.open']()}</span></sl-button
						>
					{/if}
				</QRCodeComponent>
			{/if}
			{#if commonStore.selectedTab === 'instructions'}
				<p class="bottom-sheet-header">{m['stack_group.instructions']()}</p>
				{#if project?.per_task_instructions}
					<Editor editable={false} content={project?.per_task_instructions} />
				{:else}
					<div class="active-stack-instructions">
						<p>{m['index.no_instructions']()}</p>
					</div>
				{/if}
			{/if}
		</BottomSheet>
		<hot-dialog bind:this={infoDialogRef} class="dialog-overview" no-header>
			<div class="content">
				<img src={ImportQrGif} alt="manual process of importing qr code gif" class="manual-qr-gif" />
				<sl-button
					onclick={() => infoDialogRef?.hide()}
					onkeydown={(e: KeyboardEvent) => {
						e.key === 'Enter' && infoDialogRef?.hide();
					}}
					role="button"
					tabindex="0"
					size="small"
					variant="primary"
				>
					<span>CLOSE</span>
				</sl-button>
			</div>
		</hot-dialog>
	{/if}

	{#if displayWebFormsDrawer === false}
		<sl-tab-group
			class="web-forms-drawer"
			placement="bottom"
			no-scroll-controls
			onsl-tab-show={(e: CustomEvent<{ name: string }>) => {
				commonStore.setSelectedTab(e.detail.name);
				if (
					e.detail.name !== 'qrcode' &&
					+(projectSetupStepStore.projectSetupStep || 0) === projectSetupStepEnum['odk_project_load']
				) {
					localStorage.setItem(`project-${projectId}-setup`, projectSetupStepEnum['task_selection'].toString());
					projectSetupStepStore.setProjectSetupStep(projectSetupStepEnum['task_selection']);
				}
			}}
			bind:this={tabGroup}
		>
			<sl-tab slot="nav" panel="map">
				<hot-icon name="map"></hot-icon>
			</sl-tab>
			<sl-tab slot="nav" panel="offline">
				<hot-icon name="wifi-off"></hot-icon>
			</sl-tab>
			{#if !commonStore.enableWebforms}
				<sl-tab slot="nav" panel="qrcode">
					<hot-icon name="qr-code"></hot-icon>
				</sl-tab>
			{/if}
			<sl-tab slot="nav" panel="events">
				<hot-icon name="three-dots"></hot-icon>
			</sl-tab>
		</sl-tab-group>
	{/if}

	<OdkWebFormsWrapper
		bind:webFormsRef
		bind:display={displayWebFormsDrawer}
		{projectId}
		formXml={formXmlUrl}
		entityId={entitiesStore.selectedEntityId || undefined}
		taskId={taskStore.selectedTaskIndex || undefined}
	/>
</div>
