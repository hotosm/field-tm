<script lang="ts">
	import '$styles/map-geolocation.css';
	import { Control, ControlButton, ControlGroup, GeoJSON, SymbolLayer, type LngLatLike } from 'svelte-maplibre';
	import type { FeatureCollection } from 'geojson';
	import MapLibreGlDirections, { LoadingIndicatorControl } from '@maplibre/maplibre-gl-directions';

	import { m } from '$translations/messages.js';
	import { GetDeviceRotation } from '$lib/map/get-device-rotation.ts';
	import { getAlertStore } from '$store/common.svelte.ts';
	import { getEntitiesStatusStore } from '$store/entities.svelte.ts';
	import { getCommonStore } from '$store/common.svelte.ts';
	import { layers } from '$assets/maplibre-directions.ts';
	import locationUrl from '$assets/images/location.png';
	import { untrack } from 'svelte';

	interface Props {
		map: maplibregl.Map | undefined;
	}

	const alertStore = getAlertStore();
	const commonStore = getCommonStore();
	const entitiesStore = getEntitiesStatusStore();

	let { map }: Props = $props();

	let rotationDeg: number | undefined = $state();
	let watchId: number | undefined = $state();
	let directions: MapLibreGlDirections | undefined = $state();
	let entityDistance: number = $state(0);
	let tooltipRef: any = $state();

	const entityToNavigate = $derived(entitiesStore.entityToNavigate);

	// initialize MapLibreGlDirections
	$effect(() => {
		if (map) {
			// load location image for destination
			map.loadImage(locationUrl).then((image) => {
				if (image) {
					map.addImage('location', image.data);
				}
			});

			if (!directions) {
				directions = new MapLibreGlDirections(map, {
					// custom styled direction layer
					layers,
					sensitiveWaypointLayers: ['maplibre-gl-directions-waypoint'],
					sensitiveSnappointLayers: ['maplibre-gl-directions-snappoint'],
					sensitiveRoutelineLayers: ['maplibre-gl-directions-routeline'],
					sensitiveAltRoutelineLayers: ['maplibre-gl-directions-alt-routeline'],
				});
				directions.interactive = false;
				const loadingIndicator = new LoadingIndicatorControl(directions);
				map.addControl(loadingIndicator);
				directions.clear();

				directions.on('fetchroutesend', (ev) => {
					entityDistance = ev.data?.routes[0].distance as number;
				});

				directions.on('removewaypoint', () => {
					if (directions.waypoints.length < 2) {
						entityDistance = 0;
					}
				});
			}
		}
	});

	function setWaypoints(geolocationCoord: [number, number], entityCoord: [number, number]) {
		const wayPointList = [geolocationCoord, entityCoord];
		if (directions) {
			directions?.setWaypoints(wayPointList);
		}
	}

	// set waypoints for navigation on every 10 seconds if navigation mode is on i.e. entityToNavigate is not null
	// don't track user geolocation
	$effect(() => {
		if (!untrack(() => entitiesStore.userLocationCoord) && !entityToNavigate) return;
		entityToNavigate?.coordinate &&
			setWaypoints(untrack(() => entitiesStore.userLocationCoord) as [number, number], entityToNavigate?.coordinate);
		const interval = setInterval(() => {
			entityToNavigate?.coordinate &&
				setWaypoints(untrack(() => entitiesStore.userLocationCoord) as [number, number], entityToNavigate?.coordinate);
		}, 10000);

		return () => {
			clearInterval(interval);
		};
	});

	// if navigation mode on, tilt map by 50 degrees
	$effect(() => {
		if (entityToNavigate && entitiesStore.toggleGeolocation) {
			map?.setPitch(50);
		} else {
			map?.setPitch(0);
		}
	});

	// if bottom sheet is open, add bottom padding for better visibility of location arrow
	$effect(() => {
		if (commonStore.selectedTab === 'map') {
			map?.setPadding({ bottom: 0, top: 0, left: 0, right: 0 });
		} else {
			map?.setPadding({ bottom: 300, top: 0, left: 0, right: 0 });
		}
	});

	// zoom to user's current location
	$effect(() => {
		if (entityToNavigate) {
			map?.setCenter(entitiesStore.userLocationCoord as LngLatLike);
			map?.setZoom(18);
		}
	});

	$effect(() => {
		if (map && entitiesStore.toggleGeolocation) {
			// zoom to user's current location
			navigator.geolocation.getCurrentPosition((position) => {
				const currentCoordinate: maplibregl.LngLatLike = [position.coords.longitude, position.coords.latitude];
				map.flyTo({
					center: currentCoordinate,
					essential: true,
					zoom: 18,
				});
			});

			// track users location
			watchId = navigator.geolocation.watchPosition(
				function (pos) {
					let latLong = [pos.coords.longitude, pos.coords.latitude];
					entitiesStore.setUserLocationCoordinate(latLong);
					if (entityToNavigate) {
						// if user is in navigation mode, update the map center according to user's live location since swiping map isn't possible
						map?.setCenter(latLong);
					}
				},
				function (error) {
					alert(`ERROR: ${error.message}`);
				},
				{
					enableHighAccuracy: true,
				},
			);
		} else {
			// stop tracking user's location on location toggle off
			if (watchId) {
				navigator.geolocation.clearWatch(watchId);
			}
		}
	});
	const isFirefox = /firefox/i.test(navigator.userAgent);
	const isSafari =
		/constructor/i.test(window.HTMLElement) ||
		(function (p) {
			return p.toString() === '[object SafariRemoteNotification]';
			// @ts-ignore
		})(!window['safari'] || (typeof safari !== 'undefined' && window['safari'].pushNotification));

	// locationGeojson: to display point on the map
	let locationGeojson: FeatureCollection = $derived({
		type: 'FeatureCollection',
		features: [
			{
				type: 'Feature',
				geometry: {
					type: 'Point',
					coordinates: entitiesStore.userLocationCoord as number[],
				},
				// firefox & safari doesn't support device orientation sensor, so if the browser any of the two set orientation to false
				properties: { orientation: !(isFirefox || isSafari) },
			},
		],
	});

	$effect(() => {
		if (map && entitiesStore.toggleGeolocation) {
			if (isFirefox || isSafari) {
				// firefox & safari doesn't support device orientation sensor
				alertStore.setAlert({
					variant: 'warning',
					message: m['map.no_orientation_sensors'](),
				});
			} else {
				// See the API specification at: https://w3c.github.io/orientation-sensor
				// We use referenceFrame: 'screen' because the web page will rotate when
				// the phone switches from portrait to landscape.
				const sensor = new AbsoluteOrientationSensor({
					frequency: 60,
					referenceFrame: 'screen',
				});
				sensor.addEventListener('reading', (event: Event) => {
					rotationDeg = GetDeviceRotation(sensor.quaternion);

					// rotate map according to device orientation
					if (entityToNavigate) map.rotateTo(rotationDeg || 0, { duration: 0 });
				});

				Promise.all([
					navigator.permissions.query({ name: 'accelerometer' as PermissionName }),
					navigator.permissions.query({ name: 'magnetometer' as PermissionName }),
					navigator.permissions.query({ name: 'gyroscope' as PermissionName }),
				]).then((results) => {
					if (results.every((result) => result.state === 'granted')) {
						sensor.start();
					} else {
					}
				});
			}
		}
	});

	function exitNavigationMode() {
		entitiesStore.setSelectedEntityId(null);
		entitiesStore.setSelectedEntityCoordinate(null);
		entitiesStore.setEntityToNavigate(null);
		directions.clear();
	}
