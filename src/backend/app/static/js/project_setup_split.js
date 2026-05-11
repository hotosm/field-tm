import { bindAdvancedToggle } from "./project_setup_shared.js";

export function initProjectSetupSplit({ i18nStrings }) {
  const splitAlgorithm = document.getElementById("split-algorithm");
  const paramBuildings = document.getElementById("param-buildings");
  const paramTasks = document.getElementById("param-tasks");
  const paramDimension = document.getElementById("param-dimension");
  const noOfBuildingsInput = document.getElementById("no-of-buildings");
  const noOfTasksInput = document.getElementById("no-of-tasks");
  const dimensionMetersInput = document.getElementById("dimension-meters");
  const splitAdvancedConfigToggle = document.getElementById("split-advanced-config-toggle");
  const splitAdvancedConfigPanel = document.getElementById("split-advanced-config-panel");
  const splitIncludeRoadsCheckbox = document.getElementById("split-include-roads-checkbox");
  const splitIncludeRiversCheckbox = document.getElementById("split-include-rivers-checkbox");
  const splitIncludeRailwaysCheckbox = document.getElementById("split-include-railways-checkbox");
  const splitIncludeAerowaysCheckbox = document.getElementById("split-include-aeroways-checkbox");
  const splitIncludeRoadsValue = document.getElementById("split-include-roads-value");
  const splitIncludeRiversValue = document.getElementById("split-include-rivers-value");
  const splitIncludeRailwaysValue = document.getElementById("split-include-railways-value");
  const splitIncludeAerowaysValue = document.getElementById("split-include-aeroways-value");

  bindAdvancedToggle(splitAdvancedConfigToggle, splitAdvancedConfigPanel);

  function syncSplitLinearFeatureOptions() {
    if (splitIncludeRoadsValue && splitIncludeRoadsCheckbox) {
      splitIncludeRoadsValue.value = splitIncludeRoadsCheckbox.checked ? "true" : "false";
    }
    if (splitIncludeRiversValue && splitIncludeRiversCheckbox) {
      splitIncludeRiversValue.value = splitIncludeRiversCheckbox.checked ? "true" : "false";
    }
    if (splitIncludeRailwaysValue && splitIncludeRailwaysCheckbox) {
      splitIncludeRailwaysValue.value = splitIncludeRailwaysCheckbox.checked ? "true" : "false";
    }
    if (splitIncludeAerowaysValue && splitIncludeAerowaysCheckbox) {
      splitIncludeAerowaysValue.value = splitIncludeAerowaysCheckbox.checked ? "true" : "false";
    }
  }

  [
    splitIncludeRoadsCheckbox,
    splitIncludeRiversCheckbox,
    splitIncludeRailwaysCheckbox,
    splitIncludeAerowaysCheckbox,
  ]
    .filter(Boolean)
    .forEach((checkbox) => {
      checkbox.addEventListener("change", syncSplitLinearFeatureOptions);
    });
  syncSplitLinearFeatureOptions();

  const splitParamGroups = {
    buildings: { container: paramBuildings, input: noOfBuildingsInput },
    tasks: { container: paramTasks, input: noOfTasksInput },
    dimension: { container: paramDimension, input: dimensionMetersInput },
  };
  const algorithmActiveParam = {
    DIVIDE_BY_SQUARE: "dimension",
    AVG_BUILDING_VORONOI: "buildings",
    AVG_BUILDING_SKELETON: "buildings",
    TOTAL_TASKS: "tasks",
  };

  function updateSplitParamVisibility() {
    if (!splitAlgorithm) return;
    const active = algorithmActiveParam[splitAlgorithm.value] || null;
    for (const [key, { container, input }] of Object.entries(splitParamGroups)) {
      const isActive = key === active;
      if (container) container.style.display = isActive ? "block" : "none";
      if (input) {
        input.disabled = !isActive;
        if (isActive) input.setAttribute("required", "required");
        else input.removeAttribute("required");
      }
    }
  }

  updateSplitParamVisibility();

  const splitAoiForm = document.getElementById("split-aoi-form");
  if (!splitAoiForm) return;

  function updateAlgorithmUI() {
    const algorithm = splitAlgorithm?.value;
    const paramContainer = document.getElementById("algorithm-param-container");
    const splitBtn = splitAoiForm.querySelector('button[type="submit"]');
    const splitBtnText = document.getElementById("split-btn-text");

    if (paramContainer) {
      paramContainer.style.display = algorithm && algorithm !== "NO_SPLITTING" ? "block" : "none";
    }

    if (splitBtnText) {
      const btnLabels = {
        NO_SPLITTING: i18nStrings.confirmNoSplitting,
        DIVIDE_BY_SQUARE: i18nStrings.splitBySquare,
        AVG_BUILDING_VORONOI: i18nStrings.splitByBuildings,
        AVG_BUILDING_SKELETON: i18nStrings.splitByBuildings,
        TOTAL_TASKS: i18nStrings.splitAoi,
      };
      splitBtnText.textContent =
        btnLabels[algorithm] || (algorithm ? i18nStrings.splitAoi : i18nStrings.selectOption);
    }

    if (splitBtn) {
      splitBtn.disabled = !algorithm || algorithm === "";
    }

    updateSplitParamVisibility();
  }

  if (splitAlgorithm) {
    splitAlgorithm.addEventListener("change", updateAlgorithmUI);
    updateAlgorithmUI();
  }

  splitAoiForm.addEventListener("submit", function (e) {
    syncSplitLinearFeatureOptions();
    const algorithm = splitAlgorithm?.value;
    if (!algorithm || algorithm === "") {
      e.preventDefault();
      return false;
    }
  });

  splitAoiForm.addEventListener("htmx:beforeRequest", function () {
    const splitLoading = document.getElementById("split-loading");
    const splitBtnText = document.getElementById("split-btn-text");
    const splitBtnSpinner = document.getElementById("split-btn-spinner");
    if (splitLoading) splitLoading.style.display = "block";
    const algorithm = splitAlgorithm?.value;
    if (splitBtnText) {
      if (algorithm === "NO_SPLITTING") {
        splitBtnText.textContent = i18nStrings.confirming;
      } else {
        splitBtnText.textContent = i18nStrings.splitting;
      }
    }
    if (splitBtnSpinner) splitBtnSpinner.style.display = "inline-block";
  });

  splitAoiForm.addEventListener("htmx:afterRequest", function () {
    const splitLoading = document.getElementById("split-loading");
    const splitBtnSpinner = document.getElementById("split-btn-spinner");
    if (splitLoading) splitLoading.style.display = "none";
    if (splitBtnSpinner) splitBtnSpinner.style.display = "none";
    updateAlgorithmUI();
  });
}
