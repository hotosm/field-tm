import { mount } from "svelte";
import { setWorkerUrl } from "maplibre-gl";
import maplibreWorker from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import App from "./App.svelte";
import "./app.css";

// MapLibre 6 locates its worker relative to its own module, which bundling breaks.
setWorkerUrl(maplibreWorker);

mount(App, { target: document.getElementById("app")! });
