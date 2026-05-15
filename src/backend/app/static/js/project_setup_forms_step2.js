import {
  bindAdvancedToggle,
  defaultDownloadPreset,
  parseSetupPreference,
  renderCallout,
} from "./project_setup_shared.js";

export function initProjectSetupDataExtract({
  i18nStrings,
  projectId,
  hasXlsform,
  setupPreferenceKey,
  mapCategoryToTitle,
  persistDownloadPreference,
}) {
  const downloadOsmDataBtn = document.getElementById("download-osm-data-btn");
  const collectNewDataBtn = document.getElementById("collect-new-data-btn");
  const uploadGeojsonBtn = document.getElementById("upload-geojson-btn");
  const geojsonFileInput = document.getElementById("geojson-file-input");
  const osmDataStatus = document.getElementById("osm-data-status");
  const downloadLoading = document.getElementById("download-loading");
  const downloadBtnText = document.getElementById("download-btn-text");
  const downloadSpinner = document.getElementById("download-spinner");
  const dataAdvancedConfigToggle = document.getElementById("data-advanced-config-toggle");
  const dataAdvancedConfigPanel = document.getElementById("data-advanced-config-panel");
  const recommendedDataNoteText = document.getElementById("recommended-data-note-text");
  const osmCategorySelect = document.getElementById("osm-category-select");
  const osmGeomTypeSelect = document.getElementById("osm-geom-type-select");
  const osmCentroidCheckbox = document.getElementById("osm-centroid-checkbox");
  const uploadGeojsonForm = document.getElementById("upload-geojson-form");

  bindAdvancedToggle(dataAdvancedConfigToggle, dataAdvancedConfigPanel);

  function formatGeomType(geomType) {
    if (geomType === "POLYGON") return i18nStrings.polygons;
    if (geomType === "POLYLINE") return i18nStrings.polylines;
    if (geomType === "POINT") return i18nStrings.points;
    return i18nStrings.features;
  }

  function buildDownloadUrl(config) {
    const params = new URLSearchParams({
      project_id: String(projectId),
      osm_category: config.category || "buildings",
      geom_type: config.geomType || "POLYGON",
    });
    if (config.centroid) params.set("centroid", "true");
    return `/download-osm-data-htmx?${params.toString()}`;
  }

  function readStep2DownloadConfig() {
    return {
      category: osmCategorySelect?.value || "buildings",
      geomType: osmGeomTypeSelect?.value || "POLYGON",
      centroid: Boolean(osmCentroidCheckbox?.checked),
    };
  }

  function applyStep2DownloadConfig(config, sourceMode = "template") {
    if (osmCategorySelect) osmCategorySelect.value = config.category || "buildings";
    if (osmGeomTypeSelect) osmGeomTypeSelect.value = config.geomType || "POLYGON";
    if (osmCentroidCheckbox) osmCentroidCheckbox.checked = Boolean(config.centroid);

    if (downloadOsmDataBtn) {
      downloadOsmDataBtn.setAttribute("hx-post", buildDownloadUrl(config));
    }

    if (!recommendedDataNoteText) return;

    const title = mapCategoryToTitle(config.category);
    const geomLabel = formatGeomType(config.geomType);
    if (sourceMode === "custom") {
      recommendedDataNoteText.textContent = i18nStrings.customFormDownloadNote;
    } else if (title) {
      recommendedDataNoteText.textContent = i18nStrings.recommendedSourceFormat
        .replace("%(title)s", title)
        .replace("%(geom_label)s", geomLabel);
    } else {
      recommendedDataNoteText.textContent = i18nStrings.recommendedSourceUpdatedFormat.replace(
        "%(geom_label)s",
        geomLabel,
      );
    }
  }

  if (!hasXlsform && downloadOsmDataBtn) downloadOsmDataBtn.disabled = true;
  if (!hasXlsform && collectNewDataBtn) collectNewDataBtn.disabled = true;
  if (!hasXlsform && uploadGeojsonBtn) uploadGeojsonBtn.disabled = true;

  if (downloadOsmDataBtn) {
    const preference = parseSetupPreference(setupPreferenceKey);
    const defaults =
      preference && preference.category && preference.geomType
        ? {
            category: preference.category,
            geomType: preference.geomType,
            centroid: Boolean(preference.centroid),
            sourceMode: preference.mode || "template",
          }
        : { ...defaultDownloadPreset(), sourceMode: "template" };
    applyStep2DownloadConfig(defaults, defaults.sourceMode);

    downloadOsmDataBtn.addEventListener("htmx:beforeRequest", function () {
      if (downloadLoading) downloadLoading.style.display = "block";
      if (downloadBtnText) downloadBtnText.textContent = i18nStrings.downloading;
      if (downloadSpinner) downloadSpinner.style.display = "inline-block";
      downloadOsmDataBtn.disabled = true;
    });

    downloadOsmDataBtn.addEventListener("htmx:afterRequest", function () {
      if (downloadLoading) downloadLoading.style.display = "none";
      if (downloadBtnText) downloadBtnText.textContent = i18nStrings.downloadOsmData;
      if (downloadSpinner) downloadSpinner.style.display = "none";
      downloadOsmDataBtn.disabled = false;
    });
  }

  if (osmCategorySelect || osmGeomTypeSelect || osmCentroidCheckbox) {
    const onAdvancedDownloadConfigChange = function () {
      const config = readStep2DownloadConfig();
      const preference = parseSetupPreference(setupPreferenceKey) || {};
      applyStep2DownloadConfig(config, preference.mode || "template");

      if (
        preference.category === config.category &&
        preference.geomType === config.geomType &&
        Boolean(preference.centroid) === Boolean(config.centroid)
      ) {
        return;
      }

      persistDownloadPreference(config);
    };

    if (osmCategorySelect) {
      osmCategorySelect.addEventListener("change", onAdvancedDownloadConfigChange);
    }
    if (osmGeomTypeSelect) {
      osmGeomTypeSelect.addEventListener("change", onAdvancedDownloadConfigChange);
    }
    if (osmCentroidCheckbox) {
      osmCentroidCheckbox.addEventListener("change", onAdvancedDownloadConfigChange);
    }
  }

  if (uploadGeojsonBtn) {
    uploadGeojsonBtn.addEventListener("click", () => {
      if (geojsonFileInput) geojsonFileInput.click();
    });
  }

  if (geojsonFileInput && uploadGeojsonForm) {
    geojsonFileInput.addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (!file) return;

      const validExtensions = [".geojson", ".json"];
      const fileExtension = "." + file.name.split(".").pop().toLowerCase();
      if (!validExtensions.includes(fileExtension)) {
        renderCallout(osmDataStatus, "danger", i18nStrings.invalidGeojsonFileType);
        geojsonFileInput.value = "";
        return;
      }

      if (uploadGeojsonForm.requestSubmit) {
        uploadGeojsonForm.requestSubmit();
      } else {
        const submitEvent = new Event("submit", { bubbles: true, cancelable: true });
        uploadGeojsonForm.dispatchEvent(submitEvent);
      }
    });
  }
}