</script>

<Control class="geolocation" position="top-left">
	<ControlGroup>
		<sl-tooltip
			bind:this={tooltipRef}
			placement="right"
			hoist
			open
			trigger="manual"
			onclick={() => tooltipRef.hide()}
			onkeydown={(e: KeyboardEvent) => {
				e.key === 'Enter' && tooltipRef.hide();
			}}
			role="button"
			tabindex="0"
			class="tooltip"
		>
			<div slot="content" class="content">
				<span>{m['map.enable_geolocation']()}</span>
				<button class="button">{m['map.enable_geolocation_got_it']()}</button>
			</div>
			<ControlButton
				title={m['map.control_zoom_to_project']()}
				on:click={() => {
					entitiesStore.setToggleGeolocation(!entitiesStore.toggleGeolocation);
					if (!entitiesStore.toggleGeolocation) {
						entitiesStore.setUserLocationCoordinate(undefined);
						exitNavigationMode();
					}
				}}
			>
				<sl-icon name="geolocate" class={`geolocate-icon ${entitiesStore.toggleGeolocation ? 'toggle' : 'not-toggle'}`}
				></sl-icon>
			</ControlButton>
		</sl-tooltip>
	</ControlGroup>
</Control>

{#if entitiesStore.toggleGeolocation}
	<GeoJSON data={locationGeojson} id="geolocation">
		<SymbolLayer
			applyToClusters={false}
			hoverCursor="pointer"
			layout={{
				// if orientation true (meaning the browser supports device orientation sensor show location dot with orientation sign)
				'icon-image': !entityToNavigate
					? ['case', ['==', ['get', 'orientation'], true], 'locationArc', 'locationDot']
					: ['case', ['==', ['get', 'orientation'], true], 'arrow', 'locationDot'],
				'icon-allow-overlap': true,
				'text-offset': [0, -2],
				'text-size': 12,
				'icon-rotate': rotationDeg || 0, // rotate location icon acc to device orientation
				'icon-rotation-alignment': 'map',
				'icon-size': 0.5,
			}}
		/>
	</GeoJSON>
{/if}

{#if entitiesStore.toggleGeolocation && entityToNavigate}
	<div class="geolocation-exit">
		<div class="content">
			<p class="distance">{m['map.distance']()}: {entityDistance}m</p>
			<sl-button
				onclick={exitNavigationMode}
				onkeydown={(e: KeyboardEvent) => {
					e.key === 'Enter' && exitNavigationMode();
				}}
				role="button"
				tabindex="0"
				size="small"
				disabled={entitiesStore.syncEntityStatusManuallyLoading}
			>
				<span>{m['map.exit_navigation']()}</span>
			</sl-button>
		</div>
	</div>
{/if}
