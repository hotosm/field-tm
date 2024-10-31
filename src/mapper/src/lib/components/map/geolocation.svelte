<script lang="ts">
    import { GeoJSON, SymbolLayer } from 'svelte-maplibre';
    import type { FeatureCollection } from 'geojson';

    import { GetDeviceRotation } from '$lib/utils/getDeviceRotation';
	import { getAlertStore } from '$store/common.svelte.ts';

	const alertStore = getAlertStore();

	interface Props {
		map: maplibregl.Map | undefined;
		toggleGeolocationStatus?: boolean;
	}

	let {
		map=$bindable(),
		toggleGeolocationStatus = $bindable(false),
	}: Props = $props();

	let coords: [number, number] | undefined = $state();
	let rotationDeg: number | undefined = $state();
	let watchId: number | undefined = $state();

	$effect(() => {
		if (map && toggleGeolocationStatus) {
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
					coords = [pos.coords.longitude, pos.coords.latitude];
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
					coordinates: coords,
				},
				// firefox & safari doesn't support device orientation sensor, so if the browser any of the two set orientation to false
				properties: { orientation: !(isFirefox || isSafari) },
			},
		],
	});
	

	$effect(() => {
		if (map && toggleGeolocationStatus) {
			if (isFirefox || isSafari) {
				// firefox & safari doesn't support device orientation sensor
				alertStore.setAlert({
					variant: 'warning',
					message: "Unable to handle device orientation. Your browser doesn't support device orientation sensors.",
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
				});

				Promise.all([
					navigator.permissions.query({ name: 'accelerometer' }),
					navigator.permissions.query({ name: 'magnetometer' }),
					navigator.permissions.query({ name: 'gyroscope' }),
				]).then((results) => {
					if (results.every((result) => result.state === 'granted')) {
						sensor.start();
					} else {
					}
				});
			}
		}
	});
</script>

<GeoJSON data={locationGeojson} id="point">
    <SymbolLayer
        applyToClusters={false}
        hoverCursor="pointer"
        layout={{
            // if orientation true (meaning the browser supports device orientation sensor show location dot with orientation sign)
            'icon-image': ['case', ['==', ['get', 'orientation'], true], 'locationArc', 'locationDot'],
            'icon-allow-overlap': true,
            'text-field': '{mag}',
            'text-offset': [0, -2],
            'text-size': 12,
            'icon-rotate': rotationDeg || 0, // rotate location icon acc to device orientation
            'icon-rotation-alignment': 'map',
            'icon-size': 0.5,
        }}
    />
</GeoJSON>
