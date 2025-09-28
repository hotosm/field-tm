<script lang="ts">
	import '$styles/page.css';
	import '$styles/button.css';
	import './page.css';
	import type { PageData } from './$types';
	import { onMount, onDestroy } from 'svelte';
	import { online } from 'svelte/reactivity/window';
	import { polygon } from '@turf/helpers';
	import { buffer } from '@turf/buffer';
	import { bbox } from '@turf/bbox';
	import type SlTabGroup from '@shoelace-style/shoelace/dist/components/tab-group/tab-group.component.js';
	import type SlDialog from '@shoelace-style/shoelace/dist/components/dialog/dialog.component.js';

	import type { ProjectTask, DbProjectType } from '$lib/types';
	import { FieldMappingAppEnum } from '$lib/types';
	import { projectSetupStep as projectSetupStepEnum } from '$constants/enums.ts';
	import { m } from '$translations/messages.js';
	import { openOdkCollectNewFeature } from '$lib/odk/collect';
	import { convertDateToTimeAgo } from '$lib/utils/datetime';
	import { getTaskStore } from '$store/tasks.svelte.ts';
	import { getLoginStore } from '$store/login.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getProjectSetupStepStore, getCommonStore, getAlertStore } from '$store/common.svelte.ts';
	import { readFileFromOPFS } from '$lib/fs/opfs';
	import { loadOfflineExtract, writeOfflineExtract } from '$lib/map/extracts';
	import { getNewOsmId } from '$lib/utils/random';

	import ImportQrGif from '$assets/images/importQr.gif';
	import BottomSheet from '$lib/components/bottom-sheet.svelte';
	import MapComponent from '$lib/components/map/main.svelte';
	import QRCodeComponent from '$lib/components/qrcode.svelte';
	// import OfflineComponent from '$lib/components/offline/index.svelte';
	import DialogTaskActions from '$lib/components/dialog-task-actions.svelte';
	import DialogEntityActions from '$lib/components/dialog-entities-actions.svelte';
	import OdkWebFormsWrapper from '$lib/components/forms/wrapper.svelte';
	import More from '$lib/components/more/index.svelte';
	import MyTasks from '$lib/components/my-tasks.svelte';
	import Editor from '$lib/components/editor/editor.svelte';

	interface Props {
		data: PageData;
	}

	const { data }: Props = $props();
	const { project: initialProject, projectId } = data;
	let project: DbProjectType | undefined = initialProject;

	let formXmlUrl: string | null = $state(null);
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

	const loginStore = getLoginStore();
	const taskStore = getTaskStore();
	const entitiesStore = getEntitiesStatusStore();
	const commonStore = getCommonStore();
	const alertStore = getAlertStore();

	let lastOnlineStatus: boolean | null = $state(null);
	let subscribeDebounce: ReturnType<typeof setTimeout> | null = $state(null);

	const latestEvent = $derived(taskStore.latestEvent);
	const commentMention = $derived(taskStore.commentMention);

	// Update the geojson task states when a new event is added
	$effect(() => {
		latestEvent;
		if (project) {
			taskStore.appendTaskStatesToFeatcol(project.tasks);
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
		taskStore.setSelectedTaskId(taskObj.id, taskObj?.task_index);

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

		await taskStore.startTaskEventStream(projectId);
		await entitiesStore.startEntityStatusStream(projectId);
	}

	onMount(async () => {
		if (online.current) {
			// Only subscribe if currently online (no need to await)
			subscribeToAllStreams();
		}

		// Set vars that require upstream project details set (and are not reactive)
		if (project) {
			// FIXME for now we disable webforms when in ODK mode, but perhaps we want to actually
			// FIXME use a hybrid solution in future, where ODK + WebForms can both work together?
			commonStore.setEnableWebForms(project.field_mapping_app === FieldMappingAppEnum.FIELDTM);
			const { odk_form_xml } = project;
			if (!odk_form_xml) {
				throw Error('odk_form_xml must be set for the project')
			}
			const formXmlBlob = new Blob([odk_form_xml], { type: 'application/xml' });
			formXmlUrl = URL.createObjectURL(formXmlBlob);
		}

		// Note we need this for now, as the task outlines are from API, while task
		// events are from electric sync. We pass through the task outlines.
		taskStore.appendTaskStatesToFeatcol(project.tasks);

		// check if Fgb extract exists in OPFS
		const offlineExtractFile = await readFileFromOPFS(`${projectId}/extract.fgb`);
		if (offlineExtractFile) {
			loadOfflineExtract(projectId);
			return;
		}

		// 12s delay to defer saving data until after initial page load
		timeout = setTimeout(() => {
			storeFgbExtractOffline();
		}, 12000);
	});

	async function unsubscribeFromAllStreams() {
		taskStore.unsubscribeEventStream();
		entitiesStore.unsubscribeEntitiesStream();
	}

	onDestroy(() => {
		commonStore.setSelectedTab('map');
		taskStore.clearTaskStates();
		entitiesStore.setFgbOpfsUrl('');

		if (timeout) clearTimeout(timeout);

		unsubscribeFromAllStreams();
	});

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
				// Delay initial subscriptions by 5 seconds after load (reduce memory spike)
				setTimeout(() => {
					subscribeToAllStreams();
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
			await entitiesStore.createEntity(projectId, entityUuid, {
				type: 'FeatureCollection',
				features: [
					{
						type: 'Feature',
						id: newOsmId,
						geometry: newFeatureGeom,
						properties: {
							project_id: projectId,
							osm_id: newOsmId,
							task_id: taskStore.selectedTaskIndex || '',
							status: '0', // TODO update this to use the enum / mapping
							// NOTE: 'osm|20386219' is the service user 'svcfmtm' (not a logged-in user).
							created_by: loginStore.getAuthDetails?.sub || 'osm|20386219',
						},
					},
				],
			});
			cancelMapNewFeatureInODK();

			if (commonStore.enableWebforms) {
				await entitiesStore.setSelectedEntityId(entityUuid);
				openedActionModal = null;
				const entityOsmId = entitiesStore.getOsmIdByEntityId(entityUuid);
				entitiesStore.updateEntityStatus(projectId, {
					entity_id: entityUuid,
					status: 1,
					label: `Feature ${entityOsmId}`,
				});
				displayWebFormsDrawer = true;
			} else {
				openOdkCollectNewFeature(project?.odk_form_id, entityUuid);
			}
		} catch (error) {
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
						if (!osmIdStr) return;
						const osmId = BigInt(osmIdStr);
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
							if (!osmIdStr) return;
							const osmId = BigInt(osmIdStr);
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
			await entitiesStore.syncEntityStatusManually(projectId);
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
						<span>{m['popup.proceed']()}</span>
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
			<!-- {#if commonStore.selectedTab === 'offline'}
				<OfflineComponent projectId={project.id} {project} />
			{/if} -->
			{#if commonStore.selectedTab === 'mytasks'}
				<MyTasks zoomToTask={(taskId) => zoomToTask(taskId)} />
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
		<sl-dialog bind:this={infoDialogRef} class="dialog-overview" no-header>
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
		</sl-dialog>
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
				<sl-icon name="map"></sl-icon>
			</sl-tab>
			{#if loginStore.getAuthDetails}
				<sl-tab slot="nav" panel="mytasks">
					<sl-icon name="list-task"></sl-icon>
				</sl-tab>
			{/if}
			<!-- <sl-tab slot="nav" panel="offline">
				<sl-icon name="wifi-off"></sl-icon>
			</sl-tab> -->
			{#if !commonStore.enableWebforms}
				<sl-tab slot="nav" panel="qrcode">
					<sl-icon name="qr-code"></sl-icon>
				</sl-tab>
			{/if}
			<sl-tab slot="nav" panel="events">
				<sl-icon name="three-dots"></sl-icon>
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
