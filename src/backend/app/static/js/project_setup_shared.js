export const OSM_FORM_TITLE_TO_PRESET = {
  "OSM Buildings": { category: "buildings", geomType: "POLYGON", centroid: false },
  "OSM Highways": { category: "highways", geomType: "POLYLINE", centroid: false },
  "OSM Healthcare": { category: "health", geomType: "POINT", centroid: false },
  "OSM Toilets": { category: "toilets", geomType: "POINT", centroid: false },
  "OSM Religious": { category: "religious", geomType: "POINT", centroid: false },
  "OSM Landuse": { category: "landusage", geomType: "POLYGON", centroid: false },
  "OSM Waterways": { category: "waterways", geomType: "POLYLINE", centroid: false },
  "OSM Water Points": { category: "waterpoints", geomType: "POINT", centroid: false },
  "OSM Waste Disposal": { category: "wastedisposal", geomType: "POINT", centroid: false },
  "OSM Education": { category: "education", geomType: "POINT", centroid: false },
  "OSM Cemeteries": { category: "cemeteries", geomType: "POLYGON", centroid: false },
  "OSM Amenities": { category: "amenities", geomType: "POINT", centroid: false },
};

export function defaultDownloadPreset() {
  return { category: "buildings", geomType: "POLYGON", centroid: false };
}

export function presetForFormTitle(formTitle) {
  return OSM_FORM_TITLE_TO_PRESET[formTitle] || defaultDownloadPreset();
}

export function parseSetupPreference(setupPreferenceKey) {
  try {
    const raw = window.localStorage.getItem(setupPreferenceKey);
    return raw ? JSON.parse(raw) : null;
  } catch (_) {
    return null;
  }
}

export function saveSetupPreference(setupPreferenceKey, preference) {
  try {
    window.localStorage.setItem(setupPreferenceKey, JSON.stringify(preference));
  } catch (_) {
    // Ignore storage failures to keep setup flow resilient.
  }
}

export function bindAdvancedToggle(toggleElement, panelElement) {
  if (!toggleElement || !panelElement) return;
  toggleElement.addEventListener("click", function () {
    panelElement.classList.toggle("ftm-advanced-config--hidden");
  });
}

export function clearContainer(container) {
  if (!container) return;
  container.textContent = "";
}

export function renderCallout(container, variant, message) {
  if (!container) return;
  clearContainer(container);
  if (!message) return;

  const callout = document.createElement("wa-callout");
  callout.setAttribute("variant", variant);
  const span = document.createElement("span");
  span.textContent = String(message);
  callout.appendChild(span);
  container.appendChild(callout);
}
