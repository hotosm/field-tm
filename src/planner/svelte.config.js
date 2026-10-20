import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";

// wa-* elements are interactive web components; Svelte's a11y checks only know native tags.
const WA_FALSE_POSITIVES = new Set([
  "a11y_click_events_have_key_events",
  "a11y_no_static_element_interactions",
]);

export default {
  preprocess: vitePreprocess(),
  compilerOptions: {
    runes: true,
    warningFilter: (w) => !(WA_FALSE_POSITIVES.has(w.code) && /`<wa-/.test(w.message)),
  },
};
