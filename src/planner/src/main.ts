import { mount } from "svelte";
import { setWorkerUrl } from "maplibre-gl";
import maplibreWorker from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import "@hotosm/ui/dist/style.css";
// Register every wa-* element and the hot-* ones we use before mounting.
import "@hotosm/ui/dist/webawesome-all.js";
import "@hotosm/ui/dist/components/header/header.js";
import "@hotosm/ui/dist/components/tool-menu/tool-menu.js";
import App from "./App.svelte";
import "./app.css";

// MapLibre 6 locates its worker relative to its own module, which bundling breaks.
setWorkerUrl(maplibreWorker);

mount(App, { target: document.getElementById("app")! });
